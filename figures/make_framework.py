"""Figure 3.2: layered framework diagram (editable).

Writes fig3_2_framework.drawio (open in draw.io / app.diagrams.net), .svg and .png.
Every element - panels, cards, texts, icons, arrows - is a separate draw.io object, so text
can be retyped, icons swapped (they are embedded SVG images) and boxes moved or recoloured.

    python make_framework.py
"""
import base64
import html
import os

import cairosvg

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "Times New Roman"
W, H = 1500, 1010
INK = "#1A1A1A"

# ------------------------------------------------------------------ icons (40 x 40 SVG)
S = f'fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    "doc": f'<path {S} d="M9 3h15l8 8v26H9z M24 3v8h8"/><path {S} d="M14 17h13 M14 23h13 M14 29h9"/>',
    "network": f'<g {S}><circle cx="20" cy="7" r="4"/><circle cx="7" cy="32" r="4"/><circle cx="33" cy="32" r="4"/>'
               f'<circle cx="20" cy="22" r="3"/><path d="M20 11v8 M18 24l-9 6 M22 24l9 6"/></g>',
    "grid": f'<g {S}><rect x="5" y="5" width="30" height="30"/><path d="M15 5v30 M25 5v30 M5 15h30 M5 25h30"/></g>'
            f'<rect x="15" y="15" width="10" height="10" fill="{INK}"/>',
    "car": f'<g {S}><path d="M4 26v-6l5-8h20l6 8v6z"/><path d="M11 12l-3 8h24l-4-8"/></g>'
           f'<circle cx="11" cy="28" r="4" fill="#fff" stroke="{INK}" stroke-width="2"/>'
           f'<circle cx="29" cy="28" r="4" fill="#fff" stroke="{INK}" stroke-width="2"/>',
    "db": f'<g {S}><ellipse cx="20" cy="8" rx="13" ry="4"/><path d="M7 8v24c0 2.2 5.8 4 13 4s13-1.8 13-4V8"/>'
          f'<path d="M7 16c0 2.2 5.8 4 13 4s13-1.8 13-4 M7 24c0 2.2 5.8 4 13 4s13-1.8 13-4"/></g>',
    "list": f'<g {S}><rect x="6" y="4" width="28" height="32" rx="2"/><path d="M11 12l2 2 4-4 M11 21l2 2 4-4 M11 30l2 2 4-4'
            f' M20 12h9 M20 21h9 M20 30h9"/></g>',
    "code": f'<g {S}><path d="M13 11l-8 9 8 9 M27 11l8 9-8 9 M23 7l-6 26"/></g>',
    "matrix": f'<g {S}><path d="M8 5H5v30h3 M32 5h3v30h-3"/></g>'
              + "".join(f'<rect x="{9 + 6 * c}" y="{8 + 6 * r}" width="4" height="4" fill="{INK if (r + c) % 3 == 0 else "none"}" '
                        f'stroke="{INK}" stroke-width="1.2"/>' for r in range(4) for c in range(4)),
    "atom": f'<g {S}><ellipse cx="20" cy="20" rx="16" ry="6"/><ellipse cx="20" cy="20" rx="16" ry="6" transform="rotate(60 20 20)"/>'
            f'<ellipse cx="20" cy="20" rx="16" ry="6" transform="rotate(-60 20 20)"/></g><circle cx="20" cy="20" r="3" fill="{INK}"/>',
    "sim": f'<g {S}><rect x="3" y="5" width="34" height="23" rx="2"/><path d="M14 36h12 M20 28v8"/>'
           f'<path d="M12 26l6-17 M28 26l-6-17 M20 12v3 M20 18v3"/></g>',
    "check": f'<g {S}><rect x="7" y="5" width="26" height="32" rx="2"/><path d="M15 3h10v5H15z"/>'
             f'<path d="M12 17l2 2 4-4 M21 17h7 M12 27l2 2 4-4 M21 27h7"/></g>',
    "chart": f'<g {S}><path d="M5 35h30"/></g><rect x="8" y="22" width="5" height="12" fill="{INK}"/>'
             f'<rect x="16" y="15" width="5" height="19" fill="{INK}"/><rect x="24" y="8" width="5" height="26" fill="{INK}"/>',
    "link": f'<g {S}><rect x="4" y="15" width="18" height="10" rx="5" transform="rotate(-35 13 20)"/>'
            f'<rect x="18" y="15" width="18" height="10" rx="5" transform="rotate(-35 27 20)"/></g>',
    "shield": f'<g {S}><path d="M20 3l14 5v10c0 9-6 16-14 19C12 34 6 27 6 18V8z"/><path d="M13 19l5 5 9-10"/></g>',
    "gear": f'<g {S}><circle cx="20" cy="20" r="6"/><path d="M20 3v6 M20 31v6 M3 20h6 M31 20h6 M8 8l4 4 M28 28l4 4 M8 32l4-4 M28 12l4-4"/>'
            f'<circle cx="20" cy="20" r="12"/></g>',
}


