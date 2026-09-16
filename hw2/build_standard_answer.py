#!/usr/bin/env python3
"""Build 95-703 C HW#2 standard-answer PowerPoint from the Painter ERD template."""

from copy import deepcopy
from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt, Emu
from pptx.oxml import parse_xml
import shutil

BLACK = RGBColor(0x00, 0x00, 0x00)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Times New Roman"

TEMPLATE = "/home/ubuntu/.cursor/projects/workspace/uploads/Template_ERD_-_Painter_Model__1__573e.pptx"
OUT_PPTX = "/workspace/hw2/HW2_Standard_Answer.pptx"
OUT_ROOT = "/workspace/HW2_Standard_Answer.pptx"


def set_run_font(run, size=12, bold=False, underline=False, italic=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.underline = underline
    run.font.color.rgb = BLACK
    rPr = run._r.get_or_add_rPr()
    for tag in ("latin", "ea", "cs"):
        el = rPr.find(qn(f"a:{tag}"))
        if el is None:
            el = etree.SubElement(rPr, qn(f"a:{tag}"))
        el.set("typeface", FONT)


def _tf_setup(shape, anchor="ctr", wrap=True, l=0.04, t=0.02, r=0.04, b=0.02):
    tf = shape.text_frame
    tf.word_wrap = wrap
    tf.auto_size = None
    tf.margin_left = Inches(l)
    tf.margin_right = Inches(r)
    tf.margin_top = Inches(t)
    tf.margin_bottom = Inches(b)
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    if bodyPr is not None:
        bodyPr.set("anchor", anchor)
    return tf


def _fill_line(shape, fill=WHITE, line=BLACK, line_pt=1.0):
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line
    shape.line.width = Pt(line_pt)


def add_textbox(slide, x, y, w, h, text, size=16, bold=False, align=PP_ALIGN.LEFT, italic=False):
    sp = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = _tf_setup(sp, anchor="t", wrap=True)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    set_run_font(run, size=size, bold=bold, italic=italic)
    return sp


def add_rect(slide, x, y, w, h, lines, size=14, bold=False, line_pt=1.0):
    """Entity rectangle — same language as the Painter template."""
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    _fill_line(sp, line_pt=line_pt)
    tf = _tf_setup(sp, anchor="ctr", wrap=True, l=0.05, t=0.02, r=0.05, b=0.02)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        run = p.add_run()
        run.text = line
        set_run_font(run, size=size, bold=bold)
    return (x, y, w, h)


def add_diamond(slide, x, y, w, h, lines, size=13, line_pt=1.0):
    sp = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(x), Inches(y), Inches(w), Inches(h))
    _fill_line(sp, line_pt=line_pt)
    tf = _tf_setup(sp, anchor="ctr", wrap=False, l=0.14, r=0.14, t=0.02, b=0.02)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        run = p.add_run()
        run.text = line
        set_run_font(run, size=size, bold=False)
    return (x, y, w, h)


def add_oval(slide, x, y, w, h, text, size=14):
    sp = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(w), Inches(h))
    _fill_line(sp, line_pt=1.0)
    tf = _tf_setup(sp, anchor="ctr")
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    set_run_font(run, size=size, bold=False)
    return (x, y, w, h)


