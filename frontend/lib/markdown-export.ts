import { Document, HeadingLevel, Packer, Paragraph, TextRun } from "docx";
import { jsPDF } from "jspdf";

type MdRun = { text: string; bold?: boolean; italic?: boolean };
type MdBlock =
  | { type: "heading"; level: number; runs: MdRun[] }
  | { type: "paragraph"; runs: MdRun[] }
  | { type: "bullet"; runs: MdRun[] };

// A deliberately small markdown subset (headings, bold/italic, bullets,
// paragraphs) -- enough for the study summaries/explanations the AI writes,
// without pulling in a full markdown-to-PDF/DOCX pipeline for two buttons.
function parseInlineRuns(text: string): MdRun[] {
  const runs: MdRun[] = [];
  const pattern = /\*\*(.+?)\*\*|\*(.+?)\*|_(.+?)_/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      runs.push({ text: text.slice(lastIndex, match.index) });
    }
    if (match[1] !== undefined) {
      runs.push({ text: match[1], bold: true });
    } else {
      runs.push({ text: match[2] ?? match[3] ?? "", italic: true });
    }
    lastIndex = pattern.lastIndex;
  }
  if (lastIndex < text.length) {
    runs.push({ text: text.slice(lastIndex) });
  }
  return runs.length ? runs : [{ text }];
}

function parseMarkdownBlocks(markdown: string): MdBlock[] {
  const lines = markdown.split(/\r?\n/);
  const blocks: MdBlock[] = [];
  let paragraphLines: string[] = [];

  function flushParagraph() {
    const text = paragraphLines.join(" ").trim();
    paragraphLines = [];
    if (text) blocks.push({ type: "paragraph", runs: parseInlineRuns(text) });
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      continue;
    }

    const headingMatch = /^(#{1,6})\s+(.*)$/.exec(line);
    if (headingMatch) {
      flushParagraph();
      blocks.push({ type: "heading", level: headingMatch[1].length, runs: parseInlineRuns(headingMatch[2]) });
      continue;
    }

    const bulletMatch = /^[-*]\s+(.*)$/.exec(line);
    if (bulletMatch) {
      flushParagraph();
      blocks.push({ type: "bullet", runs: parseInlineRuns(bulletMatch[1]) });
      continue;
    }

    paragraphLines.push(line);
  }
  flushParagraph();
  return blocks;
}

function sanitizeFilename(name: string): string {
  return name.trim().replace(/[^\w\-]+/g, "_").slice(0, 60) || "documento";
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function downloadAsPdf(title: string, markdown: string): void {
  const blocks = parseMarkdownBlocks(markdown);
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const marginX = 48;
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const maxWidth = pageWidth - marginX * 2;
  let y = 56;

  function ensureSpace(lineHeight: number) {
    if (y + lineHeight > pageHeight - 48) {
      doc.addPage();
      y = 56;
    }
  }

  function writeRuns(runs: MdRun[], x: number, fontSize: number, lineHeight: number, indent = 0) {
    doc.setFontSize(fontSize);
    const maxLineWidth = maxWidth - indent;
    let cursorX = x;
    let lineHasContent = false;

    const tokens: { text: string; bold?: boolean; italic?: boolean; space?: boolean }[] = [];
    runs.forEach((run) => {
      run.text.split(/(\s+)/).forEach((part) => {
        if (!part) return;
        if (/^\s+$/.test(part)) {
          tokens.push({ text: " ", space: true });
        } else {
          tokens.push({ text: part, bold: run.bold, italic: run.italic });
        }
      });
    });

    tokens.forEach((token) => {
      doc.setFont("helvetica", token.bold ? "bold" : token.italic ? "italic" : "normal");
      if (token.space) {
        if (lineHasContent) cursorX += doc.getTextWidth(" ");
        return;
      }
      const wordWidth = doc.getTextWidth(token.text);
      if (lineHasContent && cursorX + wordWidth - x > maxLineWidth) {
        y += lineHeight;
        ensureSpace(lineHeight);
        cursorX = x;
        lineHasContent = false;
      }
      doc.text(token.text, cursorX, y);
      cursorX += wordWidth;
      lineHasContent = true;
    });

    y += lineHeight;
  }

  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text(title, marginX, y);
  y += 26;

  const headingSizeByLevel = [0, 16, 14, 13, 12, 12, 12];
  blocks.forEach((block) => {
    if (block.type === "heading") {
      ensureSpace(24);
      y += 6;
      writeRuns(
        block.runs.map((run) => ({ ...run, bold: true })),
        marginX,
        headingSizeByLevel[Math.min(block.level, 6)] ?? 12,
        18
      );
    } else if (block.type === "bullet") {
      ensureSpace(16);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(11);
      doc.text("-", marginX, y);
      writeRuns(block.runs, marginX + 14, 11, 16, 14);
    } else {
      ensureSpace(16);
      writeRuns(block.runs, marginX, 11, 16);
      y += 4;
    }
  });

  doc.save(`${sanitizeFilename(title)}.pdf`);
}

export async function downloadAsDocx(title: string, markdown: string): Promise<void> {
  const blocks = parseMarkdownBlocks(markdown);
  const headingLevels = [
    HeadingLevel.HEADING_1,
    HeadingLevel.HEADING_1,
    HeadingLevel.HEADING_2,
    HeadingLevel.HEADING_3,
    HeadingLevel.HEADING_4,
    HeadingLevel.HEADING_5,
    HeadingLevel.HEADING_6
  ];

  function toTextRuns(runs: MdRun[]) {
    return runs.map((run) => new TextRun({ text: run.text, bold: run.bold, italics: run.italic }));
  }

  const children: Paragraph[] = [
    new Paragraph({ text: title, heading: HeadingLevel.TITLE, spacing: { after: 240 } })
  ];

  blocks.forEach((block) => {
    if (block.type === "heading") {
      children.push(
        new Paragraph({
          heading: headingLevels[Math.min(block.level, 6)] ?? HeadingLevel.HEADING_6,
          children: toTextRuns(block.runs),
          spacing: { before: 200, after: 100 }
        })
      );
    } else if (block.type === "bullet") {
      children.push(
        new Paragraph({
          bullet: { level: 0 },
          children: toTextRuns(block.runs),
          spacing: { after: 60 }
        })
      );
    } else {
      children.push(new Paragraph({ children: toTextRuns(block.runs), spacing: { after: 120 } }));
    }
  });

  const doc = new Document({ sections: [{ children }] });
  const blob = await Packer.toBlob(doc);
  triggerDownload(blob, `${sanitizeFilename(title)}.docx`);
}
