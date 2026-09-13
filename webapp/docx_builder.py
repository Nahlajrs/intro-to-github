"""توليد ملف Word (بطاقة الوصف الوظيفي) — القسم 12 من المواصفة."""
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HEADER_GREEN = "286140"
BORDER_GRAY = "C7C8CA"
FONT_NAME = "Arial"


def _set_rtl(paragraph):
    pf = paragraph.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pPr = paragraph._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi")
    pPr.append(bidi)


def _set_run_arabic(run, bold=False, color=None, size=11):
    run.font.name = FONT_NAME
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:cs"), FONT_NAME)


def _set_table_rtl(table):
    """يجعل جدول Word يُعرض من اليمين إلى اليسار (ترتيب الأعمدة والحدود مطابق للعربية)."""
    tblPr = table._tbl.tblPr
    bidi = OxmlElement("w:bidiVisual")
    tblPr.append(bidi)


def _set_column_widths(table, widths_cm):
    table.autofit = False
    for row in table.rows:
        for cell, width in zip(row.cells, widths_cm):
            cell.width = Cm(width)


def _shade_cell(cell, hex_color: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _cell_text(cell, text, bold=False, color=None, size=11, header=False):
    cell.text = ""
    p = cell.paragraphs[0]
    _set_rtl(p)
    if header:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    _set_run_arabic(run, bold=bold, color=color, size=size)


def _add_heading(doc, text, number):
    p = doc.add_paragraph()
    _set_rtl(p)
    run = p.add_run(f"{number}- {text}")
    _set_run_arabic(run, bold=True, color=HEADER_GREEN, size=14)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)


def _section_table_row(table, label, value):
    row = table.add_row()
    _cell_text(row.cells[0], label, bold=True, color="FFFFFF", header=True)
    _shade_cell(row.cells[0], HEADER_GREEN)
    _cell_text(row.cells[1], value or "")


def _duties_table(doc, rows):
    """جدول بعمودين: رأس أخضر للفئة، ثم قائمة نقطية بالبنود."""
    for category, duties in rows:
        table = doc.add_table(rows=0, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_rtl(table)
        header_row = table.add_row()
        _cell_text(header_row.cells[0], category, bold=True, color="FFFFFF", header=True)
        _shade_cell(header_row.cells[0], HEADER_GREEN)

        body_row = table.add_row()
        body_cell = body_row.cells[0]
        body_cell.text = ""
        for i, duty in enumerate(duties):
            p = body_cell.paragraphs[0] if i == 0 else body_cell.add_paragraph()
            _set_rtl(p)
            run = p.add_run(f"• {duty}")
            _set_run_arabic(run)
        doc.add_paragraph()


def build_document(content: dict) -> Document:
    doc = Document()

    section = doc.sections[0]
    sectPr = section._sectPr
    bidi_section = OxmlElement("w:bidi")
    sectPr.append(bidi_section)

    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = Pt(11)

    title_p = doc.add_paragraph()
    _set_rtl(title_p)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("بطاقة الوصف الوظيفي")
    _set_run_arabic(title_run, bold=True, color=HEADER_GREEN, size=18)

    # القسم 1 — المعلومات الأساسية
    _add_heading(doc, "المعلومات الأساسية", 1)
    basic_info = content["basic_info"]
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_rtl(table)
    _section_table_row(table, "المسمى الوظيفي", content["job_title"])
    _section_table_row(table, "رمز الوظيفة", basic_info.get("job_code", ""))
    _section_table_row(table, "المسؤول المباشر", basic_info.get("direct_manager", ""))
    _section_table_row(table, "القطاع", basic_info.get("sector", ""))
    _section_table_row(table, "الإدارة", basic_info.get("department", ""))
    _section_table_row(table, "القسم", basic_info.get("section", ""))
    _set_column_widths(table, [5, 11])

    # القسم 2 — الهدف العام للوظيفة
    _add_heading(doc, "الهدف العام للوظيفة", 2)
    purpose_p = doc.add_paragraph()
    _set_rtl(purpose_p)
    _set_run_arabic(purpose_p.add_run(content["job_purpose"]))

    # القسم 3 — المهام والمسؤوليات الوظيفية الأساسية (نص ثابت)
    _add_heading(doc, "المهام والمسؤوليات الوظيفية الأساسية", 3)
    core_rows = [(c["category"], c["duties"]) for c in content["core_responsibilities"]]
    _duties_table(doc, core_rows)

    # القسم 4 — المهام والمسؤوليات الوظيفية المتخصصة
    _add_heading(doc, "المهام والمسؤوليات الوظيفية المتخصصة", 4)
    specialized_rows = [(c["category"], c["duties"]) for c in content["specialized_responsibilities"]]
    _duties_table(doc, specialized_rows)

    # القسم 5 — الحد الأدنى للمؤهلات العلمية وسنوات الخبرة
    _add_heading(doc, "الحد الأدنى للمؤهلات العلمية وسنوات الخبرة", 5)
    q = content["qualifications"]
    qual_table = doc.add_table(rows=0, cols=2)
    qual_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_rtl(qual_table)
    _section_table_row(qual_table, "المؤهل العلمي المطلوب", q.get("education_required", ""))
    if q.get("education_preferred"):
        _section_table_row(qual_table, "المؤهل العلمي المفضل", q.get("education_preferred", ""))
    _section_table_row(qual_table, "سنوات الخبرة العامة", q.get("experience_years", ""))
    if q.get("supervisory_years"):
        _section_table_row(qual_table, "سنوات الخبرة الإشرافية", q.get("supervisory_years", ""))
    _section_table_row(qual_table, "اللغة العربية", q.get("language_arabic", ""))
    _section_table_row(qual_table, "اللغة الإنجليزية", q.get("language_english", ""))
    _set_column_widths(qual_table, [5, 11])

    return doc


def save_document(content: dict, output_path: str):
    doc = build_document(content)
    doc.save(output_path)
    return output_path
