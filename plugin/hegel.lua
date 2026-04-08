-- hegel.nvim — Search G.W.F. Hegel's source texts in Neovim
-- Maintainer: Christian Gleitze

if vim.g.loaded_hegel then
  return
end
vim.g.loaded_hegel = true

vim.api.nvim_create_user_command("HegelSearch", function(opts)
  require("hegel.search").search(opts.args ~= "" and opts.args or nil)
end, { nargs = "?" })

vim.api.nvim_create_user_command("HegelWerke", function()
  require("hegel.picker").werke()
end, {})

vim.api.nvim_create_user_command("HegelZufall", function()
  require("hegel.picker").zufall()
end, {})

vim.api.nvim_create_user_command("HegelParagraph", function(opts)
  require("hegel.paragraph").goto_paragraph(opts.args)
end, { nargs = 1 })
