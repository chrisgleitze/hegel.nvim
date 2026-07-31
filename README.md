# hegel.nvim

Search and browse the works of G.W.F. Hegel in German directly from Neovim.

The plugin combines Neovim's search workflow with a local corpus of Hegel's writings for full-text search, work browsing, paragraph navigation, and serendipitous discovery.

> [!NOTE]
> This is a very early-stage plugin!\
> The text is being expanded step by step toward a complete edition.

## Why?

This plugin is useful for people writing about Hegel in Neovim. A local corpus of Hegel's works is a natural fit for the Neovim workflow — it is likely the quickest way to find a passage, a term, or a specific paragraph in his writings.

Hegel is notoriously difficult to understand and requires constant re-reading. You often need to revisit what he actually wrote to check a definition or verify whether an interpretation holds up against the original text.

## Features

- **Full-text search** across all of Hegel's works via `:HegelSearch`
- **Browse by work** with `:HegelWerke`
- **Random passage** for inspiration with `:HegelZufall`
- Search ignores metadata headers and searches only the text body
- **Jump to paragraph** with `:HegelParagraph` — navigate directly to any § in the Rechtsphilosophie
- Texts include **TWA** (Theorie Werkausgabe) and **GW** (Gesammelte Werke) metadata; detailed page numbers are still incomplete
- Opens texts in **read-only** mode by default
- Search works with **fzf-lua** (default) or **telescope.nvim**

## Zitierweise (Citation System)

The project follows standard academic Hegel citation conventions where the corpus already supports them. For the _Grundlinien der Philosophie des Rechts_, the primary identifier is the paragraph number (§). TWA and GW metadata are present, but detailed page numbers still need to be added.

Paragraph files currently contain Hegel's published paragraph text and, where present, Hegel's own Anmerkung. Zusätze compiled by Eduard Gans are planned, but not bundled yet.

Standard citation format: `Hegel, GPR § 142 Anm.`

### Abbreviations

| Abbreviation | Meaning                                |
| ------------ | -------------------------------------- |
| **GPR**      | Grundlinien der Philosophie des Rechts |
| **Anm.**     | Anmerkung (Remark)                     |
| **Zus.**     | Zusatz (Addition)                      |
| **TWA**      | Theorie Werkausgabe (Suhrkamp)         |
| **GW**       | Gesammelte Werke (Meiner)              |

## Requirements