def icon_svg(name):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">{ICONS[name]}</svg>'


# ------------------------------------------------------------------ element model
E = []  # (kind, dict)


def rect(x, y, w, h, fill="#FFFFFF", stroke=INK, sw=1.5, r=10, dashed=False):
    E.append(("rect", dict(x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, sw=sw, r=r, dashed=dashed)))


def text(x, y, w, h, lines, size=13, bold_first=False, bold=False, color=INK, align="center", italic=False):
    E.append(("text", dict(x=x, y=y, w=w, h=h, lines=lines, size=size, bold_first=bold_first, bold=bold,
                           color=color, align=align, italic=italic)))


def band(x, y, w, h, label, size=14):
    rect(x, y, w, h, fill=INK, stroke=INK, r=4)
    text(x, y, w, h, [label], size=size, bold=True, color="#FFFFFF")


def icon(name, x, y, s=40):
    E.append(("icon", dict(name=name, x=x, y=y, s=s)))


def arrow(p0, p1, pts=(), dashed=False, both=False):
    E.append(("arrow", dict(p0=p0, p1=p1, pts=list(pts), dashed=dashed, both=both)))


def num(n, x, y):
    E.append(("num", dict(n=n, x=x, y=y)))


# ------------------------------------------------------------------ layout
L1C, L2C = "#EAF2FB", "#F3ECF8"
PX, PW = 230, 1040          # central panels
# title
rect(250, 10, 1000, 92, r=8, sw=2)
text(250, 14, 1000, 36, ["ReqODD-Q FRAMEWORK"], size=28, bold=True)
text(250, 50, 1000, 24, ["Requirement-to-ODD Quantum Scenario Selection"], size=17, bold=True)
text(250, 74, 1000, 22, ["(grounded in EU Implementing Regulation 2022/1426 and UN Regulation No 157)"], size=14)

# inputs column
rect(20, 130, 170, 700, r=10, sw=2)
band(20, 130, 170, 40, "INPUTS")
inputs = [("doc", ["Regulatory safety", "requirements", "(EU 2022/1426, R157)"]),
          ("network", ["ODD taxonomies", "(ISO 34503, PAS 1883)"]),
          ("grid", ["ODD scenario", "parameter space"]),
          ("car", ["System under test", "(R157 ALKS model)"])]
for i, (ic, lines) in enumerate(inputs):
    y = 190 + i * 160
    icon(ic, 85, y, 44)
    text(25, y + 48, 160, 60, lines, size=13)

# outputs column
rect(1310, 130, 170, 700, r=10, sw=2)
rect(1310, 130, 170, 52, fill=INK, stroke=INK, r=4)
text(1310, 130, 170, 52, ["OUTPUTS &", "TRACEABILITY"], size=14, bold=True, color="#FFFFFF")
outputs = [("check", ["Optimised, budgeted", "scenario set"]),
           ("chart", ["Coverage and fault-", "detection evidence"]),
           ("link", ["Traceability matrix", "(clause to result)"]),
           ("atom", ["Quantum vs classical", "empirical assessment"]),
           ("shield", ["Change-aware", "re-selection"])]
for i, (ic, lines) in enumerate(outputs):
    y = 200 + i * 126
    icon(ic, 1375, y, 40)
    text(1315, y + 42, 160, 44, lines, size=13)

