#!/usr/bin/env python3
"""
P_311 Academic Project Report DOCX & PDF Generator
Parses and compiles PROJECT_REPORT.md into a publication-grade DOCX document,
embeds the architecture diagram, styles headers, tables, and typography,
and converts to PDF via headless LibreOffice.
"""
import re
import subprocess
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_footer_page_number(run):
    fldSimple = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
    run._r.append(fldSimple)

def generate_report():
    md_path = Path("docs/submission/PROJECT_REPORT.md")
    docx_path = Path("docs/submission/PROJECT_REPORT.docx")
    pdf_path = Path("docs/submission/PROJECT_REPORT.pdf")
    arch_png = Path("docs/submission/architecture.png")

    if not md_path.exists():
        print(f"Error: {md_path} not found.")
        return

    doc = Document()

    # Set Margins (1 inch all around)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # Header
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("P_311: Knowledge-Driven IoT Fault Diagnosis Assistant")
        hrun.font.name = "Arial"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(100, 116, 139)

        # Footer
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Page ")
        frun.font.name = "Arial"
        frun.font.size = Pt(9)
        frun.font.color.rgb = RGBColor(100, 116, 139)
        add_footer_page_number(frun)

    # Styles
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Arial'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(30, 41, 59)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    content = md_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    in_table = False
    table_rows = []

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return

        num_cols = max(len(r) for r in table_rows)
        table = doc.add_table(rows=len(table_rows), cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True

        for i, row_data in enumerate(table_rows):
            for j in range(num_cols):
                cell = table.cell(i, j)
                text = row_data[j] if j < len(row_data) else ""
                cell.text = text
                set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
                
                # Format text
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.line_spacing = 1.05
                    for run in p.runs:
                        run.font.name = "Arial"
                        run.font.size = Pt(9.5)
                        if i == 0:
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(255, 255, 255)
                        else:
                            run.font.color.rgb = RGBColor(30, 41, 59)

                if i == 0:
                    set_cell_background(cell, "0F172A") # Slate 900
                elif i % 2 == 1:
                    set_cell_background(cell, "F8FAFC") # Slate 50
                else:
                    set_cell_background(cell, "FFFFFF")

        doc.add_paragraph() # Spacing
        table_rows = []
        in_table = False

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for table
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            # Skip separator line | :--- | :--- |
            if not all(re.match(r"^:?-+:?$", c) for c in cells):
                in_table = True
                table_rows.append(cells)
            i += 1
            continue
        elif in_table:
            flush_table()

        # Page Break
        if "<div style=\"page-break-after: always;\"></div>" in line:
            doc.add_page_break()
            i += 1
            continue

        # Horizontal rule
        if line == "---":
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(8)
            i += 1
            continue

        # Headings
        if line.startswith("# "):
            text = line[2:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(text)
            run.font.name = "Arial"
            run.font.size = Pt(20)
            run.font.bold = True
            run.font.color.rgb = RGBColor(15, 23, 42) # Slate 900
            i += 1
            continue

        if line.startswith("## "):
            text = line[3:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(text)
            run.font.name = "Arial"
            run.font.size = Pt(15)
            run.font.bold = True
            run.font.color.rgb = RGBColor(2, 132, 199) # Sky 600
            i += 1
            continue

        if line.startswith("### "):
            text = line[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(text)
            run.font.name = "Arial"
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = RGBColor(51, 65, 85) # Slate 700
            i += 1
            continue

        # List items
        if line.startswith("- ") or line.startswith("* "):
            text = line[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_after = Pt(3)
            # Simple bold parsing
            parts = re.split(r"(\*\*.*?\*\*)", text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(part[2:-2])
                    r.font.bold = True
                else:
                    p.add_run(part)
            i += 1
            continue

        # Numbered lists
        m_num = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m_num:
            num = m_num.group(1)
            text = m_num.group(2)
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_after = Pt(3)
            parts = re.split(r"(\*\*.*?\*\*)", text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(part[2:-2])
                    r.font.bold = True
                else:
                    p.add_run(part)
            i += 1
            continue

        # Embed architecture image if in Section 8
        if "The P_311 architecture enforces strict horizontal layering" in line and arch_png.exists():
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(12)
            p_img.paragraph_format.space_after = Pt(4)
            run_img = p_img.add_run()
            run_img.add_picture(str(arch_png), width=Inches(6.2))
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(12)
            rcap = p_cap.add_run("Figure 8.1: P_311 End-to-End System Architecture & Layered Component Topology")
            rcap.font.size = Pt(9.5)
            rcap.font.italic = True
            rcap.font.color.rgb = RGBColor(100, 116, 139)

        # Standard Paragraph
        if line:
            p = doc.add_paragraph()
            parts = re.split(r"(\*\*.*?\*\*)", line)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(part[2:-2])
                    r.font.bold = True
                else:
                    p.add_run(part)
        else:
            # Empty line
            pass

        i += 1

    if in_table:
        flush_table()

    doc.save(str(docx_path))
    print(f"Generated DOCX: {docx_path} ({docx_path.stat().st_size} bytes)")

    # Convert to PDF via LibreOffice
    print("Converting DOCX to PDF via LibreOffice headless...")
    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(pdf_path.parent),
        str(docx_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and pdf_path.exists():
        print(f"Successfully generated PDF: {pdf_path} ({pdf_path.stat().st_size} bytes)")
    else:
        print(f"LibreOffice conversion warning/error: {res.stderr or res.stdout}")

if __name__ == "__main__":
    generate_report()
