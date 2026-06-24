"""Reference data and governed resource registry worksheet generation."""

from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from typing import Any

from openpyxl import Workbook
from openpyxl.cell.cell import Cell
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill, Protection
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.worksheet import Worksheet

from .styles import header_style, table_styles, workbook_theme
from .vm_inventory import VM_INVENTORY_COLUMNS


REFERENCE_SHEET_NAME = "Reference Data"
REFERENCE_MAX_ROW = 200
LIVE_SOURCE_RANGES: dict[str, str] = {
    "RefHosts": "'Host Inventory'!$A$2:$A$1000",
    "RefClusters": "'Host Inventory'!$I$2:$I$1000",
    "RefDatastores": "'Datastore'!$A$2:$A$1000",
    "RefBackupJobs": "'Backup Register'!$A$9:$A$1000",
    "RefRepositories": "'Backup Register'!$C$9:$C$1000",
    "RefVMNames": "'VM Inventory'!$A$2:$A$1000",
}


@dataclass(frozen=True)
class ReferenceList:
    """Reference list definition used for dropdowns and governance."""

    title: str
    defined_name: str
    start_column: int
    values: tuple[str, ...]
    assignment_formula: str | None = None


def _vm_column_letter(column_name: str) -> str:
    """Return an Excel column letter for a VM Inventory column."""
    column_index = VM_INVENTORY_COLUMNS.index(column_name) + 1
    column_letter = ""
    while column_index:
        column_index, remainder = divmod(column_index - 1, 26)
        column_letter = chr(65 + remainder) + column_letter
    return column_letter