# layer 1
rect(PX, 130, PW, 250, fill=L1C, r=10, sw=2)
band(PX + PW / 2 - 70, 120, 140, 26, "LAYER 1", size=13)
text(PX, 148, PW, 28, ["Requirements and ODD Formalisation Layer"], size=19, bold=True)
l1 = [("db", "Verbatim Requirements Corpus", ["441 statements with stable identifiers:", "370 from EU 2022/1426, 71 from UN R157"]),
      ("list", "Formal ODD Condition Library", ["29 conditions: dimension, variable,", "operator, threshold, unit, response"]),
      ("code", "Executable Boundary Predicates", ["Boolean tests on scenarios, each", "carrying its source-clause identifier"])]
for i, (ic, title, desc) in enumerate(l1):
    x = 250 + i * 340
    rect(x, 182, 320, 180, r=8)
    text(x, 188, 320, 26, [title], size=15, bold=True)
    icon(ic, x + 138, 222, 46)
    text(x, 278, 320, 70, desc, size=13)

# pipeline
band(PX + PW / 2 - 150, 390, 300, 28, "ReqODD-Q PIPELINE (6 STAGES)", size=13)
stages = [("doc", ["Requirements", "Formalisation"], ["Corpus, condition", "library and traced", "predicates"], "RQ1"),
          ("grid", ["ODD Scenario", "Space"], ["6 dimensions,", "972 scenarios,", "candidate pools"], "EU 2022/1426 3.1.4.1"),
          ("matrix", ["QUBO", "Formulation"], ["Coverage-aligned", "objective, budget,", "exact reference"], "RQ2"),
          ("atom", ["Hybrid Quantum-", "Classical Solving"], ["QAOA, exact,", "SA, GA, greedy;", "decomposition"], "RQ3"),
          ("sim", ["Scenario Generation", "and Simulation"], ["OpenSCENARIO 1.1,", "R157 ALKS model,", "planted faults"], "RQ2"),
          ("check", ["Evaluation and", "Traceability"], ["Coverage, faults,", "cost, statistics,", "trace audit"], "RQ4")]
SW, SG, SY, SH = 156, 20, 426, 178
for i, (ic, title, desc, tag) in enumerate(stages):
    x = 234 + i * (SW + SG)
    rect(x, SY, SW, SH, r=8)
    num(i + 1, x + 16, SY + 18)
    text(x + 26, SY + 4, SW - 28, 40, title, size=13, bold=True)
    icon(ic, x + SW / 2 - 20, SY + 50, 40)
    text(x, SY + 92, SW, 56, desc, size=12)
    text(x, SY + 150, SW, 22, [tag], size=11, italic=True)
    if i < 5:
        arrow((x + SW, SY + SH / 2), (x + SW + SG, SY + SH / 2))

# layer 2
rect(PX, 632, PW, 250, fill=L2C, r=10, sw=2)
band(PX + 20, 622, 140, 26, "LAYER 2", size=13)
text(PX, 650, PW, 28, ["Quantum Optimisation and Verification Layer"], size=19, bold=True)
l2 = [("matrix", "Coverage-Aligned QUBO", ["min −Σ|Pi|xi + Σ|Pi ∩ Pj|xixj", "+ C(Σxi − k)²; exact optimum as reference"]),
      ("atom", "Quantum and Classical Solvers", ["QAOA (statevector simulator), exact", "optimum, SA, GA, greedy, decomposition"]),
      ("sim", "Simulation-Based Verification", ["R157 ALKS model cross-checked with esmini;", "oracle: collision = FAIL (Annex III 1.4.2)"])]
for i, (ic, title, desc) in enumerate(l2):
    x = 250 + i * 340
    rect(x, 684, 320, 180, r=8)
    text(x, 690, 320, 26, [title], size=15, bold=True)
    icon(ic, x + 138, 724, 46)
    text(x, 780, 320, 70, desc, size=13)

# bottom bar
rect(PX, 900, PW, 92, r=10, sw=2)
icon("shield", PX + 24, 918, 50)
icon("gear", PX + PW - 74, 918, 50)
text(PX + 80, 906, PW - 160, 34, ["END-TO-END TRACEABILITY ACROSS BOTH LAYERS THROUGH THE ReqODD-Q PIPELINE"], size=16, bold=True)
text(PX + 80, 944, PW - 160, 40, ["Regulation clause → ODD condition → boundary predicate → selected scenario → "
                                  "simulation result → evidence;  requirement change → impact → re-selection"],
     size=13)

