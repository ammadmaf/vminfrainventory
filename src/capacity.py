"""Capacity Planner worksheet generation.

This module creates only the ``Capacity Planner`` worksheet. It includes
formula-driven utilization, growth forecasts, recommendations, and charts.
"""

from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from typing import Any

from openpyxl import Workbook
from openpyxl.cell.cell import Cell
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet

from .styles import header_style, table_styles, workbook_theme


CAPACITY_COLUMNS: tuple[str, ...] = (
    "Cluster",
    "CPU Capacity (GHz)",
    "CPU Used (GHz)",
    "CPU Utilization",
    "Memory Capacity (GB)",
    "Memory Used (GB)",
    "Memory Utilization",
    "Storage Capacity (TB)",
    "Storage Used (TB)",
    "Storage Utilization",
    "Growth %",
    "6 Month Forecast",
    "12 Month Forecast",
    "Recommendations",
)


@dataclass(frozen=True)
class CapacityRecord:
    """Sample capacity planning row."""

    cluster: str
    cpu_capacity_ghz: int
    cpu_used_ghz: int
    memory_capacity_gb: int
    memory_used_gb: int
    storage_capacity_tb: int
    storage_used_tb: int
    growth_percent: float

    def as_row(self, row_index: int) -> tuple[Any, ...]:
        """Return the record in worksheet order with forecast formulas."""
        cpu_utilization = f"=IFERROR(C{row_index}/B{row_index},0)"
        memory_utilization = f"=IFERROR(F{row_index}/E{row_index},0)"
        storage_utilization = f"=IFERROR(I{row_index}/H{row_index},0)"
        six_month_forecast = f"=J{row_index}*(1+(K{row_index}/2))"
        twelve_month_forecast = f"=J{row_index}*(1+K{row_index})"
        recommendation = (
            f'=IF(M{row_index}>=0.9,"Add capacity immediately",'
            f'IF(M{row_index}>=0.8,"Plan expansion within 90 days",'
            f'IF(MAX(D{row_index},G{row_index},J{row_index})>=0.75,'
            f'"Monitor closely","Capacity healthy")))'
        )

        return (
            self.cluster,
            self.cpu_capacity_ghz,
            self.cpu_used_ghz,
            cpu_utilization,
            self.memory_capacity_gb,
            self.memory_used_gb,
            memory_utilization,
            self.storage_capacity_tb,
            self.storage_used_tb,
            storage_utilization,
            self.growth_percent,
            six_month_forecast,
            twelve_month_forecast,
            recommendation,
        )


