"""Generates the thesis figures from one source, in three formats each:
  *.drawio  - editable in draw.io / diagrams.net (desktop app or app.diagrams.net)
  *.svg     - vector version (editable in Inkscape, PowerPoint, Word)
  *.png     - raster version embedded in the thesis document (300 dpi equivalent)

    python make_diagrams.py
"""
import html
import os

import cairosvg

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "Times New Roman"


class Box:
    def __init__(self, bid, x, y, w, h, lines, fill="#FFFFFF", stroke="#333333", bold_first=True,
                 align="center", size=13, rounded=True, dashed=False, rotate=False):
        self.__dict__.update(locals())
        del self.__dict__["self"]


class Edge:
    def __init__(self, src, tgt, s_side="bottom", t_side="top", points=None, dashed=False, label=None):
        self.__dict__.update(locals())
        del self.__dict__["self"]


def anchor(b, side):
    return {"top": (b.x + b.w / 2, b.y), "bottom": (b.x + b.w / 2, b.y + b.h),
            "left": (b.x, b.y + b.h / 2), "right": (b.x + b.w, b.y + b.h / 2)}[side]


# ---------------------------------------------------------------- SVG
def svg(boxes, edges, W, H):
    B = {b.bid: b for b in boxes}
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{FONT}, Liberation Serif, serif">',
         '<defs><marker id="a" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
         '<path d="M0,0 L10,4 L0,8 z" fill="#333333"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    for b in boxes:
        rx = 8 if b.rounded else 0
        dash = ' stroke-dasharray="6,4"' if b.dashed else ""
        o.append(f'<rect x="{b.x}" y="{b.y}" width="{b.w}" height="{b.h}" rx="{rx}" fill="{b.fill}" '
                 f'stroke="{b.stroke}" stroke-width="1.4"{dash}/>')
        lh = b.size * 1.28
        if b.rotate:
            cx, cy = b.x + b.w / 2, b.y + b.h / 2
            o.append(f'<text x="{cx}" y="{cy}" font-size="{b.size}" font-weight="bold" text-anchor="middle" '
                     f'dominant-baseline="middle" transform="rotate(-90 {cx} {cy})">{html.escape(b.lines[0])}</text>')
            continue
        y0 = b.y + b.h / 2 - lh * (len(b.lines) - 1) / 2
        for i, ln in enumerate(b.lines):
            bold = b.bold_first and i == 0
            if b.align == "left":
                x, anc = b.x + 10, "start"
            else:
                x, anc = b.x + b.w / 2, "middle"
            fw = ' font-weight="bold"' if bold else ""
            o.append(f'<text x="{x}" y="{y0 + i * lh}" font-size="{b.size}" text-anchor="{anc}" '
                     f'dominant-baseline="middle"{fw}>{html.escape(ln)}</text>')
    for e in edges:
        p0, p1 = anchor(B[e.src], e.s_side), anchor(B[e.tgt], e.t_side)
        pts = [p0] + (e.points or []) + [p1]
        d = " ".join(f"{'M' if i == 0 else 'L'}{x},{y}" for i, (x, y) in enumerate(pts))
        dash = ' stroke-dasharray="6,4"' if e.dashed else ""
        o.append(f'<path d="{d}" fill="none" stroke="#333333" stroke-width="1.4"{dash} marker-end="url(#a)"/>')
        if e.label:
            mx = (pts[-2][0] + pts[-1][0]) / 2 if len(pts) > 2 else (p0[0] + p1[0]) / 2
            my = (pts[-2][1] + pts[-1][1]) / 2 if len(pts) > 2 else (p0[1] + p1[1]) / 2
            o.append(f'<text x="{mx + 6}" y="{my - 6}" font-size="11" font-style="italic">{html.escape(e.label)}</text>')
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- draw.io
def drawio(boxes, edges, W, H, name):
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for b in boxes:
        if b.rotate:
            val = f"<b>{html.escape(b.lines[0])}</b>"
            style = (f"rounded={int(b.rounded)};whiteSpace=wrap;html=1;fillColor={b.fill};strokeColor={b.stroke};"
                     f"fontFamily={FONT};fontSize={b.size};horizontal=0;")
        else:
            parts = [(f"<b>{html.escape(l)}</b>" if (b.bold_first and i == 0) else html.escape(l)) for i, l in enumerate(b.lines)]
            val = "<br>".join(parts)
            style = (f"rounded={int(b.rounded)};whiteSpace=wrap;html=1;fillColor={b.fill};strokeColor={b.stroke};"
                     f"fontFamily={FONT};fontSize={b.size};align={b.align};spacingLeft=6;arcSize=6;"
                     + ("dashed=1;" if b.dashed else ""))
        cells.append(f'<mxCell id="{b.bid}" value="{html.escape(val)}" style="{style}" vertex="1" parent="1">'
                     f'<mxGeometry x="{b.x}" y="{b.y}" width="{b.w}" height="{b.h}" as="geometry"/></mxCell>')
    sides = {"top": (0.5, 0), "bottom": (0.5, 1), "left": (0, 0.5), "right": (1, 0.5)}
    for i, e in enumerate(edges):
        ex, ey = sides[e.s_side]
        nx, ny = sides[e.t_side]
        style = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeColor=#333333;"
                 f"exitX={ex};exitY={ey};entryX={nx};entryY={ny};fontFamily={FONT};fontSize=11;fontStyle=2;"
                 + ("dashed=1;" if e.dashed else ""))
        pts = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in (e.points or []))
        geo = (f'<mxGeometry relative="1" as="geometry"><Array as="points">{pts}</Array></mxGeometry>'
               if pts else '<mxGeometry relative="1" as="geometry"/>')
        lab = html.escape(e.label or "")
        cells.append(f'<mxCell id="e{i}" value="{lab}" style="{style}" edge="1" parent="1" source="{e.src}" '
                     f'target="{e.tgt}">{geo}</mxCell>')
    return (f'<mxfile host="app.diagrams.net"><diagram name="{html.escape(name)}">'
            f'<mxGraphModel dx="{W}" dy="{H}" grid="1" gridSize="10" guides="1" page="1" pageWidth="{W}" '
            f'pageHeight="{H}" math="0" shadow="0"><root>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>')


