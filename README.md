# hegel.nvim

Search and browse the works of G.W.F. Hegel in German directly from Neovim.

The plugin combines Neovim's powerful search capabilities with a local corpus of Hegel's writings and integrates with fuzzy finders for full-text search, work browsing, paragraph navigation, and serendipitous discovery.

> [!NOTE]
> This is a very early-stage plugin!\
> The corpus currently contains selected paragraphs from the Rechtsphilosophie.\
> The text is being expanded step by step toward a complete edition.\

## Why?

This plugin is useful for people writing about Hegel in Neovim. A local corpus of Hegel's works is a natural fit for the Neovim workflow — it is likely the quickest way to find a passage, a term, or a specific paragraph in his writings.

Hegel is notoriously difficult to understand and requires constant re-reading. You often need to revisit what he actually wrote to check a definition or verify whether an interpretation holds up against the original text.

## Features

- **Full-text search** across all of Hegel's works via `:HegelSearch`
- **Browse by work** with `:HegelWerke`
- **Random passage** for inspiration with `:HegelZufall`
- **Jump to paragraph** with `:HegelParagraph` — navigate directly to any § in the Rechtsphilosophie
- Texts annotated with **TWA** (Theorie Werkausgabe) and **GW** (Gesammelte Werke) references
- Opens texts in **read-only** mode by default
- Works with **fzf-lua** (default) or **telescope.nvim**

## Zitierweise (Citation System)

The plugin follows standard academic Hegel citation conventions:

- **Primary identifier**: § (paragraph number) — edition-independent, universally recognized
- **TWA**: Theorie Werkausgabe (Suhrkamp), ed. Moldenhauer/Michel — the most widely used edition
- **GW**: Gesammelte Werke (Meiner), the historisch-kritische Ausgabe — the scholarly standard

Each paragraph file contains up to three textual layers:

| Layer | Abbreviation | Source |
|---|---|---|
| **Paragraph** (§) | — | Hegel's own published text (1821) |
| **Anmerkung** | Anm. | Hegel's own remark, part of the 1821 edition |
| **Zusatz** | Zus. | Compiled by Eduard Gans (1833) from student lecture notes |

Standard citation format: `Hegel, GPR § 142 Anm.`

### Abbreviations

| Abbreviation | Meaning |
|---|---|
| **GPR** | Grundlinien der Philosophie des Rechts |
| **Anm.** | Anmerkung (Remark) |
| **Zus.** | Zusatz (Addition) |
| **TWA** | Theorie Werkausgabe (Suhrkamp) |
| **GW** | Gesammelte Werke (Meiner) |

## Requirements

- Neovim >= 0.8
- [fzf-lua](https://github.com/ibhagwan/fzf-lua) or
  [telescope.nvim](https://github.com/nvim-telescope/telescope.nvim)
- [ripgrep](https://github.com/BurntSushi/ripgrep) (used by both pickers)

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
  -- Directory containing the text corpus.
  -- Defaults to the texts/ directory bundled with the plugin.
  texts_dir = vim.fn.stdpath("data") .. "/hegel-texte",

  -- Picker backend: "fzf-lua" or "telescope"
  picker = "fzf-lua",

  -- Open texts in read-only mode
  readonly = true,

  -- Show edition references (TWA, GW)
  show_references = true,

  -- Key mappings (set to false to disable)
  keymaps = {
    search    = "<leader>hs",   -- Open search prompt
    werke     = "<leader>hw",   -- Browse works
    zufall    = "<leader>hz",   -- Random passage
    paragraph = "<leader>hp",   -- Jump to paragraph
  },
})
```

## Commands

| Command                  | Description                              |
| ------------------------ | ---------------------------------------- |
| `:HegelSearch [query]`   | Full-text search across all works        |
| `:HegelWerke`            | Pick a work, then search within it       |
| `:HegelZufall`           | Jump to a random passage                 |
| `:HegelParagraph [nr]`   | Jump to a specific § (e.g. `:HegelParagraph 142`) |

## Default Keymaps

| Keymap       | Action             |
| ------------ | ------------------ |
| `<leader>hs` | `:HegelSearch`     |
| `<leader>hw` | `:HegelWerke`      |
| `<leader>hz` | `:HegelZufall`     |
| `<leader>hp` | `:HegelParagraph`  |

## Text Corpus

The plugin ships with plaintext files from Hegel's works. Each file includes a YAML-style metadata header with the work title, paragraph number, section name, TWA and GW references, and year of first publication.

### Currently included

- **Grundlinien der Philosophie des Rechts** (1821) — selected paragraphs (§§ 1-4, 34, 36, 105, 142, 158, 182, 257-258 + Vorrede)

### Text structure

The Rechtsphilosophie (§§ 1-360) is organized as follows:

- **Vorrede** (Preface)
- **Einleitung** (Introduction): §§ 1-33
- **Erster Theil — Das abstracte Recht** (Abstract Right): §§ 34-104
- **Zweiter Theil — Die Moralität** (Morality): §§ 105-141
- **Dritter Theil — Die Sittlichkeit** (Ethical Life): §§ 142-360
  - Die Familie (Family): §§ 158-181
  - Die bürgerliche Gesellschaft (Civil Society): §§ 182-256
  - Der Staat (The State): §§ 257-360

### Adding texts

Place additional `.txt` files in a subdirectory under `texts/`. Each
subdirectory represents one work. Files should follow this format:

```
---
Werk: Title of the Work
Paragraph: § 142
Abschnitt: Section Name
TWA: Bd. 7, S. 292
GW: Bd. 14,1, S. 137
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
│   └── hegel.vim           # Vim command definitions
├── texts/
│   └── 1821-grundlinien-der-philosophie-des-rechts/
│       ├── 000-vorrede.txt
│       ├── 001-par-001.txt
│       ├── ...
│       └── 360-par-360.txt
├── scripts/                # Text fetching utilities (planned)
└── README.md
```

## Roadmap

- [ ] Complete text of Grundlinien der Philosophie des Rechts (all 360 §§)
- [ ] Include Zusätze (Gans 1833 edition) as separate textual layer
- [ ] Add more works (Phänomenologie des Geistes, Wissenschaft der Logik, Enzyklopädie)
- [ ] `:HegelStelle` — look up passages by TWA or GW page number
- [ ] Citation export to clipboard (`Hegel, GPR § 142 Anm.`)
- [ ] Begriffregister (concept index) for key philosophical terms
- [ ] Custom `ft=hegel` syntax highlighting for §, Anmerkung, Zusatz layers
- [ ] `scripts/fetch_texts.sh` to download texts from public domain sources

## License

The plugin code is released under the MIT License.

Hegel's texts (1821/1833) are in the public domain.
