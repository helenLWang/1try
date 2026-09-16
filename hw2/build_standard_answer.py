#!/usr/bin/env python3
"""Build 95-703 C Homework #2 standard-answer PowerPoint (TA key)."""

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt
from lxml import etree
from copy import deepcopy

BLACK = RGBColor(0x00, 0x00, 0x00)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NAVY = RGBColor(0x1A, 0x1A, 0x2E)
GRAY = RGBColor(0x33, 0x33, 0x33)
LIGHT = RGBColor(0xF7, 0xF7, 0xF7)
RULE = RGBColor(0x22, 0x22, 0x22)

FONT = "Times New Roman"
SLIDE_W = Inches(13.333333)
SLIDE_H = Inches(7.5)


def set_run_font(run, size=12, bold=False, color=BLACK, underline=False, italic=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.underline = underline
    run.font.color.rgb = color
    # Force latin/ea/cs typeface (LibreOffice + PowerPoint)
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


def _fill_line(shape, fill=WHITE, line=BLACK, line_pt=1.25):
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line
    shape.line.width = Pt(line_pt)


def add_textbox(slide, x, y, w, h, text, size=14, bold=False, color=BLACK, align=PP_ALIGN.LEFT, anchor="t", italic=False):
    sp = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = _tf_setup(sp, anchor=anchor, wrap=True)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    set_run_font(run, size=size, bold=bold, color=color, italic=italic)
    return sp


def add_rect(slide, x, y, w, h, lines, size=11, bold=True, line_pt=1.5, fill=WHITE):
    sp = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    _fill_line(sp, fill=fill, line=BLACK, line_pt=line_pt)
    tf = _tf_setup(sp, anchor="ctr")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        run = p.add_run()
        run.text = line
        set_run_font(run, size=size, bold=bold)
    return sp, (x, y, w, h)


def add_diamond(slide, x, y, w, h, lines, size=11, line_pt=1.25):
    sp = slide.shapes.add_shape(
        MSO_SHAPE.DIAMOND, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    _fill_line(sp, fill=WHITE, line=BLACK, line_pt=line_pt)
    tf = _tf_setup(sp, anchor="ctr", wrap=False, l=0.12, r=0.12, t=0.02, b=0.02)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        run = p.add_run()
        run.text = line
        set_run_font(run, size=size, bold=False)
    return sp, (x, y, w, h)


def add_oval(slide, x, y, w, h, text, size=12, bold=True, line_pt=1.5):
    sp = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    _fill_line(sp, fill=WHITE, line=BLACK, line_pt=line_pt)
    tf = _tf_setup(sp, anchor="ctr")
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    set_run_font(run, size=size, bold=bold)
    return sp, (x, y, w, h)


def add_card(slide, x, y, text, w=0.52, h=0.22, size=10):
    """Cardinality label (min, max) — white fill so it sits on connectors."""
    sp = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    _fill_line(sp, fill=WHITE, line=WHITE, line_pt=0)
    sp.line.fill.background()
    tf = _tf_setup(sp, anchor="ctr", l=0.0, r=0.0, t=0.0, b=0.0, wrap=False)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    set_run_font(run, size=size, bold=False)
    return sp


def center(box):
    x, y, w, h = box
    return (x + w / 2.0, y + h / 2.0)


def add_line(slide, a, b, width=1.0):
    x1, y1 = a if len(a) == 2 else center(a)
    x2, y2 = b if len(b) == 2 else center(b)
    sp = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Inches(x1),
        Inches(y1),
        Inches(x2),
        Inches(y2),
    )
    sp.line.color.rgb = BLACK
    sp.line.width = Pt(width)
    return sp


def header_bar(slide, title):
    # top rule
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), SLIDE_W, Inches(0.08)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    add_textbox(
        slide, 0.35, 0.14, 10.2, 0.32,
        "95–703 C: Database Management   ·   Homework #2   ·   Fall 2026",
        size=11, bold=False, color=GRAY,
    )
    add_textbox(
        slide, 0.35, 0.38, 12.6, 0.36,
        title, size=20, bold=True, color=NAVY,
    )
    rule = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.35), Inches(0.78), Inches(12.63), Inches(0.015)
    )
    rule.fill.solid()
    rule.fill.fore_color.rgb = RULE
    rule.line.fill.background()