# legend
rect(1310, 850, 170, 142, r=8)
arrow((1322, 872), (1372, 872))
text(1378, 862, 100, 20, ["Data flow"], size=12, align="left")
arrow((1322, 900), (1372, 900), dashed=True, both=True)
text(1378, 890, 100, 20, ["Traceability link"], size=12, align="left")
rect(1322, 918, 46, 22, fill=L1C, r=3)
text(1378, 918, 100, 22, ["Layer 1"], size=12, align="left")
rect(1322, 952, 46, 22, fill=L2C, r=3)
text(1378, 952, 100, 22, ["Layer 2"], size=12, align="left")

# flows
arrow((190, 255), (230, 255))
arrow((190, 521), (234, 521))
arrow((190, 757), (230, 757))
arrow((1270, 521), (1310, 521))
for sx in (234 + SW / 2, 234 + 5 * (SW + SG) + SW / 2):          # layer 1 <-> stages 1 and 6
    arrow((sx, 380), (sx, SY), dashed=True, both=True)
for sx in (234 + 2 * (SW + SG) + SW / 2, 234 + 3 * (SW + SG) + SW / 2, 234 + 4 * (SW + SG) + SW / 2):
    arrow((sx, SY + SH), (sx, 632), dashed=True, both=True)       # stages 3-5 <-> layer 2
arrow((1310, 330), (1270, 330), dashed=True)
arrow((1310, 757), (1270, 757), dashed=True)


# ------------------------------------------------------------------ renderers
def to_svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{FONT}, Liberation Serif, serif">',
         f'<defs><marker id="a" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="{INK}"/></marker>'
         f'<marker id="b" markerWidth="10" markerHeight="8" refX="1" refY="4" orient="auto"><path d="M10,0 L0,4 L10,8 z" fill="{INK}"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    for kind, d in E:
        if kind == "rect":
            dash = ' stroke-dasharray="6,4"' if d["dashed"] else ""
            o.append(f'<rect x="{d["x"]}" y="{d["y"]}" width="{d["w"]}" height="{d["h"]}" rx="{d["r"]}" fill="{d["fill"]}" '
                     f'stroke="{d["stroke"]}" stroke-width="{d["sw"]}"{dash}/>')
        elif kind == "text":
            lh = d["size"] * 1.25
            y0 = d["y"] + d["h"] / 2 - lh * (len(d["lines"]) - 1) / 2
            x, anc = (d["x"] + 4, "start") if d["align"] == "left" else (d["x"] + d["w"] / 2, "middle")
            for i, ln in enumerate(d["lines"]):
                b = d["bold"] or (d["bold_first"] and i == 0)
                st = (' font-weight="bold"' if b else "") + (' font-style="italic"' if d["italic"] else "")
                o.append(f'<text x="{x}" y="{y0 + i * lh}" font-size="{d["size"]}" fill="{d["color"]}" text-anchor="{anc}" '
                         f'dominant-baseline="middle"{st}>{html.escape(ln)}</text>')
        elif kind == "icon":
            s = d["s"] / 40
            o.append(f'<g transform="translate({d["x"]},{d["y"]}) scale({s})">{ICONS[d["name"]]}</g>')
        elif kind == "num":
            o.append(f'<circle cx="{d["x"]}" cy="{d["y"]}" r="12" fill="{INK}"/>'
                     f'<text x="{d["x"]}" y="{d["y"]}" font-size="14" font-weight="bold" fill="#FFFFFF" text-anchor="middle" '
                     f'dominant-baseline="central">{d["n"]}</text>')
        elif kind == "arrow":
            pts = [d["p0"]] + d["pts"] + [d["p1"]]
            path = " ".join(f"{'M' if i == 0 else 'L'}{x},{y}" for i, (x, y) in enumerate(pts))
            dash = ' stroke-dasharray="6,4"' if d["dashed"] else ""
            ms = ' marker-start="url(#b)"' if d["both"] else ""
            o.append(f'<path d="{path}" fill="none" stroke="{INK}" stroke-width="1.6"{dash}{ms} marker-end="url(#a)"/>')
    o.append("</svg>")
    return "\n".join(o)