def write(stem, boxes, edges, W, H, name):
    s = svg(boxes, edges, W, H)
    open(os.path.join(OUT, stem + ".svg"), "w").write(s)
    open(os.path.join(OUT, stem + ".drawio"), "w").write(drawio(boxes, edges, W, H, name))
    cairosvg.svg2png(bytestring=s.encode(), write_to=os.path.join(OUT, stem + ".png"), scale=3)
    print("wrote", stem, "(.drawio .svg .png)")


# ================================================================ PRISMA 2020
def prisma():
    grey, blue = "#F2F2F2", "#DCE6F2"
    W, H = 900, 640
    bx = [
        Box("idl", 20, 20, 40, 170, ["Identification"], fill=blue, rotate=True),
        Box("scl", 20, 220, 40, 290, ["Screening"], fill=blue, rotate=True),
        Box("inl", 20, 540, 40, 90, ["Included"], fill=blue, rotate=True),
        Box("id", 80, 20, 420, 170, [
            "Records identified (n = 202)",
            "Reference lists of the research proposal",
            "and earlier drafts (n = 134)",
            "Structured keyword search and backward/forward",
            "citation tracing (n = 38)",
            "Standards, regulations, tools and statistical",
            "methods added during method development (n = 30)"], align="left"),
        Box("dup", 560, 70, 320, 70, ["Records removed before screening", "Duplicate records (n = 8)"], fill=grey, align="left"),
        Box("sc", 80, 250, 420, 60, ["Records screened (n = 194)"]),
        Box("ex1", 560, 225, 320, 110, [
            "Records excluded (n = 9)",
            "Record could not be confirmed (n = 1)",
            "Grey literature, commercial report or",
            "non-peer-reviewed preprint (n = 3)",
            "Outside the scope of the review (n = 5)"], fill=grey, align="left"),
        Box("fa", 80, 400, 420, 60, ["Full-text records assessed for eligibility (n = 185)"]),
        Box("ex2", 560, 375, 320, 110, [
            "Records excluded after full text (n = 8)",
            "Not used in the final synthesis (n = 8)"], fill=grey, align="left"),
        Box("inc", 80, 540, 420, 90, [
            "Sources included in the review (n = 177)",
            "of which 45 studies are summarised",
            "study by study in Table 2.15"]),
    ]
    ed = [Edge("id", "sc"), Edge("id", "dup", "right", "left"),
          Edge("sc", "fa"), Edge("sc", "ex1", "right", "left"),
          Edge("fa", "inc"), Edge("fa", "ex2", "right", "left")]
    write("fig2_1_prisma", bx, ed, W, H, "PRISMA 2020 flow")


