"""Application entry point for Virtualization Administration Toolkit."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from src.backup import BackupWorksheet
from src.capacity import CapacityWorksheet
from src.cover import CoverMetadata, CoverWorksheet
from src.dashboard import DashboardWorksheet
from src.datastore import DatastoreWorksheet
from src.host_inventory import HostInventoryWorksheet
from src.instructions import InstructionsWorksheet
from src.license import LicenseWorksheet
from src.reference_data import ReferenceDataWorksheet
from src.snapshot import SnapshotWorksheet
from src.vm_inventory import VirtualMachineInventoryWorksheet


OUTPUT_FILE_NAME = "Premium_Virtualization_Administration_Toolkit.xlsx"


class VirtualizationAdministrationToolkit:
    """Coordinates workbook creation for the Virtualization Administration Toolkit."""

    def __init__(
        self,
        project_root: Path | None = None,
        *,
        cover_metadata: CoverMetadata | None = None,
        vm_records: list | None = None,
        host_records: list | None = None,
        datastore_records: list | None = None,
        backup_records: list | None = None,
        snapshot_records: list | None = None,
        capacity_records: list | None = None,
    ) -> None:
        """Initialize application paths."""
        self.project_root = project_root or Path(__file__).resolve().parent
        self.output_dir = self.project_root / "output"
        self.output_path = self.output_dir / OUTPUT_FILE_NAME
        self.cover_metadata = cover_metadata
        self.vm_records = vm_records
        self.host_records = host_records
        self.datastore_records = datastore_records
        self.backup_records = backup_records
        self.snapshot_records = snapshot_records
        self.capacity_records = capacity_records

    def run(self) -> None:
        """Create, save, and verify the virtualization administration workbook."""
        workbook = Workbook()
        self._configure_calculation(workbook)
        self._remove_default_sheet(workbook)
        self._build_worksheets(workbook)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        workbook.save(self.output_path)
        self._verify_workbook_created()
        print("Workbook created successfully.")

    @staticmethod
    def _remove_default_sheet(workbook: Workbook) -> None:
        """Remove the default openpyxl worksheet."""
        for worksheet in list(workbook.worksheets):
            workbook.remove(worksheet)

    @staticmethod
    def _configure_calculation(workbook: Workbook) -> None:
        """Force Excel to calculate formulas when the workbook opens."""
        workbook.calculation.calcMode = "auto"
        workbook.calculation.fullCalcOnLoad = True
        workbook.calculation.forceFullCalc = True

    def _build_worksheets(self, workbook: Workbook) -> None:
        """Create every worksheet in the workbook."""
        worksheet_builders = (
            CoverWorksheet(metadata=self.cover_metadata),
            InstructionsWorksheet(),
            ReferenceDataWorksheet(),
            DashboardWorksheet(),
            VirtualMachineInventoryWorksheet(records=self.vm_records),
            HostInventoryWorksheet(records=self.host_records),
            DatastoreWorksheet(records=self.datastore_records),
            CapacityWorksheet(records=self.capacity_records),
            SnapshotWorksheet(records=self.snapshot_records),
            BackupWorksheet(records=self.backup_records),
            LicenseWorksheet(),
        )
        for builder in worksheet_builders:
            builder.build(workbook)

    def _verify_workbook_created(self) -> None:
        """Verify the expected workbook exists on disk."""
        if not self.output_path.exists():
            raise FileNotFoundError(f"Workbook was not created: {self.output_path}")


def main() -> None:
    """Run the workbook generator application."""
    VirtualizationAdministrationToolkit().run()




if __name__ == "__main__":
    main()