def to_drawio():
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for i, (kind, d) in enumerate(E):
        cid = f"c{i}"
        if kind == "rect":
            st = (f"rounded=1;arcSize={min(40, int(d['r'] * 100 / max(1, min(d['w'], d['h']))))};whiteSpace=wrap;html=1;"
                  f"fillColor={d['fill']};strokeColor={d['stroke']};strokeWidth={d['sw']};" + ("dashed=1;" if d["dashed"] else ""))
            cells.append(f'<mxCell id="{cid}" value="" style="{st}" vertex="1" parent="1">'
                         f'<mxGeometry x="{d["x"]}" y="{d["y"]}" width="{d["w"]}" height="{d["h"]}" as="geometry"/></mxCell>')
        elif kind == "text":
            parts = []
            for j, ln in enumerate(d["lines"]):
                t = html.escape(ln)
                if d["bold"] or (d["bold_first"] and j == 0):
                    t = f"<b>{t}</b>"
                if d["italic"]:
                    t = f"<i>{t}</i>"
                parts.append(t)
            st = (f"text;html=1;whiteSpace=wrap;align={d['align']};verticalAlign=middle;fontFamily={FONT};"
                  f"fontSize={d['size']};fontColor={d['color']};strokeColor=none;fillColor=none;")
            cells.append(f'<mxCell id="{cid}" value="{html.escape("<br>".join(parts))}" style="{st}" vertex="1" parent="1">'
                         f'<mxGeometry x="{d["x"]}" y="{d["y"]}" width="{d["w"]}" height="{d["h"]}" as="geometry"/></mxCell>')
        elif kind == "icon":
            b64 = base64.b64encode(icon_svg(d["name"]).encode()).decode()
            st = f"shape=image;verticalLabelPosition=bottom;aspect=fixed;imageAspect=0;image=data:image/svg+xml,{b64};"
            cells.append(f'<mxCell id="{cid}" value="" style="{st}" vertex="1" parent="1">'
                         f'<mxGeometry x="{d["x"]}" y="{d["y"]}" width="{d["s"]}" height="{d["s"]}" as="geometry"/></mxCell>')
        elif kind == "num":
            st = (f"ellipse;whiteSpace=wrap;html=1;fillColor={INK};strokeColor={INK};fontColor=#FFFFFF;fontStyle=1;"
                  f"fontSize=14;fontFamily={FONT};")
            cells.append(f'<mxCell id="{cid}" value="{d["n"]}" style="{st}" vertex="1" parent="1">'
                         f'<mxGeometry x="{d["x"] - 12}" y="{d["y"] - 12}" width="24" height="24" as="geometry"/></mxCell>')
        elif kind == "arrow":
            st = (f"endArrow=block;endFill=1;html=1;rounded=0;strokeColor={INK};strokeWidth=1.6;"
                  + ("dashed=1;" if d["dashed"] else "") + ("startArrow=block;startFill=1;" if d["both"] else ""))
            (x0, y0), (x1, y1) = d["p0"], d["p1"]
            cells.append(f'<mxCell id="{cid}" value="" style="{st}" edge="1" parent="1"><mxGeometry relative="1" as="geometry">'
                         f'<mxPoint x="{x0}" y="{y0}" as="sourcePoint"/><mxPoint x="{x1}" y="{y1}" as="targetPoint"/>'
                         f'</mxGeometry></mxCell>')
    return (f'<mxfile host="app.diagrams.net"><diagram name="ReqODD-Q framework"><mxGraphModel grid="1" gridSize="10" '
            f'guides="1" page="1" pageWidth="{W}" pageHeight="{H}"><root>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>')


if __name__ == "__main__":
    s = to_svg()
    open(os.path.join(OUT, "fig3_2_framework.svg"), "w").write(s)
    open(os.path.join(OUT, "fig3_2_framework.drawio"), "w").write(to_drawio())
    cairosvg.svg2png(bytestring=s.encode(), write_to=os.path.join(OUT, "fig3_2_framework.png"), scale=2.5)
    print("wrote fig3_2_framework (.drawio .svg .png)")