# ================================================================ Architecture / proposed model
def architecture():
    W, H = 1000, 1210
    c_in, c_a, c_b, c_c, c_e = "#FFF2CC", "#DAE8FC", "#E1D5E7", "#D5E8D4", "#F8CECC"
    L, MW = 60, 560          # main column
    R, RW = 660, 320         # artefact / RQ column
    bx = [
        Box("reg", L, 20, MW, 80, ["Safety requirements (natural language)",
            "EU Implementing Regulation 2022/1426, Annexes II and III",
            "UN Regulation No 157 (ALKS), paragraphs 2, 5, 6 and 7"], fill=c_in),
        Box("cor", L, 140, MW, 70, ["1  Requirements corpus",
            "441 verbatim statements with stable identifiers",
            "(370 from EU 2022/1426; 71 from UN R157)"], fill=c_a),
        Box("lib", L, 250, MW, 90, ["2  Formal ODD condition library",
            "29 conditions: dimension, variable, operator, threshold, unit, response",
            "ODD conditions | performance limits | boundary responses | activation",
            "Threshold recorded only when the clause states it"], fill=c_a),
        Box("pred", L, 380, MW, 80, ["3  Phase A: executable ODD boundary predicates",
            "P1 to P8, each a Boolean test on a scenario,",
            "carrying the identifier of its source clause"], fill=c_a),
        Box("space", L, 500, MW, 70, ["4  ODD scenario space and candidate pool",
            "6 dimensions (972 concrete scenarios); pool of n candidates, budget k"], fill=c_b),
        Box("qubo", L, 610, MW, 100, ["5  Phase B: QUBO scenario selection",
            "Coverage-aligned objective: min  −Σ |Pi| xi + Σ |Pi ∩ Pj| xi xj + C(Σ xi − k)²",
            "Solvers: QAOA (statevector simulator), exact enumeration,",
            "simulated annealing, genetic algorithm, greedy; sub-QUBO decomposition"], fill=c_b),
        Box("osc", L, 760, MW, 70, ["6  Executable test scenarios",
            "ASAM OpenSCENARIO 1.1 files with ODD levels, predicates and source clauses"], fill=c_c),
        Box("sim", L, 870, MW, 90, ["7  Simulation-based execution",
            "Longitudinal model of the UN R157 ALKS, cross-checked against esmini",
            "Environment effects from published measurements (friction, visibility); planted faults",
            "Oracle: collision = FAIL (EU 2022/1426 Annex III 1.4.2)"], fill=c_c),
        Box("eval", L, 1000, MW, 90, ["8  Evaluation and traceability",
            "Coverage, fault detection, computational cost, statistical tests",
            "Trace audit: result → scenario → predicate → condition → clause"], fill=c_e),
        Box("out", L, 1130, MW, 60, ["Traceable, optimised verification evidence",
            "for ODD boundaries of automated driving systems"], fill="#FFFFFF"),
        # right column: artefacts and research questions
        Box("tm", R, 250, RW, 90, ["Traceability matrix",
            "clause → condition → predicate",
            "→ code representation (or gap)"], fill="#FFFFFF", dashed=True),
        Box("rq1", R, 380, RW, 80, ["RQ1", "Share of requirements mapped to a",
            "traceable ODD boundary predicate"], fill="#FFFFFF", dashed=True),
        Box("ref", R, 610, RW, 100, ["Reference optimum",
            "exhaustive enumeration (n ≤ 20) or",
            "integer linear programme (n > 20)", "RQ2: coverage   RQ3: cost and scale"],
            fill="#FFFFFF", dashed=True),
        Box("rq2", R, 870, RW, 90, ["RQ2", "Fault detection of the selected", "scenario sets in simulation"],
            fill="#FFFFFF", dashed=True),
        Box("rq4", R, 1000, RW, 90, ["RQ4", "Trace completeness and change",
            "propagation after a requirement edit"], fill="#FFFFFF", dashed=True),
    ]
    ed = [Edge("reg", "cor"), Edge("cor", "lib"), Edge("lib", "pred"), Edge("pred", "space"),
          Edge("space", "qubo"), Edge("qubo", "osc"), Edge("osc", "sim"), Edge("sim", "eval"),
          Edge("eval", "out"),
          Edge("lib", "tm", "right", "left", dashed=True), Edge("pred", "rq1", "right", "left", dashed=True),
          Edge("qubo", "ref", "right", "left", dashed=True), Edge("sim", "rq2", "right", "left", dashed=True),
          Edge("eval", "rq4", "right", "left", dashed=True),
          Edge("eval", "lib", "left", "left", points=[(30, 1045), (30, 295)], dashed=True)]
    bx.append(Box("chg", 21, 560, 18, 190, ["requirement change"], fill="#FFFFFF", stroke="#FFFFFF",
                  rotate=True, size=11))
    write("fig3_1_architecture", bx, ed, W, H, "Proposed model")


