local M = {}
local hegel = require("hegel")

local function set_readonly()
  if hegel.config.readonly then
    vim.bo.readonly = true
    vim.bo.modifiable = false
  end
end

function M._body_start(lines)
  if lines[1] and lines[1]:match("^%-%-%-%s*$") then
    for i = 2, #lines do
      if lines[i]:match("^%-%-%-%s*$") then
        return i + 1
      end
    end
  end
  return 1
end

function M._collect_results(query, texts_dir)
  local needle = vim.fn.tolower(vim.trim(query or ""))
  local files = vim.fn.globpath(texts_dir, "**/*.txt", false, true)
  table.sort(files)

  local results = {}
  for _, file in ipairs(files) do
    local ok, lines = pcall(vim.fn.readfile, file)
    if ok then
      local rel = file
      if file:sub(1, #texts_dir + 1) == texts_dir .. "/" then
        rel = file:sub(#texts_dir + 2)
      end

      for lnum = M._body_start(lines), #lines do
        local line = lines[lnum]
        local col = needle == "" and 1 or vim.fn.tolower(line):find(needle, 1, true)
        if line:match("%S") and (needle == "" or col) then
          table.insert(results, string.format("%s:%d:%d:%s", rel, lnum, col or 1, line))
        end
      end
    end
  end

  return results
end

function M._rg_cmd(query)
  local body_filter = [[
function body_start(file, line, n) {
  if (file in starts) return starts[file]
  starts[file] = 1
  n = 0
  while ((getline line < file) > 0) {
    n++
    if (n == 1 && line != "---") break
    if (n > 1 && line == "---") {
      starts[file] = n + 1
      break
    }
    if (n > 100) break
  }
  close(file)
  return starts[file]
}
($2 + 0) >= body_start($1) { print }
]]

  return table.concat({
    "rg",
    "--column --line-number --no-heading --color=never --smart-case",
    "--glob '*.txt'",
    "-e",
    vim.fn.shellescape(query or ""),
    "| awk -F: " .. vim.fn.shellescape(body_filter),
  }, " ")
end

function M._result_file_line(entry)
  local stripped = entry:gsub("\27%[[0-9;]*m", "")
  local file, lnum = stripped:match("^(.-):(%d+):%d+:")
  if not file then
    file, lnum = stripped:match("^(.-):(%d+):")
  end
  return file and file:gsub("^%./", ""), tonumber(lnum)
end

function M._open_result(entry, texts_dir)
  local file, lnum = M._result_file_line(entry)
  if not file then
    vim.notify("[hegel.nvim] Invalid search result: " .. entry, vim.log.levels.ERROR)
    return
  end

  local sep = texts_dir:sub(-1) == "/" and "" or "/"
  vim.cmd("edit " .. vim.fn.fnameescape(texts_dir .. sep .. file))
  vim.api.nvim_win_set_cursor(0, { tonumber(lnum), 0 })
  vim.cmd("normal! zz")
  set_readonly()
end

--- Full-text search across all Hegel texts, excluding metadata headers.
---@param query string|nil Search term (nil opens empty picker)
function M.search(query)
  local texts_dir = hegel.config.texts_dir
  local picker = hegel.config.picker

  if picker == "fzf-lua" then
    M._search_fzf(query, texts_dir)
  elseif picker == "telescope" then
    local results = M._collect_results(query, texts_dir)
    if #results == 0 then
      vim.notify("[hegel.nvim] No matches found.", vim.log.levels.WARN)
      return
    end
    M._search_telescope(results, texts_dir)
  else
    vim.notify("[hegel.nvim] Unknown picker: " .. picker, vim.log.levels.ERROR)
  end
end

function M._search_fzf(query, texts_dir)
  local ok, fzf = pcall(require, "fzf-lua")
  if not ok then
    vim.notify("[hegel.nvim] fzf-lua not installed.", vim.log.levels.ERROR)
    return
  end

  local action = require("fzf-lua.actions")
  local opts = {
    cwd = texts_dir,
    file_icons = false,
    git_icons = false,
    multiprocess = false,
    prompt = "Hegel> ",
    winopts = {
      title = " Hegel Source Texts ",
      title_pos = "center",
      preview = {
        title = " Preview ",
        title_pos = "center",
      },
    },
    actions = {
      ["default"] = function(selected, fzf_opts)
        action.file_edit(selected, fzf_opts)
        set_readonly()
      end,
    },
  }

  if vim.fn.executable("rg") == 1 then
    opts.raw_cmd = M._rg_cmd(query)
    opts.search = query or ""
    fzf.grep(opts)
    return
  end

  local results = M._collect_results(query, texts_dir)
  if #results == 0 then
    vim.notify("[hegel.nvim] No matches found.", vim.log.levels.WARN)
    return
  end

  opts._type = "file"
  opts.previewer = "builtin"
  fzf.fzf_exec(results, opts)
end

function M._search_telescope(results, texts_dir)
  local ok_pickers, pickers = pcall(require, "telescope.pickers")
  local ok_finders, finders = pcall(require, "telescope.finders")
  local ok_conf, conf = pcall(require, "telescope.config")
  local ok_actions, actions = pcall(require, "telescope.actions")
  local ok_state, action_state = pcall(require, "telescope.actions.state")
  if not (ok_pickers and ok_finders and ok_conf and ok_actions and ok_state) then
    vim.notify("[hegel.nvim] telescope.nvim not installed.", vim.log.levels.ERROR)
    return
  end

  pickers.new({}, {
    prompt_title = "Hegel Search",
    finder = finders.new_table({ results = results }),
    sorter = conf.values.generic_sorter({}),
    attach_mappings = function(prompt_bufnr)
      actions.select_default:replace(function()
        local selected = action_state.get_selected_entry()
        actions.close(prompt_bufnr)
        if selected then
          M._open_result(selected[1] or selected.value, texts_dir)
        end
      end)
      return true
    end,
  }):find()
end

return M