def footer(slide, page, total=4):
    add_textbox(
        slide, 0.35, 7.18, 9.5, 0.25,
        "Standard solution  ·  ER: Chen notation with (min, max) look-across  ·  No attributes on ER",
        size=9, color=GRAY,
    )
    add_textbox(
        slide, 11.6, 7.18, 1.4, 0.25,
        f"{page} / {total}",
        size=9, color=GRAY, align=PP_ALIGN.RIGHT,
    )


def build_title(prs, blank):
    slide = prs.slides.add_slide(blank)
    # background white already
    band = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.18), SLIDE_H
    )
    band.fill.solid()
    band.fill.fore_color.rgb = NAVY
    band.line.fill.background()

    add_textbox(slide, 0.85, 1.55, 11.5, 0.35,
                "Carnegie Mellon University  ·  Heinz College",
                size=14, color=GRAY)
    add_textbox(slide, 0.85, 2.05, 11.5, 0.55,
                "95–703 C: Database Management",
                size=28, bold=True, color=NAVY)
    add_textbox(slide, 0.85, 2.65, 11.5, 0.50,
                "Homework #2  —  Standard Solution (TA Answer Key)",
                size=22, bold=True, color=BLACK)
    add_textbox(slide, 0.85, 3.25, 11.5, 0.35,
                "Fall 2026",
                size=16, color=GRAY)

    rule = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.85), Inches(3.75), Inches(6.2), Inches(0.02)
    )
    rule.fill.solid()
    rule.fill.fore_color.rgb = NAVY
    rule.line.fill.background()

    bullets = [
        "1.  Conceptual model: ER diagram without attributes",
        "2.  Many-to-many relationships transformed into composite entities",
        "3.  Logical model: relational schema  (PK underlined, FK marked with @)",
    ]
    y = 4.05
    for b in bullets:
        add_textbox(slide, 0.85, y, 11.2, 0.38, b, size=16, color=BLACK)
        y += 0.42

    add_textbox(slide, 0.85, 6.55, 11.2, 0.40,
                "Use this deck as the in-class key.  Cardinality uses (min, max) look-across, matching the Painter-model template.",
                size=12, italic=True, color=GRAY)
    return slide


