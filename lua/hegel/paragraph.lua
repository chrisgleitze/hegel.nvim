local M = {}
local hegel = require("hegel")

--- Jump to a specific paragraph (§) in a work
--- Searches for files whose metadata contains the given paragraph number
---@param nr string|number Paragraph number (e.g. "142" or 142)
function M.goto_paragraph(nr)
  nr = tostring(nr):match("^%s*(.-)%s*$") -- trim
  if nr == "" then
    vim.notify("[hegel.nvim] Please specify a paragraph number.", vim.log.levels.WARN)
    return
  end

  local texts_dir = hegel.config.texts_dir
  local files = vim.fn.globpath(texts_dir, "**/*.txt", false, true)

  -- Search for file containing this paragraph
  local pattern = "Paragraph: %§ " .. nr .. "$"
  local pattern_padded = "par%-" .. string.format("%03d", tonumber(nr) or 0) .. ".txt"

  for _, file in ipairs(files) do
    -- Match by filename convention (NNN-par-NNN.txt)
    if file:match(pattern_padded) then
      vim.cmd("edit " .. vim.fn.fnameescape(file))
      -- Jump past metadata header
      local lines = vim.fn.readfile(file)
      local start = 1
      if lines[1] and lines[1]:match("^%-%-%-") then
        for i = 2, #lines do
          if lines[i]:match("^%-%-%-") then
            start = i + 1
            break
          end
        end
      end
      vim.api.nvim_win_set_cursor(0, { start, 0 })
      vim.cmd("normal! zz")

      if hegel.config.readonly then
        vim.bo.readonly = true
        vim.bo.modifiable = false
      end
      return
    end
  end

  vim.notify("[hegel.nvim] Paragraph § " .. nr .. " not found.", vim.log.levels.WARN)
end

return M