def add_card(slide, x, y, text, w=0.55, h=0.24, size=12):
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = WHITE
    sp.line.fill.background()
    tf = _tf_setup(sp, anchor="ctr", wrap=False, l=0.0, t=0.0, r=0.0, b=0.0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    set_run_font(run, size=size)
    return sp


def center(box):
    x, y, w, h = box
    return (x + w / 2.0, y + h / 2.0)


def add_line(slide, a, b, width=0.75):
    x1, y1 = a if len(a) == 2 else center(a)
    x2, y2 = b if len(b) == 2 else center(b)
    sp = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    sp.line.color.rgb = BLACK
    sp.line.width = Pt(width)
    return sp


def clear_slide(slide):
    spTree = slide.shapes._spTree
    for el in list(spTree):
        if el.tag.endswith("}nvGrpSpPr") or el.tag.endswith("}grpSpPr"):
            continue
        spTree.remove(el)


def delete_slide(prs, index):
    rId = prs.slides._sldIdLst[index].get(qn("r:id"))
    prs.part.drop_rel(rId)
    sldId = prs.slides._sldIdLst[index]
    prs.slides._sldIdLst.remove(sldId)


def add_blank_slide(prs):
    # Painter template: layout 6 = Blank
    return prs.slides.add_slide(prs.slide_layouts[6])


def build_er(slide):
    add_textbox(
        slide, 0.30, 0.12, 12.7, 0.36,
        "95–703 C  Homework #2   —   Standard Answer:  ER Diagram  (no attributes)",
        size=18, bold=False,
    )

    E = {
        "SUPPLIER":     (0.20, 2.10, 1.42, 0.38),
        "PROCUREMENT":  (1.80, 2.06, 1.62, 0.46),
        "ITEM":         (3.62, 2.10, 1.30, 0.38),
        "PASM":         (3.45, 2.92, 1.64, 0.50),
        "PRODUCT":      (3.50, 3.86, 1.52, 0.38),
        "INCLUDE":      (3.36, 4.58, 1.82, 0.64),
        "PLINE":        (3.42, 5.48, 1.70, 0.38),
        "CUSTOMER":     (7.55, 0.92, 1.52, 0.38),
        "SUBMIT":       (7.42, 1.40, 1.78, 0.60),
        "ORDER":        (7.55, 2.10, 1.52, 0.38),
        "PROCESS":      (9.28, 1.97, 1.90, 0.64),
        "SREP":         (11.38, 2.10, 1.58, 0.38),
        "OLINE":        (5.72, 2.58, 1.58, 0.44),
        "PRODUCE":      (5.48, 3.73, 1.82, 0.64),
        "WC":           (7.48, 3.86, 1.70, 0.38),
        "ASSIGN":       (9.38, 3.82, 1.58, 0.46),
        "EMP":          (11.15, 3.86, 1.42, 0.38),
        "MANAGE":       (7.48, 4.58, 1.70, 0.62),
        "MGR":          (7.58, 5.48, 1.50, 0.38),
        "ISA":          (12.68, 4.40, 0.46, 0.46),
        "ADMIN":        (10.72, 5.48, 1.92, 0.38),
    }

    pairs = [
        "SUPPLIER", "PROCUREMENT", "PROCUREMENT", "ITEM",
        "ITEM", "PASM", "PASM", "PRODUCT",
        "PRODUCT", "INCLUDE", "INCLUDE", "PLINE",
        "CUSTOMER", "SUBMIT", "SUBMIT", "ORDER",
        "ORDER", "PROCESS", "PROCESS", "SREP",
        "ORDER", "OLINE", "OLINE", "PRODUCT",
        "PRODUCT", "PRODUCE", "PRODUCE", "WC",
        "WC", "ASSIGN", "ASSIGN", "EMP",
        "WC", "MANAGE", "MANAGE", "MGR",
        "EMP", "ISA", "ISA", "SREP", "ISA", "MGR", "ISA", "ADMIN",
    ]
    for a, b in zip(pairs[0::2], pairs[1::2]):
        add_line(slide, E[a], E[b], width=0.75)

    # regular entities (1 pt, like Painter)
    add_rect(slide, *E["SUPPLIER"], ["SUPPLIER"], size=13)
    add_rect(slide, *E["ITEM"], ["ITEM"], size=13)
    add_rect(slide, *E["PRODUCT"], ["PRODUCT"], size=13)
    add_rect(slide, *E["PLINE"], ["PRODUCT_LINE"], size=13)
    add_rect(slide, *E["CUSTOMER"], ["CUSTOMER"], size=13)
    add_rect(slide, *E["ORDER"], ["ORDER"], size=13)
    add_rect(slide, *E["SREP"], ["SALES_REP"], size=13)
    add_rect(slide, *E["WC"], ["WORK_CENTER"], size=12)
    add_rect(slide, *E["EMP"], ["EMPLOYEE"], size=13)
    add_rect(slide, *E["MGR"], ["MANAGER"], size=13)
    add_rect(slide, *E["ADMIN"], ["ADMIN_ASSISTANT"], size=12)

    # composite entities (thicker border = M:N transformed)
    add_rect(slide, *E["PROCUREMENT"], ["PROCUREMENT"], size=12, line_pt=2.25)
    add_rect(slide, *E["PASM"], ["PRODUCT", "ASSEMBLY"], size=12, line_pt=2.25)
    add_rect(slide, *E["OLINE"], ["ORDER_LINE"], size=12, line_pt=2.25)
    add_rect(slide, *E["ASSIGN"], ["ASSIGNMENT"], size=12, line_pt=2.25)

    add_diamond(slide, *E["INCLUDE"], ["INCLUDE"], size=13)
    add_diamond(slide, *E["SUBMIT"], ["SUBMIT"], size=13)
    add_diamond(slide, *E["PROCESS"], ["PROCESS"], size=13)
    add_diamond(slide, *E["PRODUCE"], ["PRODUCE"], size=13)
    add_diamond(slide, *E["MANAGE"], ["MANAGE"], size=13)
    add_oval(slide, *E["ISA"], "O", size=14)

    # (min, max) look-across — Painter convention
    add_card(slide, 1.48, 1.84, "(1,1)")
    add_card(slide, 1.48, 2.52, "(0,N)")
    add_card(slide, 3.20, 1.84, "(0,N)")
    add_card(slide, 3.20, 2.52, "(1,1)")
    add_card(slide, 4.95, 2.10, "(1,1)")
    add_card(slide, 2.88, 2.95, "(1,N)")
    add_card(slide, 2.88, 3.40, "(1,N)")
    add_card(slide, 2.88, 3.86, "(1,1)")
    add_card(slide, 5.22, 4.72, "(1,N)")
    add_card(slide, 5.22, 5.48, "(1,1)")
    add_card(slide, 9.12, 0.94, "(1,1)")
    add_card(slide, 7.00, 2.12, "(0,N)")
    add_card(slide, 7.02, 2.48, "(1,1)")
    add_card(slide, 6.42, 3.02, "(1,N)")
    add_card(slide, 5.55, 2.38, "(0,N)")
    add_card(slide, 5.05, 3.50, "(1,1)")
    add_card(slide, 9.12, 1.78, "(0,N)")
    add_card(slide, 11.12, 1.78, "(1,1)")
    add_card(slide, 5.15, 4.22, "(0,N)")
    add_card(slide, 7.20, 3.55, "(1,1)")
    add_card(slide, 9.18, 3.55, "(1,1)")
    add_card(slide, 9.18, 4.28, "(5,N)")
    add_card(slide, 10.85, 4.28, "(1,N)")
    add_card(slide, 10.85, 3.55, "(1,1)")
    add_card(slide, 9.22, 4.70, "(1,1)")
    add_card(slide, 9.22, 5.48, "(1,1)")

    add_rect(slide, 0.22, 6.05, 0.40, 0.26, [""], size=8, line_pt=1.0)
    add_textbox(slide, 0.70, 6.05, 2.3, 0.26, "Entity", size=12)
    add_rect(slide, 0.22, 6.38, 0.40, 0.26, [""], size=8, line_pt=2.25)
    add_textbox(slide, 0.70, 6.38, 2.8, 0.26, "Composite entity (from M:N)", size=12)
    add_diamond(slide, 0.16, 6.68, 0.50, 0.34, [""], size=6)
    add_textbox(slide, 0.70, 6.72, 2.8, 0.26, "Relationship (1:1 or 1:N)", size=12)
    add_textbox(slide, 3.55, 6.72, 5.5, 0.26, "O  =  overlapping, partial specialization", size=12)


def add_schema_line(tf, first, rel, fields):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = PP_ALIGN.LEFT
    p.space_before = Pt(8)
    p.space_after = Pt(2)
    p.line_spacing = 1.15
    r = p.add_run()
    r.text = rel + ":  "
    set_run_font(r, size=16, bold=False)
    for i, (attr, is_pk, is_fk) in enumerate(fields):
        if i:
            sep = p.add_run()
            sep.text = ",  "
            set_run_font(sep, size=16)
        ar = p.add_run()
        ar.text = attr
        set_run_font(ar, size=16, underline=is_pk)
        if is_fk:
            at = p.add_run()
            at.text = "@"
            set_run_font(at, size=16, underline=is_pk)


def build_schema(slide):
    add_textbox(
        slide, 0.40, 0.12, 12.5, 0.36,
        "95–703 C  Homework #2   —   Standard Answer:  Relational Schema",
        size=18,
    )
    add_textbox(
        slide, 0.40, 0.50, 12.5, 0.32,
        "PK underlined.   FK marked with @.   Identifying FK that is also part of the PK is both underlined and tagged @.",
        size=13, italic=True,
    )

    left = [
        ("Supplier", [
            ("Supplier_ID", True, False),
            ("Supplier_Name", False, False),
            ("Supplier_Address", False, False),
            ("Supplier_Phone", False, False),
        ]),
        ("Procurement", [
            ("Item_ID", True, True),
            ("Procurement_Date", True, False),
            ("Supplier_ID", False, True),
            ("Quantity", False, False),
            ("Unit_Price", False, False),
        ]),
        ("Item", [
            ("Item_ID", True, False),
            ("Description", False, False),
            ("Average_Unit_Cost", False, False),
            ("Units_On_Hand", False, False),
            ("Reorder_Point", False, False),
        ]),
        ("Product_Assembly", [
            ("Product_ID", True, True),
            ("Item_ID", True, True),
            ("Quantity_Needed", False, False),
        ]),
        ("Product", [
            ("Product_ID", True, False),
            ("Product_Name", False, False),
            ("Product_Line_ID", False, True),
            ("Work_Center_ID", False, True),
        ]),
        ("Product_Line", [
            ("Product_Line_ID", True, False),
            ("Product_Line_Name", False, False),
        ]),
        ("Customer", [
            ("Customer_ID", True, False),
            ("Customer_Name", False, False),
            ("Customer_Email", False, False),
            ("Customer_Address", False, False),
            ("Customer_Phone", False, False),
        ]),
        ("Order", [
            ("Order_ID", True, False),
            ("Order_Date", False, False),
            ("Customer_ID", False, True),
            ("Sales_Rep_ID", False, True),
        ]),
    ]
    right = [
        ("Order_Line", [
            ("Order_ID", True, True),
            ("Product_ID", True, True),
            ("Quantity_Ordered", False, False),
            ("Unit_Price", False, False),
        ]),
        ("Work_Center", [
            ("Work_Center_ID", True, False),
            ("Work_Center_Name", False, False),
            ("Manager_ID", False, True),
        ]),
        ("Assignment", [
            ("Employee_ID", True, True),
            ("Work_Center_ID", True, True),
        ]),
        ("Employee", [
            ("Employee_ID", True, False),
            ("First_Name", False, False),
            ("Last_Name", False, False),
            ("Address", False, False),
            ("Salary", False, False),
            ("Title", False, False),
        ]),
        ("Manager", [
            ("Employee_ID", True, True),
            ("Driver_License", False, False),
            ("Budget_Amount", False, False),
        ]),
        ("Admin_Assistant", [
            ("Employee_ID", True, True),
            ("Accounting_Training", False, False),
            ("MS_Office_Level", False, False),
        ]),
        ("Sales_Rep", [
            ("Employee_ID", True, True),
            ("Sales_Area", False, False),
            ("Email", False, False),
        ]),
    ]

    sp = slide.shapes.add_textbox(Inches(0.40), Inches(0.90), Inches(6.2), Inches(5.55))
    tf = _tf_setup(sp, anchor="t", wrap=True, l=0.04, t=0.02, r=0.04, b=0.02)
    for i, (rel, fields) in enumerate(left):
        add_schema_line(tf, i == 0, rel, fields)

    sp2 = slide.shapes.add_textbox(Inches(6.70), Inches(0.90), Inches(6.2), Inches(5.55))
    tf2 = _tf_setup(sp2, anchor="t", wrap=True, l=0.04, t=0.02, r=0.04, b=0.02)
    for i, (rel, fields) in enumerate(right):
        add_schema_line(tf2, i == 0, rel, fields)

    add_textbox(
        slide, 0.40, 6.55, 12.5, 0.55,
        "Notes:  Work_Center.Manager_ID@ is unique (1:1 with Manager).  "
        "Customer_Email may be null for potential customers.  "
        "Procurement PK = (Item_ID, Procurement_Date) so that at a given date an item has only one supplier.  "
        "Assignment: employee (1,N), work center (5,N).",
        size=12, italic=True,
    )


def main():
    shutil.copy(TEMPLATE, OUT_PPTX)
    prs = Presentation(OUT_PPTX)

    # Slide 1 of the template is the Painter ERD — replace with HW2 ER
    s1 = prs.slides[0]
    clear_slide(s1)
    build_er(s1)

    s2 = add_blank_slide(prs)
    build_schema(s2)

    # core props
    prs.core_properties.title = "95-703 C Homework #2 Standard Answer"
    prs.core_properties.subject = "ER diagram and relational schema"
    prs.core_properties.author = "TA Standard Answer"

    prs.save(OUT_PPTX)
    shutil.copy(OUT_PPTX, OUT_ROOT)
    print("wrote", OUT_PPTX)
    print("wrote", OUT_ROOT)


if __name__ == "__main__":
    main()