def build_er(prs, blank):
    slide = prs.slides.add_slide(blank)
    header_bar(slide, "1.  ER Diagram  (no attributes; M:N → composite entities)")

    # Boxes: (x, y, w, h) in inches.  Lines are drawn first; white fills cover them.
    E = {
        # procurement row
        "SUPPLIER":     (0.20, 2.10, 1.42, 0.36),
        "PROCUREMENT":  (1.80, 2.06, 1.62, 0.44),
        "ITEM":         (3.62, 2.10, 1.30, 0.36),
        # product stack
        "PASM":         (3.45, 2.92, 1.64, 0.50),
        "PRODUCT":      (3.50, 3.86, 1.52, 0.36),
        "INCLUDE":      (3.36, 4.58, 1.82, 0.64),
        "PLINE":        (3.42, 5.48, 1.70, 0.36),
        # order flow
        "CUSTOMER":     (7.55, 0.92, 1.52, 0.36),
        "SUBMIT":       (7.42, 1.40, 1.78, 0.60),
        "ORDER":        (7.55, 2.10, 1.52, 0.36),
        "PROCESS":      (9.28, 1.97, 1.90, 0.64),
        "SREP":         (11.38, 2.10, 1.58, 0.36),
        "OLINE":        (5.72, 2.58, 1.58, 0.42),
        # production / staffing
        "PRODUCE":      (5.48, 3.73, 1.82, 0.64),
        "WC":           (7.48, 3.86, 1.70, 0.36),
        "ASSIGN":       (9.38, 3.82, 1.58, 0.44),
        "EMP":          (11.15, 3.86, 1.42, 0.36),
        "MANAGE":       (7.48, 4.58, 1.70, 0.62),
        "MGR":          (7.58, 5.48, 1.50, 0.36),
        "ISA":          (12.68, 4.40, 0.46, 0.46),
        "ADMIN":        (10.72, 5.48, 1.92, 0.36),
    }

    pairs = [
        "SUPPLIER", "PROCUREMENT",
        "PROCUREMENT", "ITEM",
        "ITEM", "PASM",
        "PASM", "PRODUCT",
        "PRODUCT", "INCLUDE",
        "INCLUDE", "PLINE",
        "CUSTOMER", "SUBMIT",
        "SUBMIT", "ORDER",
        "ORDER", "PROCESS",
        "PROCESS", "SREP",
        "ORDER", "OLINE",
        "OLINE", "PRODUCT",
        "PRODUCT", "PRODUCE",
        "PRODUCE", "WC",
        "WC", "ASSIGN",
        "ASSIGN", "EMP",
        "WC", "MANAGE",
        "MANAGE", "MGR",
        "EMP", "ISA",
        "ISA", "SREP",
        "ISA", "MGR",
        "ISA", "ADMIN",
    ]
    for a, b in zip(pairs[0::2], pairs[1::2]):
        add_line(slide, E[a], E[b], width=1.15)

    add_rect(slide, *E["SUPPLIER"], ["SUPPLIER"], size=11)
    add_rect(slide, *E["PROCUREMENT"], ["PROCUREMENT"], size=10, line_pt=2.5)
    add_rect(slide, *E["ITEM"], ["ITEM"], size=11)
    add_rect(slide, *E["PASM"], ["PRODUCT", "ASSEMBLY"], size=10, line_pt=2.5)
    add_rect(slide, *E["PRODUCT"], ["PRODUCT"], size=11)
    add_diamond(slide, *E["INCLUDE"], ["INCLUDE"], size=11)
    add_rect(slide, *E["PLINE"], ["PRODUCT_LINE"], size=11)

    add_rect(slide, *E["CUSTOMER"], ["CUSTOMER"], size=11)
    add_diamond(slide, *E["SUBMIT"], ["SUBMIT"], size=11)
    add_rect(slide, *E["ORDER"], ["ORDER"], size=11)
    add_diamond(slide, *E["PROCESS"], ["PROCESS"], size=11)
    add_rect(slide, *E["SREP"], ["SALES_REP"], size=11)
    add_rect(slide, *E["OLINE"], ["ORDER_LINE"], size=10, line_pt=2.5)

    add_diamond(slide, *E["PRODUCE"], ["PRODUCE"], size=11)
    add_rect(slide, *E["WC"], ["WORK_CENTER"], size=10)
    add_rect(slide, *E["ASSIGN"], ["ASSIGNMENT"], size=10, line_pt=2.5)
    add_rect(slide, *E["EMP"], ["EMPLOYEE"], size=11)

    add_diamond(slide, *E["MANAGE"], ["MANAGE"], size=11)
    add_rect(slide, *E["MGR"], ["MANAGER"], size=11)
    add_oval(slide, *E["ISA"], "O", size=14, bold=True)
    add_rect(slide, *E["ADMIN"], ["ADMIN_ASSISTANT"], size=10)

    # (min, max) look-across, same convention as the Painter-model template
    # SUPPLIER (1,1) -- (0,N) PROCUREMENT (0,N) -- (1,1) ITEM
    add_card(slide, 1.48, 1.84, "(1,1)")
    add_card(slide, 1.48, 2.50, "(0,N)")
    add_card(slide, 3.20, 1.84, "(0,N)")
    add_card(slide, 3.20, 2.50, "(1,1)")

    # ITEM (1,1) -- (1,N) PRODUCT_ASSEMBLY (1,N) -- (1,1) PRODUCT
    # keep these on the LEFT of the stack so they do not collide with PRODUCE
    add_card(slide, 4.95, 2.10, "(1,1)")
    add_card(slide, 2.88, 2.95, "(1,N)")
    add_card(slide, 2.88, 3.40, "(1,N)")
    add_card(slide, 2.88, 3.86, "(1,1)")

    # PRODUCT (1,N) INCLUDE (1,1) PRODUCT_LINE
    add_card(slide, 5.22, 4.72, "(1,N)")
    add_card(slide, 5.22, 5.48, "(1,1)")

    # CUSTOMER (1,1) SUBMIT (0,N) ORDER   — (0,N) sits LEFT of ORDER
    add_card(slide, 9.12, 0.94, "(1,1)")
    add_card(slide, 7.00, 2.12, "(0,N)")

    # ORDER (1,1) -- (1,N) ORDER_LINE (0,N) -- (1,1) PRODUCT
    add_card(slide, 7.02, 2.48, "(1,1)")
    add_card(slide, 6.42, 3.02, "(1,N)")
    add_card(slide, 5.55, 2.38, "(0,N)")
    add_card(slide, 5.05, 3.50, "(1,1)")

    # ORDER (0,N) PROCESS (1,1) SALES_REP
    add_card(slide, 9.12, 1.78, "(0,N)")
    add_card(slide, 11.12, 1.78, "(1,1)")

    # PRODUCT (0,N) PRODUCE (1,1) WORK_CENTER
    add_card(slide, 5.15, 4.22, "(0,N)")
    add_card(slide, 7.20, 3.55, "(1,1)")

    # WC (1,1) -- (5,N) ASSIGNMENT (1,N) -- (1,1) EMPLOYEE
    add_card(slide, 9.18, 3.55, "(1,1)")
    add_card(slide, 9.18, 4.28, "(5,N)")
    add_card(slide, 10.85, 4.28, "(1,N)")
    add_card(slide, 10.85, 3.55, "(1,1)")

    # WC (1,1) MANAGE (1,1) MANAGER
    add_card(slide, 9.22, 4.70, "(1,1)")
    add_card(slide, 9.22, 5.48, "(1,1)")

    # compact legend — bottom left, clear of the model
    add_rect(slide, 0.22, 6.00, 0.38, 0.24, [""], size=8, line_pt=1.5)
    add_textbox(slide, 0.66, 6.00, 2.4, 0.24, "Entity", size=11)
    add_rect(slide, 0.22, 6.30, 0.38, 0.24, [""], size=8, line_pt=2.5)
    add_textbox(slide, 0.66, 6.30, 2.7, 0.24, "Composite entity (from M:N)", size=11)
    add_diamond(slide, 0.18, 6.56, 0.46, 0.32, [""], size=6)
    add_textbox(slide, 0.66, 6.60, 2.6, 0.24, "Relationship (1:1 or 1:N)", size=11)
    add_textbox(slide, 3.40, 6.60, 4.4, 0.24, "O  =  overlapping, partial specialization", size=11)

    footer(slide, 2)
    return slide


