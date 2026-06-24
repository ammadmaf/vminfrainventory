"""Generate commercial sales collateral for Virtualization Administration Toolkit."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT_DIR / "assets" / "preview"
PDF_PATH = ROOT_DIR / "ReadMe.pdf"

NAVY = "#173B5F"
BLUE = "#2F75B5"
LIGHT_BLUE = "#D9EAF7"
CANVAS = "#F3F6FA"
GREEN = "#70AD47"
AMBER = "#FFC000"
RED = "#C00000"
DARK = "#172B4D"
MUTED = "#5E6C84"
WHITE = "#FFFFFF"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a Windows UI font with a safe PIL fallback."""
    font_names = ["arialbd.ttf" if bold else "arial.ttf", "calibri.ttf"]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_card(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    value: str,
    accent: str,
) -> None:
    """Draw a rounded KPI preview card."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle((x1 + 5, y1 + 6, x2 + 5, y2 + 6), 18, fill="#DDE5EF")
    draw.rounded_rectangle(xy, 18, fill=WHITE, outline="#D6DEE8", width=2)
    draw.rounded_rectangle((x1, y1, x1 + 10, y2), 8, fill=accent)
    draw.text((x1 + 26, y1 + 18), title, fill=MUTED, font=load_font(22, True))
    draw.text((x1 + 26, y1 + 54), value, fill=accent, font=load_font(46, True))


def draw_table_preview(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    headers: list[str],
    rows: list[list[str]],
) -> None:
    """Draw a clean workbook table mockup."""
    x1, y1, x2, _ = xy
    col_width = (x2 - x1) // len(headers)
    row_height = 44
    header_font = load_font(17, True)
    body_font = load_font(15)

    for col, header in enumerate(headers):
        cx1 = x1 + col * col_width
        draw.rectangle((cx1, y1, cx1 + col_width, y1 + row_height), fill=NAVY)
        draw.text((cx1 + 10, y1 + 12), header, fill=WHITE, font=header_font)

    for row_index, row in enumerate(rows, start=1):
        y = y1 + row_index * row_height
        fill = WHITE if row_index % 2 else "#EEF4FA"
        for col, value in enumerate(row):
            cx1 = x1 + col * col_width
            draw.rectangle(
                (cx1, y, cx1 + col_width, y + row_height),
                fill=fill,
                outline="#D6DEE8",
            )
            draw.text((cx1 + 10, y + 12), value, fill=DARK, font=body_font)


def create_cover_preview() -> None:
    """Create the cover page sales preview image."""
    img = Image.new("RGB", (1600, 900), NAVY)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 1600, 900), fill=NAVY)
    draw.rectangle((0, 0, 130, 900), fill=LIGHT_BLUE)
    draw.rounded_rectangle((220, 180, 1380, 700), 30, fill="#244D73")
    draw.text(
        (310, 250),
        "Virtualization Administration Toolkit",
        fill=WHITE,
        font=load_font(62, True),
    )
    draw.text(
        (310, 345),
        "Enterprise workbook automation for Virtualization reporting",
        fill=LIGHT_BLUE,
        font=load_font(30),
    )
    draw.text((310, 455), "Version 1.0.0", fill=WHITE, font=load_font(28, True))
    draw.text((310, 510), "Author: <Author Name>", fill=WHITE, font=load_font(26))
    draw.text((310, 560), "Company: <Company Name>", fill=WHITE, font=load_font(26))
    draw.text(
        (310, 650),
        "Professional Excel reports powered by Python",
        fill=LIGHT_BLUE,
        font=load_font(24),
    )
    img.save(ASSET_DIR / "cover-preview.png")


def create_dashboard_preview() -> None:
    """Create the dashboard sales preview image."""
    img = Image.new("RGB", (1600, 900), CANVAS)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((80, 50, 1520, 145), 22, fill=NAVY)
    draw.text(
        (125, 78),
        "Virtualization Executive Dashboard",
        fill=WHITE,
        font=load_font(44, True),
    )

    cards = [
        ((90, 190, 450, 320), "Total VMs", "124", BLUE),
        ((620, 190, 980, 320), "Powered On", "118", GREEN),
        ((1150, 190, 1510, 320), "Critical", "7", RED),
    ]
    for card in cards:
        draw_card(draw, *card)

    chart_boxes = [
        (90, 390, 500, 780, "Power State"),
        (595, 390, 1005, 780, "Environment"),
        (1100, 390, 1510, 780, "Storage Utilization"),
    ]
    for x1, y1, x2, y2, title in chart_boxes:
        draw.rounded_rectangle((x1, y1, x2, y2), 20, fill=WHITE, outline="#D6DEE8")
        draw.text((x1 + 24, y1 + 20), title, fill=DARK, font=load_font(25, True))
        draw.rectangle((x1 + 70, y2 - 95, x2 - 70, y2 - 70), fill=LIGHT_BLUE)
        draw.rectangle((x1 + 95, y2 - 150, x1 + 155, y2 - 70), fill=BLUE)
        draw.rectangle((x1 + 185, y2 - 230, x1 + 245, y2 - 70), fill=GREEN)
        draw.rectangle((x1 + 275, y2 - 185, x1 + 335, y2 - 70), fill=AMBER)
    img.save(ASSET_DIR / "dashboard-preview.png")


def create_inventory_preview() -> None:
    """Create the VM inventory sales preview image."""
    img = Image.new("RGB", (1600, 900), CANVAS)
    draw = ImageDraw.Draw(img)
    draw.text((80, 60), "VM Inventory", fill=DARK, font=load_font(48, True))
    headers = ["VM Name", "Environment", "Owner", "OS", "Backup", "Criticality"]
    rows = [
        ["APP-PRD-001", "Production", "App Ops", "Windows", "Yes", "Critical"],
        ["SQL-DEV-002", "Development", "DB Team", "Ubuntu", "Yes", "Medium"],
        ["WEB-TST-003", "Test", "Web Team", "RHEL", "No", "Low"],
        ["FILE-LEG-004", "Production", "Infra", "Windows", "Yes", "High"],
    ]
    draw_table_preview(draw, (80, 160, 1520, 650), headers, rows)
    draw.text(
        (80, 735),
        "114 enterprise inventory fields with dropdowns and conditional formatting",
        fill=MUTED,
        font=load_font(28),
    )
    img.save(ASSET_DIR / "vm-inventory-preview.png")


def create_capacity_preview() -> None:
    """Create the capacity planner sales preview image."""
    img = Image.new("RGB", (1600, 900), CANVAS)
    draw = ImageDraw.Draw(img)
    draw.text((80, 60), "Capacity Planner", fill=DARK, font=load_font(48, True))
    headers = ["Cluster", "CPU", "Memory", "Storage", "Growth", "Forecast"]
    rows = [
        ["Production", "70%", "76%", "77%", "18%", "86%"],
        ["Development", "56%", "53%", "66%", "12%", "73%"],
        ["Test", "49%", "48%", "85%", "20%", "102%"],
        ["DR", "50%", "60%", "81%", "15%", "93%"],
    ]
    draw_table_preview(draw, (80, 160, 1520, 430), headers, rows)
    draw.rounded_rectangle((120, 520, 1480, 800), 24, fill=WHITE, outline="#D6DEE8")
    draw.text(
        (155, 545),
        "Forecast and Recommendation Charts",
        fill=DARK,
        font=load_font(28, True),
    )
    for index, height in enumerate([110, 165, 205, 145]):
        x = 220 + index * 220
        draw.rectangle((x, 755 - height, x + 90, 755), fill=BLUE)
        draw.rectangle((x + 105, 735 - height, x + 195, 755), fill=GREEN)
    img.save(ASSET_DIR / "capacity-planner-preview.png")


def build_pdf() -> None:
    """Create the commercial ReadMe PDF."""
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=26,
        textColor=colors.HexColor(NAVY),
        spaceAfter=18,
    )
    heading = ParagraphStyle(
        "HeadingCustom",
        parent=styles["Heading2"],
        textColor=colors.HexColor(BLUE),
        spaceBefore=12,
        spaceAfter=8,
    )
    body = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=8,
    )

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )

    story = [
        Paragraph("Virtualization Administration Toolkit", title),
        Paragraph("Commercial Product ReadMe", heading),
        Paragraph(
            "A professional Python 3.12 and openpyxl workbook automation "
            "toolkit for Virtualization administration reporting, executive "
            "dashboards, capacity planning, backup tracking, snapshot "
            "governance, and infrastructure inventory documentation.",
            body,
        ),
        Spacer(1, 8),
        Paragraph("Included Modules", heading),
    ]

    modules = [
        ["Module", "Commercial Purpose"],
        ["Cover Page", "Premium branded workbook front page"],
        ["Executive Dashboard", "Power BI-style KPI and chart summary"],
        ["VM Inventory", "Enterprise VM documentation with 114 fields"],
        ["Host Inventory", "Host, license, health, and cluster tracking"],
        ["Datastore", "Capacity, free space, utilization, and warnings"],
        ["Snapshot Tracker", "Automatic age calculation and risk colors"],
        ["Capacity Planner", "Growth forecasts and recommendations"],
        ["Backup Register", "Backup compliance and restore-test tracking"],
    ]
    table = Table(modules, colWidths=[2.1 * inch, 4.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D6DEE8")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFD")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend([table, Spacer(1, 14)])

    sections = [
        (
            "Key Benefits",
            [
                "Reduces manual Virtualization report-building effort.",
                "Creates a polished foundation for client-ready assessments.",
                "Centralizes inventory, backup, snapshot, and capacity views.",
                "Uses editable Excel output suitable for enterprise workflows.",
            ],
        ),
        (
            "Technical Requirements",
            [
                "Python 3.12",
                "openpyxl",
                "Microsoft Excel or a compatible XLSX viewer",
            ],
        ),
        (
            "How to Run",
            [
                "Create a Python virtual environment.",
                "Install dependencies with: pip install -r requirements.txt",
                "Run the Python workbook generator once orchestration is wired.",
            ],
        ),
        (
            "Commercial Use Notes",
            [
                "Customize company branding, colors, sample data, and output "
                "paths before resale or client delivery.",
                "Validate formulas and workbook output against customer "
                "requirements before production use.",
                "Add licensing terms and support policy appropriate for your "
                "sales channel.",
            ],
        ),
    ]

    for section_title, bullets in sections:
        story.append(Paragraph(section_title, heading))
        for bullet in bullets:
            story.append(Paragraph(f"• {bullet}", body))

    story.extend(
        [
            PageBreak(),
            Paragraph("Preview Images", title),
            Paragraph(
                "PNG mockups are included in assets/preview for marketplace "
                "listings, documentation pages, and product galleries.",
                body,
            ),
            Paragraph("Generated Preview Files", heading),
        ]
    )
    for file_name in [
        "cover-preview.png",
        "dashboard-preview.png",
        "vm-inventory-preview.png",
        "capacity-planner-preview.png",
    ]:
        story.append(Paragraph(f"• assets/preview/{file_name}", body))

    doc.build(story)


def main() -> None:
    """Generate all commercial collateral assets."""
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    create_cover_preview()
    create_dashboard_preview()
    create_inventory_preview()
    create_capacity_preview()
    build_pdf()


if __name__ == "__main__":
    main()