# ================================================================ Literature positioning (Figure 2.2)
def positioning():
    W, H = 1000, 700
    lit, comp, gap = "#FFF2CC", "#DAE8FC", "#F8CECC"
    L, LW = 20, 330
    M, MW = 400, 300
    R, RW = 750, 230
    th = [("t1", ["ODD standards and formalisation", "SAE J3016, PAS 1883, ISO 34503,", "ASAM OpenODD, Pkl ODD (Skoglund et al.)"]),
          ("t2", ["Requirement formalisation", "Req2Spec, FRET, DeepSTL,", "specification patterns, LLM approaches"]),
          ("t3", ["Natural language to scenarios", "ScenarioNL, TARGET,", "law-derived requirements (Jian et al.)"]),
          ("t4", ["Scenario selection and coverage", "combinatorial testing, Klück et al.,", "ODD-based allocation"]),
          ("t5", ["Quantum test optimisation", "BootQA, SelectQA, IGDec-QAOA,", "QAOA selection, Araujo et al."]),
          ("t6", ["Traceability and change", "Wohlrab et al., TVR,", "ODD mapping study (Hillen et al.)"])]
    bx = [Box("hl", L, 15, LW, 30, ["Reviewed literature (Chapter 2)"], fill="#FFFFFF", stroke="#FFFFFF"),
          Box("hm", M, 15, MW, 30, ["ReqODD-Q component"], fill="#FFFFFF", stroke="#FFFFFF"),
          Box("hr", R, 15, RW, 30, ["Gap addressed"], fill="#FFFFFF", stroke="#FFFFFF")]
    y = 60
    for tid, lines in th:
        bx.append(Box(tid, L, y, LW, 90, lines, fill=lit, size=12)); y += 105
    cm = [("a", 80, ["Phase A", "condition library with trace", "links; boundary predicates"]),
          ("b", 250, ["Phase B", "coverage-aligned QUBO;", "QAOA, exact and classical solvers"]),
          ("c", 420, ["Change-aware re-selection", "impact set through trace links;", "stability term"]),
          ("d", 570, ["Fault-detection evaluation", "R157 model, sourced environment,", "mutation analysis"])]
    for cid, yy, lines in cm:
        bx.append(Box(cid, M, yy, MW, 90, lines, fill=comp, size=12))
    gp = [("g1", 80, ["Gap 1", "ODD not derived from", "stated requirements"]),
          ("g2", 200, ["Gap 2", "no optimised selection from", "requirement-level conditions"]),
          ("g3", 320, ["Gap 3", "formulation fidelity", "not examined"]),
          ("g4", 440, ["Gap 4", "no change-aware", "re-selection"])]
    for gid, yy, lines in gp:
        bx.append(Box(gid, R, yy, RW, 80, lines, fill=gap, size=12))
    ed = [Edge("t1", "a", "right", "left"), Edge("t2", "a", "right", "left"), Edge("t3", "a", "right", "left", dashed=True),
          Edge("t4", "b", "right", "left"), Edge("t5", "b", "right", "left"), Edge("t6", "c", "right", "left"),
          Edge("t4", "d", "right", "left", dashed=True),
          Edge("a", "g1", "right", "left"), Edge("b", "g2", "right", "left"), Edge("b", "g3", "right", "left"),
          Edge("c", "g4", "right", "left")]
    write("fig2_2_positioning", bx, ed, W, H, "Literature positioning")