def add_schema_block(slide, x, y, w, h, items):
    """items: list of (rel_name, [(attr, is_pk, is_fk), ...])"""
    sp = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = _tf_setup(sp, anchor="t", wrap=True, l=0.06, t=0.04, r=0.06, b=0.04)
    first = True
    for rel_name, fields in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = PP_ALIGN.LEFT
        p.space_before = Pt(7)
        p.space_after = Pt(1)
        p.line_spacing = 1.08
        r = p.add_run()
        r.text = rel_name + ":  "
        set_run_font(r, size=14, bold=True)
        for i, (attr, is_pk, is_fk) in enumerate(fields):
            if i:
                sep = p.add_run()
                sep.text = ",  "
                set_run_font(sep, size=14)
            ar = p.add_run()
            ar.text = attr
            set_run_font(ar, size=14, underline=is_pk)
            if is_fk:
                at = p.add_run()
                at.text = "@"
                set_run_font(at, size=14, underline=is_pk)
    return sp


def build_schema(prs, blank):
    slide = prs.slides.add_slide(blank)
    header_bar(slide, "2.  Relational schema   (PK underlined;  FK marked with @)")

    add_textbox(
        slide, 0.35, 0.88, 12.6, 0.32,
        "Each relation maps one entity, composite entity, or subclass.  Identifying FKs that are also part of the PK are both underlined and tagged @.",
        size=12, color=GRAY,
    )

    left = [
        ("SUPPLIER", [
            ("Supplier_ID", True, False),
            ("Supplier_Name", False, False),
            ("Supplier_Address", False, False),
            ("Supplier_Phone", False, False),
        ]),
        ("PROCUREMENT", [
            ("Item_ID", True, True),
            ("Procurement_Date", True, False),
            ("Supplier_ID", False, True),
            ("Quantity", False, False),
            ("Unit_Price", False, False),
        ]),
        ("ITEM", [
            ("Item_ID", True, False),
            ("Description", False, False),
            ("Average_Unit_Cost", False, False),
            ("Units_On_Hand", False, False),
            ("Reorder_Point", False, False),
        ]),
        ("PRODUCT_ASSEMBLY", [
            ("Product_ID", True, True),
            ("Item_ID", True, True),
            ("Quantity_Needed", False, False),
        ]),
        ("PRODUCT", [
            ("Product_ID", True, False),
            ("Product_Name", False, False),
            ("Product_Line_ID", False, True),
            ("Work_Center_ID", False, True),
        ]),
        ("PRODUCT_LINE", [
            ("Product_Line_ID", True, False),
            ("Product_Line_Name", False, False),
        ]),
        ("CUSTOMER", [
            ("Customer_ID", True, False),
            ("Customer_Name", False, False),
            ("Customer_Email", False, False),
            ("Customer_Address", False, False),
            ("Customer_Phone", False, False),
        ]),
        ("ORDER", [
            ("Order_ID", True, False),
            ("Order_Date", False, False),
            ("Customer_ID", False, True),
            ("Sales_Rep_ID", False, True),
        ]),
    ]
    right = [
        ("ORDER_LINE", [
            ("Order_ID", True, True),
            ("Product_ID", True, True),
            ("Quantity_Ordered", False, False),
            ("Unit_Price", False, False),
        ]),
        ("WORK_CENTER", [
            ("Work_Center_ID", True, False),
            ("Work_Center_Name", False, False),
            ("Manager_ID", False, True),
        ]),
        ("ASSIGNMENT", [
            ("Employee_ID", True, True),
            ("Work_Center_ID", True, True),
        ]),
        ("EMPLOYEE", [
            ("Employee_ID", True, False),
            ("First_Name", False, False),
            ("Last_Name", False, False),
            ("Address", False, False),
            ("Salary", False, False),
            ("Title", False, False),
        ]),
        ("MANAGER", [
            ("Employee_ID", True, True),
            ("Driver_License", False, False),
            ("Budget_Amount", False, False),
        ]),
        ("ADMIN_ASSISTANT", [
            ("Employee_ID", True, True),
            ("Accounting_Training", False, False),
            ("MS_Office_Level", False, False),
        ]),
        ("SALES_REP", [
            ("Employee_ID", True, True),
            ("Sales_Area", False, False),
            ("Email", False, False),
        ]),
    ]

    # two panel backgrounds
    for x in (0.32, 6.85):
        bg = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(1.22), Inches(6.15), Inches(5.22)
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = LIGHT
        bg.line.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
        bg.line.width = Pt(0.75)
        # radius
        try:
            bg.adjustments[0] = 0.04
        except Exception:
            pass

    add_schema_block(slide, 0.42, 1.28, 5.95, 5.30, left)
    add_schema_block(slide, 6.95, 1.28, 5.95, 5.30, right)

    add_textbox(
        slide, 0.42, 6.55, 12.4, 0.42,
        "Notes:  WORK_CENTER.Manager_ID@ is unique (1:1 with MANAGER).  "
        "CUSTOMER.Customer_Email may be null until the first order.  "
        "(5,N) on ASSIGNMENT is an ER constraint — not encoded by the relation keys alone.",
        size=11, color=GRAY,
    )

    footer(slide, 3)
    return slide