class CapacityWorksheet:
    """Builds a professional Capacity Planner worksheet."""

    sheet_name = "Capacity Planner"
    table_name = "CapacityPlannerTable"

    def __init__(self, records: list[CapacityRecord] | None = None) -> None:
        """Initialize the worksheet builder with optional capacity records."""
        self.records = records if records is not None else self._sample_records()
        self.theme = workbook_theme()
        self.header = header_style("capacity_planner_header")
        self.table = table_styles()

    def build(self, workbook: Workbook) -> Worksheet:
        """Create and format the Capacity Planner worksheet."""
        worksheet = self._get_worksheet(workbook)
        self._reset_worksheet(worksheet)
        self._configure_worksheet(worksheet)
        self._write_headers(worksheet)
        self._write_sample_data(worksheet)
        self._add_chart_data_tables(worksheet)
        self._apply_table(worksheet)
        self._apply_dropdowns(worksheet)
        self._apply_body_formatting(worksheet)
        self._apply_conditional_formatting(worksheet)
        self._add_charts(worksheet)
        self._auto_fit_columns(worksheet)
        return worksheet

    def _get_worksheet(self, workbook: Workbook) -> Worksheet:
        """Return the Capacity Planner worksheet."""
        if self.sheet_name in workbook.sheetnames:
            return workbook[self.sheet_name]

        if len(workbook.worksheets) == 1 and workbook.active.max_row == 1:
            worksheet = workbook.active
            worksheet.title = self.sheet_name
            return worksheet

        return workbook.create_sheet(self.sheet_name)

    @staticmethod
    def _reset_worksheet(worksheet: Worksheet) -> None:
        """Clear existing content, tables, charts, and formatting rules."""
        for merged_range in list(worksheet.merged_cells.ranges):
            worksheet.unmerge_cells(str(merged_range))

        if worksheet.max_row:
            worksheet.delete_rows(1, worksheet.max_row)

        worksheet.tables.clear()
        worksheet._charts = []
        worksheet.conditional_formatting._cf_rules.clear()

    def _configure_worksheet(self, worksheet: Worksheet) -> None:
        """Apply professional worksheet layout settings."""
        worksheet.sheet_view.showGridLines = False
        worksheet.freeze_panes = "A2"
        worksheet.sheet_properties.tabColor = self.theme.palette.green
        worksheet.page_setup.orientation = "landscape"
        worksheet.page_setup.fitToWidth = 1
        worksheet.page_setup.fitToHeight = 0
        worksheet.row_dimensions[1].height = 28

    def _write_headers(self, worksheet: Worksheet) -> None:
        """Write Capacity Planner headers."""
        for column_index, header in enumerate(CAPACITY_COLUMNS, start=1):
            cell = worksheet.cell(row=1, column=column_index, value=header)
            self._apply_named_style(cell, self.header)

    def _write_sample_data(self, worksheet: Worksheet) -> None:
        """Write sample capacity data with formulas."""
        for row_index, record in enumerate(self.records, start=2):
            for column_index, value in enumerate(record.as_row(row_index), start=1):
                worksheet.cell(row=row_index, column=column_index, value=value)

    def _apply_table(self, worksheet: Worksheet) -> None:
        """Create an Excel table with filters over planner data."""
        table_range = f"A1:N{worksheet.max_row}"
        table = Table(displayName=self.table_name, ref=table_range)
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )

        worksheet.add_table(table)

    @staticmethod
    def _apply_dropdowns(worksheet: Worksheet) -> None:
        """Add governed dropdowns to capacity planner fields."""
        validation = DataValidation(
            type="list",
            formula1="=RefClusters",
            allow_blank=True,
        )
        validation.error = "Select a valid cluster from Reference Data."
        validation.errorTitle = "Invalid Cluster"
        validation.prompt = "Select a governed cluster."
        validation.promptTitle = "Cluster"
        validation.showErrorMessage = True
        validation.showInputMessage = True
        worksheet.add_data_validation(validation)
        validation.add("A2:A1000")

    def _apply_body_formatting(self, worksheet: Worksheet) -> None:
        """Apply corporate table styling and number formats."""
        numeric_columns = {2, 3, 5, 6, 8, 9}
        percentage_columns = {4, 7, 10, 11, 12, 13}

        for row in worksheet.iter_rows(
            min_row=2,
            max_row=worksheet.max_row,
            min_col=1,
            max_col=len(CAPACITY_COLUMNS),
        ):
            for cell in row:
                style = (
                    self.table["table_numeric"]
                    if (
                        cell.column in numeric_columns
                        or cell.column in percentage_columns
                    )
                    else self.table["table_body"]
                )
                self._apply_named_style(cell, style)

                if cell.column in numeric_columns:
                    cell.number_format = '#,##0'
                elif cell.column in percentage_columns:
                    cell.number_format = "0.0%"

        for row_index in range(2, worksheet.max_row + 1):
            worksheet.row_dimensions[row_index].height = 22

    @staticmethod
    def _apply_conditional_formatting(worksheet: Worksheet) -> None:
        """Highlight capacity risk levels for utilization and forecast fields."""
        max_row = max(worksheet.max_row, 2)

        for column in ("D", "G", "J", "L", "M"):
            worksheet.conditional_formatting.add(
                f"{column}2:{column}{max_row}",
                CellIsRule(
                    operator="greaterThanOrEqual",
                    formula=["0.9"],
                    fill=PatternFill("solid", fgColor="F4CCCC"),
                    font=Font(color="9C0006", bold=True),
                ),
            )
            worksheet.conditional_formatting.add(
                f"{column}2:{column}{max_row}",
                CellIsRule(
                    operator="between",
                    formula=["0.8", "0.8999"],
                    fill=PatternFill("solid", fgColor="FFF2CC"),
                    font=Font(color="7F6000", bold=True),
                ),
            )

        worksheet.conditional_formatting.add(
            f"N2:N{max_row}",
            CellIsRule(
                operator="equal",
                formula=['"Add capacity immediately"'],
                fill=PatternFill("solid", fgColor="F4CCCC"),
                font=Font(color="9C0006", bold=True),
            ),
        )
        worksheet.conditional_formatting.add(
            f"N2:N{max_row}",
            CellIsRule(
                operator="equal",
                formula=['"Plan expansion within 90 days"'],
                fill=PatternFill("solid", fgColor="FFF2CC"),
                font=Font(color="7F6000", bold=True),
            ),
        )
        worksheet.conditional_formatting.add(
            f"N2:N{max_row}",
            CellIsRule(
                operator="equal",
                formula=['"Capacity healthy"'],
                fill=PatternFill("solid", fgColor="E2F0D9"),
                font=Font(color="006100", bold=True),
            ),
        )

    @staticmethod
    def _add_chart_data_tables(worksheet: Worksheet) -> None:
        """Add summary tables used by capacity charts."""
        headers = ("Cluster", "CPU", "Memory", "Storage")
        for offset, header in enumerate(headers, start=16):
            worksheet.cell(row=1, column=offset, value=header)

        forecast_headers = ("Cluster", "Current", "6 Month", "12 Month")
        for offset, header in enumerate(forecast_headers, start=21):
            worksheet.cell(row=1, column=offset, value=header)

        for row_index in range(2, worksheet.max_row + 1):
            worksheet.cell(row=row_index, column=16, value=f"=A{row_index}")
            worksheet.cell(row=row_index, column=17, value=f"=D{row_index}")
            worksheet.cell(row=row_index, column=18, value=f"=G{row_index}")
            worksheet.cell(row=row_index, column=19, value=f"=J{row_index}")
            worksheet.cell(row=row_index, column=21, value=f"=A{row_index}")
            worksheet.cell(row=row_index, column=22, value=f"=J{row_index}")
            worksheet.cell(row=row_index, column=23, value=f"=L{row_index}")
            worksheet.cell(row=row_index, column=24, value=f"=M{row_index}")

    @staticmethod
    def _add_charts(worksheet: Worksheet) -> None:
        """Add utilization and forecast charts to the worksheet."""
        max_row = worksheet.max_row

        utilization_chart = BarChart()
        utilization_chart.title = "CPU, Memory, and Storage Utilization"
        utilization_chart.y_axis.title = "Utilization"
        utilization_chart.x_axis.title = "Cluster"
        utilization_chart.height = 8.0
        utilization_chart.width = 16.0
        utilization_chart.style = 11

        utilization_data = Reference(
            worksheet,
            min_col=17,
            max_col=19,
            min_row=1,
            max_row=max_row,
        )
        cluster_labels = Reference(worksheet, min_col=16, min_row=2, max_row=max_row)
        utilization_chart.add_data(utilization_data, titles_from_data=True)
        utilization_chart.set_categories(cluster_labels)
        worksheet.add_chart(utilization_chart, "A8")

        forecast_chart = LineChart()
        forecast_chart.title = "Storage Growth Forecast"
        forecast_chart.y_axis.title = "Forecast Utilization"
        forecast_chart.x_axis.title = "Cluster"
        forecast_chart.height = 8.0
        forecast_chart.width = 16.0
        forecast_chart.style = 13

        forecast_data = Reference(
            worksheet,
            min_col=22,
            max_col=24,
            min_row=1,
            max_row=max_row,
        )
        forecast_labels = Reference(worksheet, min_col=21, min_row=2, max_row=max_row)
        forecast_chart.add_data(forecast_data, titles_from_data=True)
        forecast_chart.set_categories(forecast_labels)
        worksheet.add_chart(forecast_chart, "H8")

    @staticmethod
    def _apply_named_style(cell: Cell, named_style: Any) -> None:
        """Copy a named style's visual attributes onto a cell."""
        cell.font = copy(named_style.font)
        cell.fill = copy(named_style.fill)
        cell.border = copy(named_style.border)
        cell.alignment = copy(named_style.alignment)
        cell.number_format = named_style.number_format

    @staticmethod
    def _auto_fit_columns(worksheet: Worksheet) -> None:
        """Set practical column widths based on visible cell values."""
        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                if cell.value is None:
                    continue
                max_length = max(max_length, len(str(cell.value)))

            worksheet.column_dimensions[column_letter].width = min(
                max(max_length + 2, 12),
                34,
            )

    @staticmethod
    def _sample_records() -> list[CapacityRecord]:
        """Return representative cluster capacity planning rows."""
        return [
            CapacityRecord(
                cluster="Cluster-Production",
                cpu_capacity_ghz=560,
                cpu_used_ghz=392,
                memory_capacity_gb=4096,
                memory_used_gb=3120,
                storage_capacity_tb=120,
                storage_used_tb=92,
                growth_percent=0.18,
            ),
            CapacityRecord(
                cluster="Cluster-Development",
                cpu_capacity_ghz=320,
                cpu_used_ghz=178,
                memory_capacity_gb=2048,
                memory_used_gb=1090,
                storage_capacity_tb=64,
                storage_used_tb=42,
                growth_percent=0.12,
            ),
            CapacityRecord(
                cluster="Cluster-Test",
                cpu_capacity_ghz=240,
                cpu_used_ghz=118,
                memory_capacity_gb=1536,
                memory_used_gb=740,
                storage_capacity_tb=40,
                storage_used_tb=34,
                growth_percent=0.2,
            ),
            CapacityRecord(
                cluster="Cluster-DR",
                cpu_capacity_ghz=420,
                cpu_used_ghz=210,
                memory_capacity_gb=3072,
                memory_used_gb=1840,
                storage_capacity_tb=96,
                storage_used_tb=78,
                growth_percent=0.15,
            ),
        ]


