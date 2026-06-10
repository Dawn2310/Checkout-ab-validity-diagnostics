# Manuscript — Springer Nature LaTeX

## Files

| File | Purpose |
|---|---|
| `sn-article.tex` | Main manuscript (Springer Nature `sn-jnl` class) |
| `references.bib` | Bibliography (copied from `../references.bib`) |
| `sn-jnl.cls` | Springer Nature class file |
| `sn-mathphys-num.bst` | Numbered-reference bibstyle (Math & Physical Sciences) |
| `figures/` | All 14 PNG figures referenced from the manuscript |

## Compile locally

```bash
cd paper/manuscript
pdflatex sn-article
bibtex   sn-article
pdflatex sn-article
pdflatex sn-article
```

## Compile on Overleaf

1. Upload the entire `paper/manuscript/` folder as a new project.
2. Set the compiler to **pdfLaTeX**.
3. Click Recompile.

## What to edit before submission

- `\title{...}` and subtitle if you want to tweak the wording.
- `\author*[1]{...}` — name, email, affiliation block.
- `\bmhead{Code and data availability}` — paste your actual GitHub URL.
- Numbers in tables/abstract were pasted from `output/statistical_results.txt`
  and the `output/tables/*.csv` files. If you re-run `python main.py` and
  numbers change, update them by hand or regenerate via a small script.
- If the journal requires the author-year style, change the class option
  from `sn-mathphys-num` to `sn-mathphys-ay` (or another supported style)
  in line 4 of `sn-article.tex`.

## Reference style

Currently using `sn-mathphys-num` (numeric citations). Alternatives:

| Class option | Style | Use when |
|---|---|---|
| `sn-mathphys-num` | numeric \[1\], \[2\] | most data-science/ML journals |
| `sn-mathphys-ay` | author-year | Marketing Science, JAMS |
| `sn-vancouver-num` | Vancouver numeric | medical journals |
| `sn-basic` | publisher default | when in doubt |

Change in line 4 of `sn-article.tex`.