def add_bullets(slide, x, y, w, h, items, size=13, title=None):
    sp = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = _tf_setup(sp, anchor="t", wrap=True, l=0.08, t=0.04, r=0.08, b=0.04)
    p = tf.paragraphs[0]
    if title:
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = title
        set_run_font(r, size=14, bold=True, color=NAVY)
        start = items
        first_item = True
    else:
        start = items[1:]
        r = p.add_run()
        r.text = items[0]
        set_run_font(r, size=size)
        first_item = False
        p.space_after = Pt(4)

    seq = items if title else items[1:]
    for t in seq:
        bp = tf.add_paragraph() if (title or True) else tf.add_paragraph()
        bp.alignment = PP_ALIGN.LEFT
        bp.level = 0
        bp.space_before = Pt(3)
        bp.space_after = Pt(2)
        run = bp.add_run()
        run.text = t
        set_run_font(run, size=size)
    return sp


def build_notes(prs, blank):
    slide = prs.slides.add_slide(blank)
    header_bar(slide, "3.  Mapping decisions  ·  what to accept  ·  common errors")

    # four cards
    cards = [
        (0.32, 0.95, "Composite entities (only M:N)", [
            "PROCUREMENT  —  SUPPLIER ↔ ITEM",
            "PRODUCT_ASSEMBLY  —  ITEM ↔ PRODUCT",
            "ORDER_LINE  —  ORDER ↔ PRODUCT",
            "ASSIGNMENT  —  EMPLOYEE ↔ WORK_CENTER",
            "1:1 and 1:N stay diamonds; FK goes into the N-side (or either side of 1:1).",
        ]),
        (6.85, 0.95, "Required cardinalities", [
            "Supplier may supply 0..N items over time; an item at a given date has 1 supplier.",
            "Item (1,N) products; product (1,N) items; store Quantity_Needed.",
            "Customer (0,N) orders (potential customers); each order (1,1) customer.",
            "Order (1,N) products; product (0,N) orders; store qty + unit price on ORDER_LINE.",
            "Work center (0,N) products; each product (1,1) work center.",
            "Employee (1,N) centers; work center (5,N) employees.",
            "Each work center (1,1) manager; each manager (1,1) work center.",
        ]),
        (0.32, 4.05, "Schema details worth full credit", [
            "PROCUREMENT PK = (Item_ID, Procurement_Date); Supplier_ID@ is NOT in the PK — this enforces “at that time, one supplier”.",
            "ORDER.Customer_ID@ and ORDER.Sales_Rep_ID@ both mandatory (every order has one customer and one sales rep).",
            "WORK_CENTER.Manager_ID@ references MANAGER and is unique (1:1).",
            "Subclasses: MANAGER / SALES_REP / ADMIN_ASSISTANT with Employee_ID@ as PK/FK (overlapping, partial ISA).",
            "Customer_Email lives on CUSTOMER (nullable for potential customers).  Sales-rep Email is a subclass attribute.",
        ]),
        (6.85, 4.05, "Do not award full credit if …", [
            "ASSIGNMENT shows employee participation (0,N) — the spec says every employee is assigned to ≥ 1 center.",
            "M:N left as a single relationship (no composite entity / no associative table).",
            "PROCESS attached to EMPLOYEE rather than SALES_REP (“only sales reps can process orders”).",
            "Procurement PK = (Supplier_ID, Item_ID, Date) — allows two suppliers for the same item on the same date.",
            "Specialization drawn as total (every employee is a manager/rep/assistant) — it is partial.",
            "Attribute ovals on the ER — the assignment asks for ER without attributes.",
        ]),
    ]

    for x, y, title, bullets in cards:
        bg = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(6.15), Inches(2.95)
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = LIGHT
        bg.line.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
        bg.line.width = Pt(0.75)
        try:
            bg.adjustments[0] = 0.04
        except Exception:
            pass
        add_textbox(slide, x + 0.14, y + 0.08, 5.85, 0.30, title, size=14, bold=True, color=NAVY)
        sp = slide.shapes.add_textbox(Inches(x + 0.10), Inches(y + 0.38), Inches(5.92), Inches(2.50))
        tf = _tf_setup(sp, anchor="t", wrap=True, l=0.06, t=0.0, r=0.06, b=0.04)
        for i, t in enumerate(bullets):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.LEFT
            p.space_before = Pt(2)
            p.space_after = Pt(1)
            p.level = 0
            run = p.add_run()
            run.text = "•  " + t
            set_run_font(run, size=11)

    footer(slide, 4)
    return slide


def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    build_title(prs, blank)
    build_er(prs, blank)
    build_schema(prs, blank)
    build_notes(prs, blank)

    out = "/workspace/hw2/DBM-C_HW2_F2026_Standard_Answer.pptx"
    prs.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
