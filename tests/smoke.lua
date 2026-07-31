local hegel = require("hegel")
local paragraph = require("hegel.paragraph")
local search = require("hegel.search")

local function check(condition, message)
  assert(condition, message)
end

check(search._body_start({"---", "Werk: Test", "---", "Text"}) == 4, "header end")
check(search._body_start({"Text"}) == 1, "body without header")
check(search._rg_cmd("A+B"):find("--fixed-strings", 1, true), "literal ripgrep search")

local old_notify, old_picker, notification = vim.notify, hegel.config.picker, nil
vim.notify = function(message)
  notification = message
end
hegel.setup({ picker = "unknown" })
vim.notify = old_notify
hegel.config.picker = old_picker
check(notification and notification:find("Invalid picker", 1, true), "invalid picker")

local dir = vim.fn.tempname()
vim.fn.mkdir(dir, "p")
local search_file = dir .. "/seite-001.txt"
vim.fn.writefile({
  "---",
  "Werk: Test",
  "---",
  "",
  "A+B",
  "AAAB",
}, search_file)

local results = search._collect_results("A+B", dir)
check(#results == 1, "literal search")
check(results[1] == "seite-001.txt:5:1:A+B", "search result location")

local result_file, result_line = search._result_file_line("./seite-001.txt:5:1:A+B")
check(result_file == "seite-001.txt" and result_line == 5, "result parsing")

local old_readonly = hegel.config.readonly
hegel.config.readonly = false
search._open_result(results[1], dir)
check(vim.api.nvim_buf_get_name(0) == search_file, "open result file")
check(vim.api.nvim_win_get_cursor(0)[1] == 5, "open result line")

local paragraph_file = dir .. "/001-par-001.txt"
vim.fn.writefile({
  "---",
  "Werk: Test",
  "Paragraph: § 1",
  "---",
  "",
  "§ 1",
  "Text",
}, paragraph_file)

local old_dir = hegel.config.texts_dir
hegel.config.texts_dir = dir
paragraph.goto_paragraph("1")
check(vim.api.nvim_buf_get_name(0) == paragraph_file, "paragraph file")
hegel.config.texts_dir, hegel.config.readonly = old_dir, old_readonly

vim.cmd("enew")
vim.fn.delete(dir, "rf")
print("hegel.nvim smoke: OK")