- Neovim >= 0.8
- One search picker for `:HegelSearch`: [fzf-lua](https://github.com/ibhagwan/fzf-lua),
  [telescope.nvim](https://github.com/nvim-telescope/telescope.nvim), or
  [fff.nvim](https://github.com/dmtrKovalenko/fff)
- FFF requires its own binary installation; follow the upstream installation
  instructions when using `picker = "fff"`.
- Optional: [ripgrep](https://github.com/BurntSushi/ripgrep) for faster `fzf-lua` search

## Installation

### [lazy.nvim](https://github.com/folke/lazy.nvim)

To use the default config:

```lua
{
  "chrisgleitze/hegel.nvim",
  config = true,
}
```

If you'd like to edit the default configuration:

```lua
{
  "chrisgleitze/hegel.nvim",
  config = function()
    require("hegel").setup({
      -- your own config
    })
  end,
}
```

### [vim.pack](https://echasnovski.com/blog/2026-03-13-a-guide-to-vim-pack)

Since Neovim 0.12, this is the built-in plugin manager.

```lua
vim.pack.add({
  "https://github.com/chrisgleitze/hegel.nvim",
})
require("hegel").setup()
```

### [packer.nvim](https://github.com/wbthomason/packer.nvim)

```lua
use {
  "chrisgleitze/hegel.nvim",
  config = function()
    require("hegel").setup()
  end,
}
```

## Configuration

```lua
require("hegel").setup({
  -- Preferred external text directory.
  -- Falls back to the bundled texts/ directory if this path does not exist.
  texts_dir = vim.fn.stdpath("data") .. "/hegel-texte",

  -- Search picker: "fzf-lua", "telescope", or "fff"
  picker = "fzf-lua",

  -- Open texts in read-only mode
  readonly = true,

  -- Key mappings (set to false to disable)
  keymaps = {
    search    = "<leader>hs",   -- Open search prompt
    werke     = "<leader>hw",   -- Browse works
    zufall    = "<leader>hz",   -- Random passage
    paragraph = "<leader>hp",   -- Jump to paragraph
  },
})
```

With `picker = "fff"`, FFF performs the content search and Neovim's native
selection UI displays the filtered results.

## Commands

| Command                | Description                                       |
| ---------------------- | ------------------------------------------------- |
| `:HegelSearch [query]` | Full-text search across all works                 |
| `:HegelWerke`          | Pick a work, then search within it                |
| `:HegelZufall`         | Jump to a random passage                          |
| `:HegelParagraph [nr]` | Jump to a specific § (e.g. `:HegelParagraph 142`) |

## Default Keymaps

| Keymap       | Action            |
| ------------ | ----------------- |
| `<leader>hs` | `:HegelSearch`    |
| `<leader>hw` | `:HegelWerke`     |
| `<leader>hz` | `:HegelZufall`    |
| `<leader>hp` | `:HegelParagraph` |

## Text Corpus

The plugin ships with plaintext files from Hegel's works. Each file includes a YAML-style metadata header with the work title, section name, TWA and GW metadata, and year of first publication. Paragraph files for the _Grundlinien der Philosophie des Rechts_ also include a `Paragraph` field.

### Currently included

- **Die Verfassung Deutschlands** (verfasst 1798-1802, erste Druckausgabe 1893)
- **Differenz des Fichteschen und Schellingschen Systems der Philosophie** (1801)
- **Über das Wesen der philosophischen Kritik überhaupt** (1802)
- **Glauben und Wissen** (1802)
- **Grundlinien der Philosophie des Rechts** (1821)
- **Wer denkt abstrakt?** (ca. 1807, first published 1835)

### Adding texts

Place additional `.txt` files in a subdirectory under `texts/`. Each
subdirectory represents one work. Files should follow this format:

```
---
Werk: Title of the Work
Paragraph: § 142
Abschnitt: Section Name
TWA: Bd. 7
GW: Bd. 14,1
Erstausgabe: 1821
---

§ 142

[Paragraph text]

Anmerkung

[Remark text]

Zusatz

[Addition text, if available]
```

## Project Structure

```
hegel.nvim/
├── lua/
│   └── hegel/
│       ├── init.lua        # Plugin setup and configuration
│       ├── search.lua      # Full-text search (fzf-lua / telescope)
│       ├── picker.lua      # Work browser and random passage
│       └── paragraph.lua   # Paragraph (§) navigation
├── plugin/
│   └── hegel.lua           # Neovim command definitions
├── texts/
│   ├── 1798-1802-die-verfassung-deutschlands/
│   ├── 1801-differenz-des-fichteschen-und-schellingschen-systems-der-philosophie/
│   ├── 1802-glauben-und-wissen/
│   ├── 1802-ueber-das-wesen-der-philosophischen-kritik/
│   ├── 1807-wer-denkt-abstrakt/
│   └── 1821-grundlinien-der-philosophie-des-rechts/
├── scripts/
│   ├── build_minor_works.py
│   ├── check_corpus.py
│   ├── extract_vorrede.py
│   └── parse_ocr.py
└── README.md
```

## Roadmap

- [ ] Review and correct remaining OCR artifacts in the text
- [ ] Include Zusätze (Gans 1833 edition) as separate textual layer
- [ ] Add TWA and GW page numbers to metadata
- [ ] Add more works (Phänomenologie des Geistes, Wissenschaft der Logik, Enzyklopädie)
- [ ] `:HegelStelle` — look up passages by TWA or GW page number
- [ ] Citation export to clipboard (`Hegel, GPR § 142 Anm.`)

## License

The plugin code is released under the MIT License.

Hegel's texts are in the public domain.
