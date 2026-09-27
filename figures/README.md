# Thesis figures (editable)

| Figure | draw.io (edit) | SVG (vector) | PNG (in thesis) |
|---|---|---|---|
| Figure 2.1 PRISMA 2020 flow diagram | `fig2_1_prisma.drawio` | `fig2_1_prisma.svg` | `fig2_1_prisma.png` |
| Figure 3.1 Proposed model | `fig3_1_architecture.drawio` | `fig3_1_architecture.svg` | `fig3_1_architecture.png` |

Edit: open the `.drawio` file at https://app.diagrams.net (File → Open from → Device) or in the draw.io desktop app,
then File → Export as → PNG (300 dpi) to replace the image in the thesis.
Regenerate all three formats from code: `python make_diagrams.py` (needs `pip install cairosvg`).
