# Thesis figures (editable)

| Figure | draw.io (edit) | SVG (vector) | PNG (in thesis) |
|---|---|---|---|
| Figure 2.1 PRISMA 2020 flow diagram | `fig2_1_prisma.drawio` | `fig2_1_prisma.svg` | `fig2_1_prisma.png` |
| Figure 3.1 Proposed model | `fig3_1_architecture.drawio` | `fig3_1_architecture.svg` | `fig3_1_architecture.png` |
| Figure 3.2 TRACE-Q framework (layered) | `fig3_2_framework.drawio` | `fig3_2_framework.svg` | `fig3_2_framework.png` |

Edit: open the `.drawio` file at https://app.diagrams.net (File → Open from → Device) or in the draw.io desktop app,
then File → Export as → PNG (300 dpi) to replace the image in the thesis.
Regenerate from code: `python make_diagrams.py` (Figures 2.1, 3.1) and `python make_framework.py` (Figure 3.2); needs `pip install cairosvg`.
In Figure 3.2 every text, box, icon and arrow is a separate draw.io object; icons are embedded SVG images and can be replaced from draw.io's icon libraries.
