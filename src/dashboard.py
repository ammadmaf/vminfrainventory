"""Executive Dashboard worksheet generation.

This module creates only the executive dashboard worksheet. KPI cards reference
the VM Inventory worksheet and do not create or modify inventory data.
"""

from __future__ import annotations

from dataclasses import dataclass

from openpyxl import Workbook
from openpyxl.chart import BarChart, DoughnutChart, PieChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter, range_boundaries
from openpyxl.worksheet.worksheet import Worksheet

from .styles import workbook_theme
from .vm_inventory import VM_INVENTORY_COLUMNS


VM_INVENTORY_SHEET = "VM Inventory"


@dataclass(frozen=True)
class KpiCard:
    """Definition for a dashboard KPI card."""

    icon: str
    title: str
    formula: str
    cell_range: str
    accent_color: str


class DashboardWorksheet:
    """Builds the Executive Dashboard worksheet."""

    sheet_name = "Executive Dashboard"

    def __init__(self, inventory_sheet_name: str = VM_INVENTORY_SHEET) -> None:
        """Initialize dashboard settings."""
        self.inventory_sheet_name = inventory_sheet_name
        self.theme = workbook_theme()
        self.palette = self.theme.palette
        self.canvas_color = "F3F6FA"
        self.card_fill = "FFFFFF"
        self.card_shadow = "E7ECF3"
        self.card_border = "D6DEE8"
        self.text_dark = "172B4D"
        self.text_muted = "5E6C84"

    def build(self, workbook: Workbook) -> Worksheet:
        """Create and format the Executive Dashboard worksheet only."""
        worksheet = self._get_worksheet(workbook)
        self._reset_worksheet(worksheet)
        self._configure_worksheet(worksheet)
        self._paint_report_canvas(worksheet)
        self._add_header(worksheet)
        self._add_section_title(worksheet, "B7:L7", "â—‰ KPI Overview")
        self._add_kpi_cards(worksheet)
        self._add_section_title(worksheet, "B22:L22", "â–£ Operational Charts")
        self._add_chart_summaries(worksheet)
        self._add_chart_containers(worksheet)
        self._add_charts(worksheet)
        self._add_footer(worksheet)
        return worksheet

    def _get_worksheet(self, workbook: Workbook) -> Worksheet:
        """Return the dashboard worksheet without creating other worksheets."""
        if self.sheet_name in workbook.sheetnames:
            return workbook[self.sheet_name]

        if len(workbook.worksheets) == 1 and workbook.active.max_row == 1:
            worksheet = workbook.active
            worksheet.title = self.sheet_name
            return worksheet

        return workbook.create_sheet(self.sheet_name)

    @staticmethod
    def _reset_worksheet(worksheet: Worksheet) -> None:
        """Clear existing dashboard content before rebuilding."""
        for merged_range in list(worksheet.merged_cells.ranges):
            worksheet.unmerge_cells(str(merged_range))

        if worksheet.max_row:
            worksheet.delete_rows(1, worksheet.max_row)

        worksheet._charts = []

    def _configure_worksheet(self, worksheet: Worksheet) -> None:
        """Apply professional dashboard layout settings."""
        worksheet.sheet_view.showGridLines = False
        worksheet.freeze_panes = None
        worksheet.sheet_properties.tabColor = self.palette.blue

        worksheet.page_setup.orientation = "landscape"
        worksheet.page_setup.fitToWidth = 1
        worksheet.page_setup.fitToHeight = 0
        worksheet.page_margins.left = 0.25
        worksheet.page_margins.right = 0.25
        worksheet.page_margins.top = 0.25
        worksheet.page_margins.bottom = 0.25

        for column in range(1, 14):
            worksheet.column_dimensions[get_column_letter(column)].width = 15

        for column in range(14, 31):
            column_letter = get_column_letter(column)
            worksheet.column_dimensions[column_letter].width = 18

        for row in range(1, 61):
            worksheet.row_dimensions[row].height = 24

    def _paint_report_canvas(self, worksheet: Worksheet) -> None:
        """Apply a Power BI-inspired report canvas background."""
        fill = PatternFill("solid", fgColor=self.canvas_color)
        for row in worksheet["A1:M60"]:
            for cell in row:
                cell.fill = fill

        worksheet.column_dimensions["A"].width = 4
        worksheet.column_dimensions["M"].width = 4

    def _add_header(self, worksheet: Worksheet) -> None:
        """Add the executive dashboard title block."""
        self._apply_panel(worksheet, "B2:L5", self.palette.navy, self.palette.navy)
        worksheet.merge_cells("B2:L4")
        title_cell = worksheet["B2"]
        title_cell.value = "â—ˆ Virtualization Executive Dashboard"
        title_cell.font = Font(
            name="Calibri Light",
            size=32,
            bold=True,
            color=self.palette.white,
        )
        title_cell.fill = PatternFill("solid", fgColor=self.palette.navy)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        worksheet.merge_cells("B5:L5")
        subtitle_cell = worksheet["B5"]
        subtitle_cell.value = "Enterprise VM estate health and operational summary"
        subtitle_cell.font = Font(
            name="Calibri",
            size=13,
            italic=True,
            color=self.palette.light_blue,
        )
        subtitle_cell.fill = PatternFill("solid", fgColor=self.palette.navy)
        subtitle_cell.alignment = Alignment(horizontal="center", vertical="center")

    def _add_section_title(
        self,
        worksheet: Worksheet,
        cell_range: str,
        title: str,
    ) -> None:
        """Add a Power BI-style section heading."""
        worksheet.merge_cells(cell_range)
        top_left = cell_range.split(":")[0]
        cell = worksheet[top_left]
        cell.value = title
        cell.font = Font(name="Calibri", size=14, bold=True, color=self.text_dark)
        cell.fill = PatternFill("solid", fgColor=self.canvas_color)
        cell.alignment = Alignment(horizontal="left", vertical="center")

    def _add_kpi_cards(self, worksheet: Worksheet) -> None:
        """Add all requested executive KPI cards."""
        for card in self._kpi_cards():
            self._add_kpi_card(worksheet, card)

    def _add_kpi_card(self, worksheet: Worksheet, card: KpiCard) -> None:
        """Render a merged-cell KPI card."""
        min_col, min_row, max_col, max_row = range_boundaries(card.cell_range)
        title_range = (
            f"{get_column_letter(min_col)}{min_row}:"
            f"{get_column_letter(max_col)}{min_row}"
        )
        value_range = (
            f"{get_column_letter(min_col)}{min_row + 1}:"
            f"{get_column_letter(max_col)}{max_row}"
        )

        self._add_card_shadow(worksheet, card.cell_range)
        self._apply_panel(worksheet, card.cell_range, self.card_fill, self.card_border)
        worksheet.merge_cells(title_range)
        worksheet.merge_cells(value_range)

        title_cell = worksheet.cell(row=min_row, column=min_col)
        title_cell.value = f"{card.icon}  {card.title}"
        title_cell.font = Font(
            name="Calibri",
            size=12,
            bold=True,
            color=self.text_muted,
        )
        title_cell.alignment = Alignment(horizontal="left", vertical="center")
        title_cell.fill = PatternFill("solid", fgColor=self.card_fill)

        value_cell = worksheet.cell(row=min_row + 1, column=min_col)
        value_cell.value = card.formula
        value_cell.font = Font(
            name="Calibri Light",
            size=30,
            bold=True,
            color=card.accent_color,
        )
        value_cell.alignment = Alignment(
            horizontal="left",
            vertical="center",
        )
        value_cell.fill = PatternFill("solid", fgColor=self.card_fill)

        accent_column = get_column_letter(min_col)
        for row_index in range(min_row, max_row + 1):
            worksheet[f"{accent_column}{row_index}"].border = Border(
                left=Side(style="thick", color=card.accent_color)
            )

        worksheet.row_dimensions[min_row].height = 26
        worksheet.row_dimensions[min_row + 1].height = 44
        worksheet.row_dimensions[min_row + 2].height = 44

    def _add_footer(self, worksheet: Worksheet) -> None:
        """Add dashboard footer guidance."""
        worksheet.merge_cells("B58:L59")
        footer_cell = worksheet["B58"]
        footer_cell.value = (
            "KPI values and charts are calculated from the VM Inventory worksheet."
        )
        footer_cell.font = Font(
            name="Calibri",
            size=11,
            italic=True,
            color=self.palette.medium_gray,
        )
        footer_cell.alignment = Alignment(horizontal="center", vertical="center")

    def _add_chart_containers(self, worksheet: Worksheet) -> None:
        """Add bordered report-card containers behind chart objects."""
        containers = (
            "B23:D38",
            "F23:H38",
            "J23:L38",
            "B40:D55",
            "F40:H55",
            "J40:L55",
        )
        for cell_range in containers:
            self._add_card_shadow(worksheet, cell_range)
            self._apply_panel(worksheet, cell_range, self.card_fill, self.card_border)

    def _add_card_shadow(self, worksheet: Worksheet, cell_range: str) -> None:
        """Apply a subtle cell-based shadow beside a report card."""
        min_col, min_row, max_col, max_row = range_boundaries(cell_range)
        shadow_fill = PatternFill("solid", fgColor=self.card_shadow)

        if max_col + 1 <= 13:
            for row_index in range(min_row + 1, max_row + 2):
                worksheet.cell(row_index, max_col + 1).fill = shadow_fill

        if max_row + 1 <= 60:
            for column_index in range(min_col + 1, max_col + 2):
                worksheet.cell(max_row + 1, column_index).fill = shadow_fill

    def _apply_panel(
        self,
        worksheet: Worksheet,
        cell_range: str,
        fill_color: str,
        border_color: str,
    ) -> None:
        """Apply a polished card panel fill and border."""
        min_col, min_row, max_col, max_row = range_boundaries(cell_range)
        fill = PatternFill("solid", fgColor=fill_color)
        thin = Side(style="thin", color=border_color)
        corner_font = Font(name="Calibri", size=8, color=border_color)

        for row in worksheet[cell_range]:
            for cell in row:
                cell.fill = fill
                cell.border = Border(
                    left=thin if cell.column == min_col else Side(style=None),
                    right=thin if cell.column == max_col else Side(style=None),
                    top=thin if cell.row == min_row else Side(style=None),
                    bottom=thin if cell.row == max_row else Side(style=None),
                )

        # Excel cells do not support true radius; glyphs soften the corners.
        corner_glyphs = {
            (min_row, min_col): "â•­",
            (min_row, max_col): "â•®",
            (max_row, min_col): "â•°",
            (max_row, max_col): "â•¯",
        }
        for (row_index, column_index), glyph in corner_glyphs.items():
            cell = worksheet.cell(row_index, column_index)
            cell.value = glyph if cell.value is None else cell.value
            cell.font = corner_font

    def _add_chart_summaries(self, worksheet: Worksheet) -> None:
        """Add formula-backed summary tables for dashboard charts."""
        summary_tables = (
            (
                "N2",
                "Power State",
                (
                    (
                        "Powered On",
                        self._count_text_formula("Power State", "Powered On"),
                    ),
                    (
                        "Powered Off",
                        self._count_text_formula("Power State", "Powered Off"),
                    ),
                    ("Suspended", self._count_text_formula("Power State", "Suspended")),
                ),
            ),
            (
                "Q2",
                "Environment",
                (
                    (
                        "Production",
                        self._count_text_formula("Environment", "Production"),
                    ),
                    (
                        "Development",
                        self._count_text_formula("Environment", "Development"),
                    ),
                    ("Test", self._count_text_formula("Environment", "Test")),
                    ("Staging", self._count_text_formula("Environment", "Staging")),
                    ("DR", self._count_text_formula("Environment", "DR")),
                ),
            ),
            (
                "T2",
                "OS Distribution",
                (
                    (
                        "Windows",
                        self._count_contains_formula("Operating System", "Windows"),
                    ),
                    ("Linux", self._linux_formula()),
                    ("Other", "=MAX(0,$B$9-$U$3-$U$4)"),
                ),
            ),
            (
                "W2",
                "Backup Compliance",
                (
                    ("Enabled", self._count_text_formula("Backup", "Yes")),
                    ("Disabled", self._count_text_formula("Backup", "No")),
                    (
                        "Not Required",
                        self._count_text_formula("Backup", "Not Required"),
                    ),
                ),
            ),
            (
                "Z2",
                "Criticality",
                (
                    ("Critical", self._count_text_formula("Criticality", "Critical")),
                    ("High", self._count_text_formula("Criticality", "High")),
                    ("Medium", self._count_text_formula("Criticality", "Medium")),
                    ("Low", self._count_text_formula("Criticality", "Low")),
                ),
            ),
            (
                "AC2",
                "Storage Utilization",
                (
                    ("Capacity", "=SUM('Datastore'!D:D)"),
                    ("Used", "=SUM('Datastore'!E:E)"),
                    ("Free", "=SUM('Datastore'!F:F)"),
                ),
            ),
        )

        for start_cell, title, rows in summary_tables:
            self._write_summary_table(worksheet, start_cell, title, rows)

    def _write_summary_table(
        self,
        worksheet: Worksheet,
        start_cell: str,
        title: str,
        rows: tuple[tuple[str, str], ...],
    ) -> None:
        """Write one summary table for a chart."""
        start = worksheet[start_cell]
        label_column = start.column
        value_column = start.column + 1
        header_row = start.row

        worksheet.cell(header_row, label_column, title)
        worksheet.cell(header_row, value_column, "Count")

        for cell in (
            worksheet.cell(header_row, label_column),
            worksheet.cell(header_row, value_column),
        ):
            cell.font = Font(name="Calibri", size=11, bold=True)
            cell.fill = PatternFill("solid", fgColor=self.palette.light_blue)
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for row_offset, (label, formula) in enumerate(rows, start=1):
            worksheet.cell(header_row + row_offset, label_column, label)
            worksheet.cell(header_row + row_offset, value_column, formula)

    def _add_charts(self, worksheet: Worksheet) -> None:
        """Add native Excel charts to the executive dashboard."""
        self._add_pie_chart(
            worksheet=worksheet,
            title="Power State",
            data_range=(15, 2, 5),
            label_range=(14, 3, 5),
            anchor="B23",
        )
        self._add_bar_chart(
            worksheet=worksheet,
            title="Environment",
            data_range=(18, 2, 7),
            label_range=(17, 3, 7),
            anchor="F23",
            y_axis_title="VMs",
        )
        self._add_doughnut_chart(
            worksheet=worksheet,
            title="OS Distribution",
            data_range=(21, 2, 5),
            label_range=(20, 3, 5),
            anchor="J23",
        )
        self._add_doughnut_chart(
            worksheet=worksheet,
            title="Backup Compliance",
            data_range=(24, 2, 5),
            label_range=(23, 3, 5),
            anchor="B40",
        )
        self._add_bar_chart(
            worksheet=worksheet,
            title="Criticality",
            data_range=(27, 2, 6),
            label_range=(26, 3, 6),
            anchor="F40",
            y_axis_title="VMs",
        )
        self._add_bar_chart(
            worksheet=worksheet,
            title="Storage Utilization",
            data_range=(30, 2, 5),
            label_range=(29, 3, 5),
            anchor="J40",
            y_axis_title="GB",
        )

    @staticmethod
    def _add_pie_chart(
        worksheet: Worksheet,
        title: str,
        data_range: tuple[int, int, int],
        label_range: tuple[int, int, int],
        anchor: str,
    ) -> None:
        """Add a native Excel pie chart."""
        chart = PieChart()
        chart.title = title
        chart.height = 7.0
        chart.width = 9.0
        chart.style = 10
        chart.plotVisOnly = False

        DashboardWorksheet._add_chart_data(
            chart,
            worksheet,
            data_range,
            label_range,
        )
        worksheet.add_chart(chart, anchor)

    @staticmethod
    def _add_doughnut_chart(
        worksheet: Worksheet,
        title: str,
        data_range: tuple[int, int, int],
        label_range: tuple[int, int, int],
        anchor: str,
    ) -> None:
        """Add a native Excel doughnut chart."""
        chart = DoughnutChart()
        chart.title = title
        chart.height = 7.0
        chart.width = 9.0
        chart.holeSize = 55
        chart.style = 10
        chart.plotVisOnly = False

        DashboardWorksheet._add_chart_data(
            chart,
            worksheet,
            data_range,
            label_range,
        )
        worksheet.add_chart(chart, anchor)

    @staticmethod
    def _add_bar_chart(
        worksheet: Worksheet,
        title: str,
        data_range: tuple[int, int, int],
        label_range: tuple[int, int, int],
        anchor: str,
        y_axis_title: str,
    ) -> None:
        """Add a native Excel vertical bar chart."""
        chart = BarChart()
        chart.title = title
        chart.height = 7.0
        chart.width = 9.0
        chart.style = 11
        chart.type = "col"
        chart.y_axis.title = y_axis_title
        chart.x_axis.title = ""
        chart.legend = None
        chart.plotVisOnly = False

        DashboardWorksheet._add_chart_data(
            chart,
            worksheet,
            data_range,
            label_range,
        )
        worksheet.add_chart(chart, anchor)

    @staticmethod
    def _add_chart_data(
        chart: PieChart | DoughnutChart | BarChart,
        worksheet: Worksheet,
        data_range: tuple[int, int, int],
        label_range: tuple[int, int, int],
    ) -> None:
        """Attach worksheet summary data to a chart."""
        data_column, data_start_row, data_end_row = data_range
        label_column, label_start_row, label_end_row = label_range
        data = Reference(
            worksheet,
            min_col=data_column,
            min_row=data_start_row,
            max_row=data_end_row,
        )
        labels = Reference(
            worksheet,
            min_col=label_column,
            min_row=label_start_row,
            max_row=label_end_row,
        )
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(labels)

    def _kpi_cards(self) -> tuple[KpiCard, ...]:
        """Return dashboard KPI card definitions."""
        return (
            KpiCard(
                "â–¦",
                "Total VMs",
                self._count_all_formula("VM Name"),
                "B8:D10",
                self.palette.navy,
            ),
            KpiCard(
                "â—†",
                "Production VMs",
                self._count_text_formula("Environment", "Production"),
                "F8:H10",
                self.palette.blue,
            ),
            KpiCard(
                "â—",
                "Powered On",
                self._count_text_formula("Power State", "Powered On"),
                "J8:L10",
                self.palette.green,
            ),
            KpiCard(
                "â– ",
                "Powered Off",
                self._count_text_formula("Power State", "Powered Off"),
                "B13:D15",
                self.palette.red,
            ),
            KpiCard(
                "â—Œ",
                "Snapshots",
                self._count_text_formula("Snapshot", "Yes"),
                "F13:H15",
                self.palette.amber,
            ),
            KpiCard(
                "âœ“",
                "Backups Enabled",
                self._count_text_formula("Backup", "Yes"),
                "J13:L15",
                self.palette.green,
            ),
            KpiCard(
                "!",
                "Critical Servers",
                self._count_text_formula("Criticality", "Critical"),
                "B18:D20",
                self.palette.red,
            ),
            KpiCard(
                "âŒ˜",
                "Linux",
                self._linux_formula(),
                "F18:H20",
                self.palette.dark_gray,
            ),
            KpiCard(
                "âŠž",
                "Windows",
                self._count_contains_formula("Operating System", "Windows"),
                "J18:L20",
                self.palette.blue,
            ),
        )

    def _count_all_formula(self, column_name: str) -> str:
        """Return a formula that counts populated inventory rows."""
        column = self._inventory_column_letter(column_name)
        return f'=COUNTA({self._sheet_range(column)})-1'

    def _count_text_formula(self, column_name: str, value: str) -> str:
        """Return a formula that counts exact text values."""
        column = self._inventory_column_letter(column_name)
        return f'=COUNTIF({self._sheet_range(column)},"{value}")'

    def _count_contains_formula(self, column_name: str, value: str) -> str:
        """Return a formula that counts cells containing text."""
        column = self._inventory_column_letter(column_name)
        return f'=COUNTIF({self._sheet_range(column)},"*{value}*")'

    def _sum_formula(self, column_name: str) -> str:
        """Return a formula that sums numeric inventory values."""
        column = self._inventory_column_letter(column_name)
        return f"=SUM({self._sheet_range(column)})"

    def _linux_formula(self) -> str:
        """Return a formula that counts common Linux distributions."""
        column = self._inventory_column_letter("Operating System")
        sheet_range = self._sheet_range(column)
        return (
            f'=SUM(COUNTIF({sheet_range},'
            '{"*Linux*","*Ubuntu*","*Red Hat*","*CentOS*","*Debian*","*SUSE*"}))'
        )

    def _inventory_column_letter(self, column_name: str) -> str:
        """Return the Excel column letter for a VM Inventory column."""
        column_index = VM_INVENTORY_COLUMNS.index(column_name) + 1
        return get_column_letter(column_index)

    def _sheet_range(self, column_letter: str) -> str:
        """Return a full-column reference for the inventory worksheet."""
        quoted_sheet = self.inventory_sheet_name.replace("'", "''")
        return f"'{quoted_sheet}'!{column_letter}:{column_letter}"