# ================================================================ Thesis structure (Figure 1.1)
def thesis_flow():
    W, H = 1000, 560
    c1, c2, c3, c4 = "#FFF2CC", "#DAE8FC", "#E1D5E7", "#D5E8D4"
    bx = [
        Box("ch1", 20, 20, 300, 80, ["Chapter 1: Introduction", "problem, aim, objectives, RQ1-RQ4"], fill=c1),
        Box("ch2", 350, 20, 300, 80, ["Chapter 2: Literature Review", "45 studies; four research gaps"], fill=c1),
        Box("ch3", 680, 20, 300, 80, ["Chapter 3: Methodology", "corpus, conditions, predicates, QUBO,", "re-selection, R157 model"], fill=c2),
        Box("ch4", 680, 150, 300, 80, ["Chapter 4: Feasibility Study", "extraction; first formulation;", "coverage-aligned formulation"], fill=c2),
        Box("rq1", 20, 290, 220, 80, ["RQ1", "requirements to traceable", "predicates"], fill=c3),
        Box("rq2", 265, 290, 220, 80, ["RQ2", "coverage and", "fault detection"], fill=c3),
        Box("rq3", 510, 290, 220, 80, ["RQ3", "cost and scaling;", "decomposition"], fill=c3),
        Box("rq4", 755, 290, 225, 80, ["RQ4", "traceability and", "change-aware re-selection"], fill=c3),
        Box("ch5", 20, 420, 700, 60, ["Chapter 5: Evaluation of Selection and Traceability", "RQ1, RQ2 (coverage), RQ3, RQ4"], fill=c4),
        Box("ch6", 750, 420, 230, 60, ["Chapter 6: Fault Detection", "RQ2 (fault detection)"], fill=c4),
        Box("ch7", 250, 500, 500, 50, ["Chapter 7: Discussion and Conclusion"], fill=c1),
    ]
    ed = [Edge("ch1", "ch2", "right", "left"), Edge("ch2", "ch3", "right", "left"), Edge("ch3", "ch4"),
          Edge("ch4", "rq4", "bottom", "top", points=[(830, 260)]),
          Edge("ch4", "rq1", "left", "top", points=[(130, 190)]), Edge("ch4", "rq2", "left", "top", points=[(375, 190)]),
          Edge("ch4", "rq3", "left", "top", points=[(620, 190)]),
          Edge("rq1", "ch5"), Edge("rq2", "ch5"), Edge("rq3", "ch5"),
          Edge("rq4", "ch5", "bottom", "top", points=[(867, 395), (680, 395)]),
          Edge("ch5", "ch6", "right", "left"),
          Edge("ch5", "ch7", "bottom", "top", points=[(370, 490), (400, 490)]),
          Edge("ch6", "ch7", "bottom", "top", points=[(865, 490), (600, 490)])]
    write("fig1_1_structure", bx, ed, W, H, "Thesis structure")


if __name__ == "__main__":
    prisma()
    architecture()
    positioning()
    thesis_flow()
