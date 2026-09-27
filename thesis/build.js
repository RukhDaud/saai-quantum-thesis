const fs = require('fs');
const D = JSON.parse(fs.readFileSync('doc.json', 'utf8'));
const OUT = process.argv[2] || 'PhD_Thesis_Draft_v3.docx';
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, PageBreak, Footer, PageNumber, TableOfContents, LevelFormat, PageOrientation,
} = require('docx');

const FONT = 'Times New Roman';
const run = (r, extra = {}) => new TextRun({
  text: r.text, bold: r.bold || extra.bold, italics: extra.italics,
  highlight: r.hl ? 'yellow' : undefined, font: FONT, size: extra.size || 24,
});
const runs = (rs, extra) => rs.map(r => run(r, extra));
const border = { style: BorderStyle.SINGLE, size: 4, color: '808080' };
const borders = { top: border, bottom: border, left: border, right: border };

const PORTRAIT_W = 9000;   // 12240 - 1800 - 1440
const LAND_W = 12960;      // 15840 - 1440 - 1440
const sections = [{ land: false, children: [] }];
let cur = sections[0].children;
let pagebreaks = 0;

function makeTable(b, textWidth, fontSize) {
  const raw = b.widths; const rt = raw.reduce((a, c) => a + c, 0);
  const widths = raw.map(w => Math.floor(w * textWidth / rt));
  widths[widths.length - 1] += textWidth - widths.reduce((a, c) => a + c, 0);
  const mk = (cells, head) => new TableRow({ tableHeader: head, cantSplit: true, children: cells.map((c, i) => new TableCell({
    borders, width: { size: widths[i], type: WidthType.DXA },
    shading: head ? { fill: 'D9E2F3', type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 50, bottom: 50, left: 80, right: 80 },
    children: [new Paragraph({ children: runs(c, { bold: head, size: fontSize }) })] })) });
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 120 }, keepNext: true,
      children: runs(b.caption, { bold: true, size: 22 }) }),
    new Table({ width: { size: textWidth, type: WidthType.DXA }, columnWidths: widths,
      rows: [mk(b.header, true), ...b.rows.map(r => mk(r, false))] }),
    new Paragraph({ spacing: { after: 200 }, children: [] }),
  ];
}

for (const b of D.blocks) {
  switch (b.t) {
    case 'title':
      cur.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 600 }, children: runs(b.runs, { bold: true, size: 36 }) }));
      break;
    case 'meta':
      cur.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: runs(b.runs, { size: 24 }) }));
      break;
    case 'h1':
      cur.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(b.runs, { bold: true, size: 32 }) }));
      break;
    case 'h2':
      cur.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(b.runs, { bold: true, size: 28 }) }));
      break;
    case 'h3':
      cur.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: runs(b.runs, { bold: true, size: 24 }) }));
      break;
    case 'p':
      cur.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 160, line: 360 }, children: runs(b.runs) }));
      break;
    case 'bullets':
    case 'numbered':
      for (const it of b.items) cur.push(new Paragraph({ numbering: { reference: b.t === 'bullets' ? 'bul' : 'num', level: 0 },
        alignment: AlignmentType.JUSTIFIED, spacing: { after: 80, line: 360 }, children: runs(it) }));
      break;
    case 'table':
      cur.push(...makeTable(b, PORTRAIT_W, 20));
      break;
    case 'table_land': {
      const land = { land: true, children: makeTable(b, LAND_W, 17) };
      const after = { land: false, children: [] };
      sections.push(land, after); cur = after.children;
      break;
    }
    case 'pagebreak':
      cur.push(new Paragraph({ children: [new PageBreak()] }));
      pagebreaks++;
      if (pagebreaks === 2) {
        cur.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: 'Table of Contents', font: FONT, bold: true, size: 32 })] }),
          new TableOfContents('Table of Contents', { hyperlink: true, headingStyleRange: '1-2' }),
          new Paragraph({ children: [new PageBreak()] }));
      }
      break;
  }
}

cur.push(new Paragraph({ children: [new PageBreak()] }));
cur.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: 'References', font: FONT, bold: true, size: 32 })] }));
for (const r of D.refs)
  cur.push(new Paragraph({ spacing: { after: 100 }, indent: { left: 567, hanging: 567 }, alignment: AlignmentType.LEFT,
    children: [new TextRun({ text: `[${r.n}]\t${r.ieee}`, font: FONT, size: 22, highlight: r.st === 'Checked' ? undefined : 'yellow' })] }));

const footer = () => new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })] })] });

const doc = new Document({
  creator: 'Saadia Sadaf', title: D.title, features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 32, bold: true, font: FONT }, paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, font: FONT }, paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, font: FONT }, paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: 'num', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ] },
  sections: sections.map(s => ({
    properties: { page: s.land
      ? { size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } }
      : { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1800, right: 1440 } } },
    footers: { default: footer() },
    children: s.children,
  })),
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(OUT, buf); console.log('ok', OUT, sections.length, 'sections'); });