REFERENCE_LISTS: tuple[ReferenceList, ...] = (
    ReferenceList(
        "Hosts",
        "RefHosts",
        1,
        (
            "host-prd-01.company.local",
            "host-prd-02.company.local",
            "host-dev-01.company.local",
            "host-tst-01.company.local",
        ),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Clusters",
        "RefClusters",
        5,
        (
            "Cluster-Production",
            "Cluster-Development",
            "Cluster-Test",
            "Cluster-DR",
        ),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Datastores",
        "RefDatastores",
        9,
        ("DS-PRD-01", "DS-PRD-02", "DS-DEV-01", "DS-TST-01"),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "VLANs",
        "RefVLANs",
        13,
        ("VLAN-120", "VLAN-230", "VLAN-340"),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Backup Jobs",
        "RefBackupJobs",
        17,
        (
            "Daily-Production",
            "Weekly-Development",
            "Critical-SQL-Logs",
            "Legacy-Test-VMs",
            "Not Assigned",
        ),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Repositories",
        "RefRepositories",
        21,
        ("Repo-Primary", "Repo-Development", "Repo-Archive"),
        '=COUNTIF(\'Backup Register\'!$C:$C,{cell})',
    ),
    ReferenceList(
        "Folders",
        "RefFolders",
        25,
        (
            "/Production/Applications",
            "/Development/Databases",
            "/Test/Web",
        ),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Resource Pools",
        "RefResourcePools",
        29,
        ("RP-Production", "RP-Development", "RP-Test"),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Owners",
        "RefOwners",
        33,
        (
            "Application Operations",
            "Database Services",
            "Web Platform Team",
            "Infrastructure Operations",
        ),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Business Units",
        "RefBusinessUnits",
        37,
        ("Finance", "Engineering", "Digital", "Infrastructure"),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Management Servers",
        "RefManagementServers",
        41,
        ("mgmt-primary.company.local", "mgmt-dr.company.local"),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Datacenters",
        "RefDatacenters",
        45,
        ("Primary Datacenter", "DR Datacenter"),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Port Groups",
        "RefPortGroups",
        49,
        ("PG-PRD-APP", "PG-DEV-DB", "PG-TST-WEB"),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Distributed Switches",
        "RefDistributedSwitches",
        53,
        ("DSwitch-Production", "DSwitch-Development", "DSwitch-Test"),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Security Zones",
        "RefSecurityZones",
        57,
        ("Restricted", "Internal", "Development", "Test"),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "Support Groups",
        "RefSupportGroups",
        61,
        (
            "Finance Application Support",
            "Database Services",
            "Web Platform Team",
            "Infrastructure Operations",
        ),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
    ReferenceList(
        "VM Names",
        "RefVMNames",
        65,
        ("APP-PRD-001", "SQL-DEV-002", "WEB-TST-003"),
        '=COUNTIF(\'VM Inventory\'!${vm_col}:${vm_col},{cell})',
    ),
)


class ReferenceDataWorksheet:
    """Builds governed dropdown source lists and dependency warnings."""

    sheet_name = REFERENCE_SHEET_NAME

    def __init__(self) -> None:
        """Initialize reference data styles."""
        self.theme = workbook_theme()
        self.header = header_style("reference_data_header")
        self.table = table_styles()

    def build(self, workbook: Workbook) -> Worksheet:
        """Create reference data lists and workbook defined names."""
        worksheet = self._get_worksheet(workbook)
        self._reset_worksheet(worksheet)
        self._configure_worksheet(worksheet)
        self._write_title(worksheet)
        for reference_list in REFERENCE_LISTS:
            self._write_reference_list(worksheet, reference_list)
            self._create_defined_name(workbook, reference_list)
        self._apply_conditional_formatting(worksheet)
        return worksheet

    def _get_worksheet(self, workbook: Workbook) -> Worksheet:
        """Return the Reference Data worksheet."""
        if self.sheet_name in workbook.sheetnames:
            return workbook[self.sheet_name]
        return workbook.create_sheet(self.sheet_name)

    @staticmethod
    def _reset_worksheet(worksheet: Worksheet) -> None:
        """Clear existing reference data content."""
        for merged_range in list(worksheet.merged_cells.ranges):
            worksheet.unmerge_cells(str(merged_range))
        if worksheet.max_row:
            worksheet.delete_rows(1, worksheet.max_row)
        worksheet.conditional_formatting._cf_rules.clear()

    def _configure_worksheet(self, worksheet: Worksheet) -> None:
        """Apply reference registry layout and protection settings."""
        worksheet.sheet_view.showGridLines = False
        worksheet.freeze_panes = "A4"
        worksheet.sheet_properties.tabColor = self.theme.palette.amber
        worksheet.protection.sheet = True
        worksheet.protection.enable()

    def _write_title(self, worksheet: Worksheet) -> None:
        """Write reference data instructions."""
        worksheet.merge_cells("A1:BO1")
        title_cell = worksheet["A1"]
        title_cell.value = "Reference Data - Governed Dropdown Lists"
        title_cell.font = Font(
            name="Calibri Light",
            size=20,
            bold=True,
            color=self.theme.palette.white,
        )
        title_cell.fill = PatternFill("solid", fgColor=self.theme.palette.navy)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        worksheet.merge_cells("A2:BO2")
        note_cell = worksheet["A2"]
        note_cell.value = (
            "Use this sheet to manage dropdown values. If Deletion Status says "
            "'Assigned to VM - must not delete', remove or reassign the VM first."
        )
        note_cell.font = Font(name="Calibri", size=11, color=self.theme.palette.navy)
        note_cell.fill = PatternFill("solid", fgColor=self.theme.palette.light_blue)
        note_cell.alignment = Alignment(horizontal="center", vertical="center")

    def _write_reference_list(
        self,
        worksheet: Worksheet,
        reference_list: ReferenceList,
    ) -> None:
        """Write one governed reference list block."""
        col = reference_list.start_column
        headers = (reference_list.title, "Assigned Count", "Deletion Status")
        for offset, header in enumerate(headers):
            cell = worksheet.cell(row=3, column=col + offset, value=header)
            self._apply_named_style(cell, self.header)

        for row_index in range(4, REFERENCE_MAX_ROW + 1):
            value_index = row_index - 4
            value = (
                reference_list.values[value_index]
                if value_index < len(reference_list.values)
                else ""
            )
            value_cell = worksheet.cell(row=row_index, column=col, value=value)
            value_cell.protection = Protection(locked=False)
            self._apply_named_style(value_cell, self.table["table_body"])

            count_cell = worksheet.cell(row=row_index, column=col + 1)
            status_cell = worksheet.cell(row=row_index, column=col + 2)
            count_cell.value = self._assignment_formula(
                reference_list,
                value_cell.coordinate,
            )
            status_cell.value = (
                f'=IF({value_cell.coordinate}="","",'
                f'IF({count_cell.coordinate}>0,'
                '"Assigned to VM - must not delete","Safe to delete"))'
            )
            self._apply_named_style(count_cell, self.table["table_numeric"])
            self._apply_named_style(status_cell, self.table["table_body"])

        for offset in range(3):
            worksheet.column_dimensions[
                worksheet.cell(row=3, column=col + offset).column_letter
            ].width = 26 if offset != 1 else 16

    def _assignment_formula(
        self,
        reference_list: ReferenceList,
        value_coordinate: str,
    ) -> str:
        """Return the assignment-count formula for a reference row."""
        if reference_list.assignment_formula is None:
            return "=0"

        vm_column_map = {
            "Hosts": "Host",
            "Clusters": "Cluster",
            "Datastores": "Datastore",
            "VLANs": "VLAN",
            "Backup Jobs": "Backup Job",
            "Folders": "Folder",
            "Resource Pools": "Resource Pool",
            "Owners": "Owner",
            "Business Units": "Business Unit",
            "Management Servers": "Management Server",
            "Datacenters": "Datacenter",
            "Port Groups": "Port Group",
            "Distributed Switches": "Distributed Switch",
            "Security Zones": "Security Zone",
            "Support Groups": "Support Group",
            "VM Names": "VM Name",
        }
        vm_col = ""
        if reference_list.title in vm_column_map:
            vm_col = _vm_column_letter(vm_column_map[reference_list.title])
        return reference_list.assignment_formula.format(
            cell=value_coordinate,
            vm_col=vm_col,
        )

    @staticmethod
    def _create_defined_name(
        workbook: Workbook,
        reference_list: ReferenceList,
    ) -> None:
        """Create or replace a workbook-level defined name for dropdowns."""
        if reference_list.defined_name in workbook.defined_names:
            del workbook.defined_names[reference_list.defined_name]
        column_letter = _column_letter(reference_list.start_column)
        attr_text = LIVE_SOURCE_RANGES.get(
            reference_list.defined_name,
            (
                f"'{REFERENCE_SHEET_NAME}'!"
                f"${column_letter}$4:${column_letter}${REFERENCE_MAX_ROW}"
            ),
        )
        workbook.defined_names.add(
            DefinedName(reference_list.defined_name, attr_text=attr_text)
        )

    @staticmethod
    def _apply_conditional_formatting(worksheet: Worksheet) -> None:
        """Highlight references that are still assigned to VMs."""
        for reference_list in REFERENCE_LISTS:
            status_col = _column_letter(reference_list.start_column + 2)
            worksheet.conditional_formatting.add(
                f"{status_col}4:{status_col}{REFERENCE_MAX_ROW}",
                CellIsRule(
                    operator="equal",
                    formula=['"Assigned to VM - must not delete"'],
                    fill=PatternFill("solid", fgColor="F4CCCC"),
                    font=Font(color="9C0006", bold=True),
                ),
            )
            worksheet.conditional_formatting.add(
                f"{status_col}4:{status_col}{REFERENCE_MAX_ROW}",
                CellIsRule(
                    operator="equal",
                    formula=['"Safe to delete"'],
                    fill=PatternFill("solid", fgColor="E2F0D9"),
                    font=Font(color="006100", bold=True),
                ),
            )

    @staticmethod
    def _apply_named_style(cell: Cell, named_style: Any) -> None:
        """Copy a named style's visual attributes onto a cell."""
        cell.font = copy(named_style.font)
        cell.fill = copy(named_style.fill)
        cell.border = copy(named_style.border)
        cell.alignment = copy(named_style.alignment)
        cell.number_format = named_style.number_format


def _column_letter(column_index: int) -> str:
    """Return an Excel column letter for a one-based column index."""
    column_letter = ""
    while column_index:
        column_index, remainder = divmod(column_index - 1, 26)
        column_letter = chr(65 + remainder) + column_letter
    return column_letter


