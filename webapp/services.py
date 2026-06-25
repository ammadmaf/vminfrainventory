"""Business services for inventory, references, and governance rules."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from typing import Any
from urllib.parse import urlparse

from werkzeug.security import check_password_hash, generate_password_hash

from src.backup import BackupRecord
from src.capacity import CapacityRecord
from src.cover import CoverMetadata
from src.datastore import DatastoreRecord
from src.host_inventory import HostRecord
from src.snapshot import SnapshotRecord
from src.vm_inventory import VirtualMachineRecord, _enterprise_field_values

from .database import get_db, row_to_dict


RESOURCE_TABLES = {
    "clusters": "clusters",
    "environments": "environments",
    "hosts": "hosts",
    "datastores": "datastores",
    "vlans": "vlans",
    "backup_jobs": "backup_jobs",
    "vms": "vms",
}


DELETE_GUARDS = {
    "environments": (
        ("clusters", "environment", "cluster"),
        ("vms", "environment", "VM"),
    ),
    "clusters": (
        ("hosts", "cluster_id", "host"),
        ("datastores", "cluster_id", "datastore"),
        ("vms", "cluster_id", "VM"),
    ),
    "hosts": (("vms", "host_id", "VM"),),
    "datastores": (("vms", "datastore_id", "VM"),),
    "vlans": (("vms", "vlan_id", "VM"),),
    "backup_jobs": (("vms", "backup_job_id", "VM"),),
}

UPDATE_FIELDS = {
    "clusters": ("name", "environment", "status", "notes"),
    "environments": ("name", "status", "notes"),
    "hosts": (
        "hostname",
        "cluster_id",
        "version",
        "build",
        "cpu",
        "memory",
        "nics",
        "management_ip",
        "license",
        "health",
        "notes",
    ),
    "datastores": (
        "name",
        "datastore_type",
        "cluster_id",
        "capacity_gb",
        "used_gb",
        "notes",
    ),
    "vlans": ("name", "cidr", "security_zone", "notes"),
    "backup_jobs": ("name", "schedule", "repository", "retention", "status"),
    "vms": (
        "name",
        "description",
        "environment",
        "business_unit",
        "owner",
        "application",
        "operating_system",
        "host_id",
        "cluster_id",
        "datastore_id",
        "folder",
        "resource_pool",
        "vcpu",
        "ram_gb",
        "disk_gb",
        "ip_address",
        "vlan_id",
        "backup_enabled",
        "backup_job_id",
        "snapshot",
        "guest_tools",
        "power_state",
        "criticality",
        "notes",
    ),
}

INTEGER_FIELDS = {
    "backup_job_id",
    "capacity_gb",
    "cluster_id",
    "datastore_id",
    "disk_gb",
    "host_id",
    "nics",
    "ram_gb",
    "used_gb",
    "vcpus",
    "vcpu",
    "vlan_id",
}

FILTER_TARGETS = {
    "vms",
    "hosts",
    "datastores",
    "vlans",
    "backup_jobs",
    "clusters",
    "environments",
}

BRANDING_DEFAULTS = {
    "company_name": "Virtualization Administration Toolkit",
    "tagline": (
        "Secure enterprise console for governed VM, host, datastore, backup, "
        "and access administration."
    ),
    "logo_url": "",
    "report_title": "Infrastructure Overview Report",
    "report_author": "Infrastructure Admin",
}

BRANDING_LIMITS = {
    "company_name": 80,
    "tagline": 180,
    "logo_url": 500,
    "report_title": 100,
    "report_author": 80,
}


def get_dashboard_summary() -> dict[str, Any]:
    """Return executive dashboard metrics and resource utilization."""
    db = get_db()
    counts = {
        "total_vms": _scalar("SELECT COUNT(*) FROM vms"),
        "production_vms": _scalar(
            "SELECT COUNT(*) FROM vms WHERE environment = 'Production'"
        ),
        "powered_on": _scalar(
            "SELECT COUNT(*) FROM vms WHERE power_state = 'Powered On'"
        ),
        "powered_off": _scalar(
            "SELECT COUNT(*) FROM vms WHERE power_state = 'Powered Off'"
        ),
        "snapshots": _scalar("SELECT COUNT(*) FROM vms WHERE snapshot = 'Yes'"),
        "critical": _scalar(
            "SELECT COUNT(*) FROM vms WHERE criticality = 'Critical'"
        ),
        "hosts": _scalar("SELECT COUNT(*) FROM hosts"),
        "datastores": _scalar("SELECT COUNT(*) FROM datastores"),
        "backup_enabled": _scalar(
            "SELECT COUNT(*) FROM vms WHERE backup_enabled = 1"
        ),
        "backup_disabled": _scalar(
            "SELECT COUNT(*) FROM vms WHERE backup_enabled = 0"
        ),
        "windows_vms": _scalar(
            "SELECT COUNT(*) FROM vms WHERE operating_system LIKE '%Windows%'"
        ),
        "linux_vms": _scalar(
            """
            SELECT COUNT(*)
            FROM vms
            WHERE operating_system LIKE '%Linux%'
               OR operating_system LIKE '%Ubuntu%'
               OR operating_system LIKE '%Red Hat%'
               OR operating_system LIKE '%Photon%'
            """
        ),
        "other_vms": _scalar(
            """
            SELECT COUNT(*)
            FROM vms
            WHERE COALESCE(operating_system, '') NOT LIKE '%Windows%'
              AND COALESCE(operating_system, '') NOT LIKE '%Linux%'
              AND COALESCE(operating_system, '') NOT LIKE '%Ubuntu%'
              AND COALESCE(operating_system, '') NOT LIKE '%Red Hat%'
              AND COALESCE(operating_system, '') NOT LIKE '%Photon%'
            """
        ),
    }
    utilization = db.execute(
        """
        SELECT
            COALESCE(SUM(capacity_gb), 0) AS capacity_gb,
            COALESCE(SUM(used_gb), 0) AS used_gb
        FROM datastores
        """
    ).fetchone()
    capacity = utilization["capacity_gb"] or 0
    used = utilization["used_gb"] or 0
    counts["storage_used_percent"] = round((used / capacity) * 100, 1) if capacity else 0
    counts["storage_capacity_gb"] = capacity
    counts["storage_used_gb"] = used
    counts["environment_distribution"] = _distribution(
        """
        SELECT environment AS name, COUNT(*) AS count
        FROM vms
        GROUP BY environment
        ORDER BY count DESC, environment
        """
    )
    counts["power_distribution"] = _distribution(
        """
        SELECT power_state AS name, COUNT(*) AS count
        FROM vms
        GROUP BY power_state
        ORDER BY count DESC, power_state
        """
    )
    counts["os_distribution"] = _distribution(
        """
        SELECT name, COUNT(*) AS count
        FROM (
            SELECT
                CASE
                    WHEN operating_system LIKE '%Windows%' THEN 'Windows'
                    WHEN operating_system LIKE '%Linux%'
                      OR operating_system LIKE '%Ubuntu%'
                      OR operating_system LIKE '%Red Hat%'
                      OR operating_system LIKE '%Photon%' THEN 'Linux'
                    ELSE 'Other'
                END AS name
            FROM vms
        )
        GROUP BY name
        ORDER BY count DESC, name
        """
    )
    counts["os_inventory"] = _select_options(
        """
        SELECT
            vms.operating_system AS name,
            COUNT(vms.id) AS vm_count
        FROM vms
        GROUP BY vms.operating_system
        ORDER BY vm_count DESC, vms.operating_system
        """
    )
    counts["backup_distribution"] = _distribution(
        """
        SELECT name, COUNT(*) AS count
        FROM (
            SELECT
                CASE
                    WHEN backup_enabled = 1 THEN 'Enabled'
                    ELSE 'Disabled'
                END AS name
            FROM vms
        )
        GROUP BY name
        ORDER BY count DESC, name
        """
    )
    counts["criticality_distribution"] = _distribution(
        """
        SELECT criticality AS name, COUNT(*) AS count
        FROM vms
        GROUP BY criticality
        ORDER BY count DESC, criticality
        """
    )
    counts["storage_by_datastore"] = _select_options(
        """
        SELECT
            name,
            capacity_gb,
            used_gb,
            ROUND((used_gb * 100.0) / NULLIF(capacity_gb, 0), 1) AS used_percent
        FROM datastores
        ORDER BY used_percent DESC, name
        LIMIT 8
        """
    )
    counts["recent_vms"] = _select_options(
        """
        SELECT
            vms.name,
            vms.environment,
            vms.power_state,
            vms.criticality,
            hosts.hostname,
            datastores.name AS datastore_name
        FROM vms
        JOIN hosts ON hosts.id = vms.host_id
        JOIN datastores ON datastores.id = vms.datastore_id
        ORDER BY vms.id DESC
        LIMIT 8
        """
    )
    counts["risk_warnings"] = _dashboard_warnings()
    return counts


def get_branding_settings() -> dict[str, str]:
    """Return company branding settings for the web UI and workbook."""
    rows = get_db().execute(
        """
        SELECT key, value
        FROM app_settings
        WHERE key IN (
            'company_name',
            'tagline',
            'logo_url',
            'report_title',
            'report_author'
        )
        """
    ).fetchall()
    branding = dict(BRANDING_DEFAULTS)
    branding.update({row["key"]: row["value"] for row in rows})
    return branding


def update_branding_settings(payload: dict[str, Any], actor: str) -> dict[str, str]:
    """Validate and persist company branding settings."""
    branding = dict(get_branding_settings())
    for key in BRANDING_DEFAULTS:
        value = str(payload.get(key, branding[key]) or "").strip()
        if key in {"company_name", "report_title"} and not value:
            raise ValueError(f"{key.replace('_', ' ').title()} is required.")
        if key == "logo_url" and value:
            _validate_logo_url(value)
        branding[key] = value[:BRANDING_LIMITS[key]]

    db = get_db()
    db.executemany(
        """
        INSERT INTO app_settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        [(key, value) for key, value in branding.items()],
    )
    _audit(db, actor, "updated", "app_settings", "branding")
    db.commit()
    return branding


def workbook_export_context() -> dict[str, Any]:
    """Build live workbook data from the web-console database."""
    branding = get_branding_settings()
    return {
        "cover_metadata": CoverMetadata(
            title=branding["report_title"],
            subtitle=branding["tagline"],
            author=f"Author: {branding['report_author']}",
            company=f"Company: {branding['company_name']}",
            footer=f"(c) 2026 {branding['company_name']}. All rights reserved.",
            brand_band=branding["company_name"].upper(),
        ),
        "vm_records": workbook_vm_records(),
        "host_records": workbook_host_records(),
        "datastore_records": workbook_datastore_records(),
        "backup_records": workbook_backup_records(),
        "snapshot_records": workbook_snapshot_records(),
        "capacity_records": workbook_capacity_records(),
    }


def workbook_vm_records() -> list[VirtualMachineRecord]:
    """Return live VM inventory rows for the Excel workbook."""
    rows = get_db().execute(
        """
        SELECT vms.*, hosts.hostname, clusters.name AS cluster_name,
               datastores.name AS datastore_name,
               datastores.capacity_gb AS datastore_capacity_gb,
               datastores.used_gb AS datastore_used_gb,
               vlans.name AS vlan_name,
               backup_jobs.name AS backup_job_name
        FROM vms
        JOIN hosts ON hosts.id = vms.host_id
        JOIN clusters ON clusters.id = vms.cluster_id
        JOIN datastores ON datastores.id = vms.datastore_id
        JOIN vlans ON vlans.id = vms.vlan_id
        LEFT JOIN backup_jobs ON backup_jobs.id = vms.backup_job_id
        ORDER BY vms.name
        """
    ).fetchall()
    records = []
    for row in rows:
        backup_name = row["backup_job_name"] or "Not Assigned"
        records.append(
            VirtualMachineRecord(
                vm_name=row["name"],
                description=row["description"],
                environment=row["environment"],
                business_unit=row["business_unit"],
                owner=row["owner"],
                application=row["application"],
                operating_system=row["operating_system"],
                host=row["hostname"],
                cluster=row["cluster_name"],
                datastore=row["datastore_name"],
                folder=row["folder"],
                resource_pool=row["resource_pool"],
                vcpu=row["vcpu"],
                ram_gb=row["ram_gb"],
                disk_gb=row["disk_gb"],
                ip_address=row["ip_address"],
                vlan=row["vlan_name"],
                backup="Yes" if row["backup_enabled"] else "No",
                backup_job=backup_name,
                snapshot=row["snapshot"],
                guest_tools=row["guest_tools"],
                power_state=row["power_state"],
                provision_date="",
                last_patch_date="",
                criticality=row["criticality"],
                notes=row["notes"],
                enterprise_fields=_enterprise_field_values(
                    **{
                        "Management Server": "Web Console",
                        "Datacenter": row["environment"],
                        "Guest Hostname": row["hostname"],
                        "FQDN": row["hostname"],
                        "Guest OS Version": row["operating_system"],
                        "CPU Sockets": max(1, int(row["vcpu"] or 1)),
                        "Cores per Socket": 1,
                        "Provisioned Disk (GB)": row["disk_gb"],
                        "Used Disk (GB)": "",
                        "Free Disk (GB)": "",
                        "Storage Policy": row["datastore_name"],
                        "Storage Tier": row["environment"],
                        "VLAN ID": row["vlan_name"],
                        "Last Backup Date": "",
                        "Last Backup Status": "Success" if row["backup_enabled"] else "Not Configured",
                        "Backup Repository": backup_name,
                        "Backup Policy": backup_name,
                        "Snapshot Count": 1 if row["snapshot"] == "Yes" else 0,
                        "Patch Group": row["environment"],
                        "Security Zone": row["vlan_name"],
                        "Owner Email": "",
                        "Support Group": row["owner"],
                    }
                ),
            )
        )
    return records


def workbook_host_records() -> list[HostRecord]:
    """Return live host rows for workbook export."""
    rows = get_db().execute(
        """
        SELECT hosts.*, clusters.name AS cluster_name,
               COUNT(DISTINCT vms.id) AS vm_count,
               COALESCE(GROUP_CONCAT(DISTINCT datastores.name), '') AS datastore_names
        FROM hosts
        JOIN clusters ON clusters.id = hosts.cluster_id
        LEFT JOIN vms ON vms.host_id = hosts.id
        LEFT JOIN datastores ON datastores.cluster_id = hosts.cluster_id
        GROUP BY hosts.id
        ORDER BY hosts.hostname
        """
    ).fetchall()
    return [
        HostRecord(
            hostname=row["hostname"],
            version=row["version"],
            build=row["build"],
            cpu=row["cpu"],
            memory=row["memory"],
            nics=row["nics"],
            vm_count=row["vm_count"],
            datastores=row["datastore_names"],
            cluster=row["cluster_name"],
            management_ip=row["management_ip"],
            license=row["license"],
            health=row["health"],
            notes=row["notes"],
        )
        for row in rows
    ]


def workbook_datastore_records() -> list[DatastoreRecord]:
    """Return live datastore rows for workbook export."""
    rows = get_db().execute(
        """
        SELECT datastores.*, clusters.name AS cluster_name
        FROM datastores
        JOIN clusters ON clusters.id = datastores.cluster_id
        ORDER BY datastores.name
        """
    ).fetchall()
    return [
        DatastoreRecord(
            datastore=row["name"],
            datastore_type=row["datastore_type"],
            cluster=row["cluster_name"],
            capacity_gb=row["capacity_gb"],
            used_gb=row["used_gb"],
            notes=row["notes"],
        )
        for row in rows
    ]


def workbook_backup_records() -> list[BackupRecord]:
    """Return live backup-job rows for workbook export."""
    rows = get_db().execute(
        """
        SELECT backup_jobs.*,
               COUNT(vms.id) AS protected_vms
        FROM backup_jobs
        LEFT JOIN vms ON vms.backup_job_id = backup_jobs.id
                   AND vms.backup_enabled = 1
        GROUP BY backup_jobs.id
        ORDER BY backup_jobs.name
        """
    ).fetchall()
    return [
        BackupRecord(
            backup_job=row["name"],
            schedule=row["schedule"],
            repository=row["repository"],
            retention=row["retention"],
            last_backup="",
            status=row["status"],
            successful_runs=1 if row["status"] == "Success" else 0,
            total_runs=1,
            restore_test="Pending",
            restore_test_date="",
            protected_vms=row["protected_vms"],
            owner="Infrastructure Operations",
            notes="Live export from web console",
        )
        for row in rows
    ]


def workbook_snapshot_records() -> list[SnapshotRecord]:
    """Return live snapshot rows for workbook export."""
    rows = get_db().execute(
        """
        SELECT name, description, notes
        FROM vms
        WHERE snapshot = 'Yes'
        ORDER BY name
        """
    ).fetchall()
    return [
        SnapshotRecord(
            vm_name=row["name"],
            snapshot_name=f"{row['name']}-snapshot",
            created_date=date.today(),
            created_by="Web Console",
            size_gb=0,
            description=row["description"] or "Snapshot recorded in VM inventory",
            notes=row["notes"],
        )
        for row in rows
    ]


def workbook_capacity_records() -> list[CapacityRecord]:
    """Return cluster-level capacity rows based on live hosts, VMs, and datastores."""
    rows = get_db().execute(
        """
        SELECT clusters.name,
               COUNT(DISTINCT hosts.id) AS host_count,
               COALESCE((
                   SELECT SUM(datastores.capacity_gb)
                   FROM datastores
                   WHERE datastores.cluster_id = clusters.id
               ), 0) AS storage_capacity_gb,
               COALESCE((
                   SELECT SUM(datastores.used_gb)
                   FROM datastores
                   WHERE datastores.cluster_id = clusters.id
               ), 0) AS storage_used_gb,
               COALESCE((
                   SELECT SUM(vms.vcpu)
                   FROM vms
                   WHERE vms.cluster_id = clusters.id
               ), 0) AS vcpu_used,
               COALESCE((
                   SELECT SUM(vms.ram_gb)
                   FROM vms
                   WHERE vms.cluster_id = clusters.id
               ), 0) AS memory_used_gb,
               COALESCE(GROUP_CONCAT(hosts.memory), '') AS host_memory
        FROM clusters
        LEFT JOIN hosts ON hosts.cluster_id = clusters.id
        GROUP BY clusters.id
        ORDER BY clusters.name
        """
    ).fetchall()
    records = []
    for row in rows:
        host_count = row["host_count"] or 0
        memory_capacity = _memory_capacity_gb(row["host_memory"])
        if memory_capacity == 0:
            memory_capacity = host_count * 512
        cpu_capacity = max(host_count * 128, int(row["vcpu_used"] or 0), 1)
        records.append(
            CapacityRecord(
                cluster=row["name"],
                cpu_capacity_ghz=cpu_capacity,
                cpu_used_ghz=int(row["vcpu_used"] or 0) * 2,
                memory_capacity_gb=memory_capacity,
                memory_used_gb=int(row["memory_used_gb"] or 0),
                storage_capacity_tb=round((row["storage_capacity_gb"] or 0) / 1024, 2),
                storage_used_tb=round((row["storage_used_gb"] or 0) / 1024, 2),
                growth_percent=0.15,
            )
        )
    return records


def get_reference_options() -> dict[str, list[dict[str, Any]]]:
    """Return live dropdown values from the source tables."""
    db = get_db()
    return {
        "clusters": _select_options(
            "SELECT id, name AS label, environment FROM clusters ORDER BY name"
        ),
        "environments": _select_options(
            "SELECT id, name AS label, status FROM environments ORDER BY name"
        ),
        "hosts": _select_options(
            """
            SELECT hosts.id, hosts.hostname AS label, clusters.name AS cluster
            FROM hosts
            JOIN clusters ON clusters.id = hosts.cluster_id
            ORDER BY hosts.hostname
            """
        ),
        "datastores": _select_options(
            """
            SELECT datastores.id, datastores.name AS label, clusters.name AS cluster
            FROM datastores
            JOIN clusters ON clusters.id = datastores.cluster_id
            ORDER BY datastores.name
            """
        ),
        "vlans": _select_options(
            "SELECT id, name AS label, security_zone FROM vlans ORDER BY name"
        ),
        "backup_jobs": _select_options(
            "SELECT id, name AS label, repository FROM backup_jobs ORDER BY name"
        ),
    }


def get_user_permissions(user_id: int) -> set[str]:
    """Return explicit permissions assigned to a user."""
    rows = get_db().execute(
        """
        SELECT permission_code
        FROM user_permissions
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchall()
    return {row["permission_code"] for row in rows}


def has_permission(user: dict[str, Any], permission_code: str) -> bool:
    """Return whether a user has a permission.

    Administrators are superusers. Client users only receive rights that are
    explicitly assigned in the admin panel.
    """
    if user["role"] == "admin":
        return True
    return permission_code in set(user.get("permissions", []))


def list_permissions() -> list[dict[str, Any]]:
    """Return assignable permissions for the admin panel."""
    rows = get_db().execute(
        "SELECT code, label, description FROM permissions ORDER BY code"
    ).fetchall()
    return [dict(row) for row in rows]


def list_users() -> list[dict[str, Any]]:
    """Return users and their assigned permissions."""
    db = get_db()
    users = [dict(row) for row in db.execute(
        """
        SELECT id, username, display_name, role
        FROM users
        ORDER BY role, username
        """
    ).fetchall()]
    for user in users:
        user["permissions"] = sorted(get_user_permissions(user["id"]))
    return users


def create_user(payload: dict[str, Any], actor: str) -> dict[str, Any]:
    """Create a read-only user account by default."""
    db = get_db()
    role = payload.get("role", "client")
    if role not in {"client", "admin"}:
        raise ValueError("Role must be admin or client.")
    new_password = _validated_password(payload.get("password", ""))
    db.execute(
        """
        INSERT INTO users (username, display_name, role, password_hash)
        VALUES (?, ?, ?, ?)
        """,
        (
            payload["username"].strip(),
            payload.get("display_name", payload["username"]).strip(),
            role,
            generate_password_hash(new_password),
        ),
    )
    created = row_to_dict(
        db.execute(
            """
            SELECT id, username, display_name, role
            FROM users
            WHERE username = ?
            """,
            (payload["username"].strip(),),
        ).fetchone()
    )
    _audit(db, actor, "created", "users", created["username"])
    db.commit()
    created["permissions"] = []
    return created


def set_user_permissions(
    user_id: int,
    permissions: list[str],
    actor: str,
) -> dict[str, Any]:
    """Replace a user's explicit permission grants."""
    db = get_db()
    user = row_to_dict(
        db.execute(
            """
            SELECT id, username, display_name, role
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    )
    if user is None:
        raise ValueError("User not found.")

    valid_permissions = {permission["code"] for permission in list_permissions()}
    requested_permissions = set(permissions)
    invalid_permissions = requested_permissions - valid_permissions
    if invalid_permissions:
        raise ValueError(
            "Invalid permission(s): " + ", ".join(sorted(invalid_permissions))
        )

    db.execute("DELETE FROM user_permissions WHERE user_id = ?", (user_id,))
    db.executemany(
        """
        INSERT INTO user_permissions (user_id, permission_code)
        VALUES (?, ?)
        """,
        [(user_id, code) for code in sorted(requested_permissions)],
    )
    _audit(db, actor, "updated permissions", "users", user["username"])
    db.commit()
    user["permissions"] = sorted(requested_permissions)
    return user


def change_own_password(
    user_id: int,
    current_password: str,
    new_password: str,
    actor: str,
) -> dict[str, str]:
    """Change the current user's password after verifying the old password."""
    db = get_db()
    user = row_to_dict(
        db.execute(
            "SELECT id, username, password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    )
    if user is None:
        raise ValueError("User not found.")
    if not check_password_hash(user["password_hash"], current_password or ""):
        raise ValueError("Current password is incorrect.")

    clean_password = _validated_password(new_password)
    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(clean_password), user_id),
    )
    _audit(db, actor, "changed password", "users", user["username"])
    db.commit()
    return {"message": "Password updated."}


def reset_user_password(
    user_id: int,
    new_password: str,
    actor: str,
) -> dict[str, str]:
    """Reset a user's password from the admin panel."""
    db = get_db()
    user = row_to_dict(
        db.execute(
            "SELECT id, username FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    )
    if user is None:
        raise ValueError("User not found.")

    clean_password = _validated_password(new_password)
    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(clean_password), user_id),
    )
    _audit(db, actor, "reset password", "users", user["username"])
    db.commit()
    return {"message": f"Password reset for {user['username']}."}


def list_user_filters(user_id: int) -> list[dict[str, Any]]:
    """Return saved quick filters for the current user."""
    rows = get_db().execute(
        """
        SELECT id, label, target_view, search_term, created_at
        FROM user_filters
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def create_user_filter(
    user_id: int,
    payload: dict[str, Any],
    actor: str,
) -> dict[str, Any]:
    """Create a user-owned quick filter."""
    label = str(payload.get("label", "")).strip()
    target_view = str(payload.get("target_view", "")).strip()
    search_term = str(payload.get("search_term", "")).strip()
    if not label:
        raise ValueError("Filter label is required.")
    if target_view not in FILTER_TARGETS:
        raise ValueError("Choose a valid filter target.")
    if not search_term:
        raise ValueError("Filter search term is required.")

    db = get_db()
    created = row_to_dict(db.execute(
        """
        INSERT INTO user_filters (user_id, label, target_view, search_term)
        VALUES (?, ?, ?, ?)
        RETURNING id, label, target_view, search_term, created_at
        """,
        (user_id, label[:40], target_view, search_term[:80]),
    ).fetchone())
    _audit(db, actor, "created filter", "user_filters", created["label"])
    db.commit()
    return created


def delete_user_filter(filter_id: int, user_id: int, actor: str) -> dict[str, Any]:
    """Delete a saved filter owned by the current user."""
    db = get_db()
    row = db.execute(
        """
        SELECT label
        FROM user_filters
        WHERE id = ? AND user_id = ?
        """,
        (filter_id, user_id),
    ).fetchone()
    if row is None:
        raise ValueError("Filter not found.")
    db.execute(
        "DELETE FROM user_filters WHERE id = ? AND user_id = ?",
        (filter_id, user_id),
    )
    _audit(db, actor, "deleted filter", "user_filters", row["label"])
    db.commit()
    return {"deleted": True, "message": f"{row['label']} filter removed."}


def list_resource(resource: str) -> list[dict[str, Any]]:
    """List a managed resource type."""
    _validate_resource(resource)
    query_map = {
        "clusters": """
            SELECT clusters.*,
                   COUNT(DISTINCT hosts.id) AS host_count,
                   COUNT(DISTINCT vms.id) AS vm_count,
                   COUNT(DISTINCT datastores.id) AS datastore_count,
                   COALESCE(GROUP_CONCAT(DISTINCT hosts.hostname), 'No hosts')
                   AS host_names
            FROM clusters
            LEFT JOIN hosts ON hosts.cluster_id = clusters.id
            LEFT JOIN vms ON vms.cluster_id = clusters.id
            LEFT JOIN datastores ON datastores.cluster_id = clusters.id
            GROUP BY clusters.id
            ORDER BY clusters.environment, clusters.name
        """,
        "environments": """
            SELECT environments.*,
                   COUNT(DISTINCT clusters.id) AS cluster_count,
                   COUNT(DISTINCT vms.id) AS vm_count
            FROM environments
            LEFT JOIN clusters ON clusters.environment = environments.name
            LEFT JOIN vms ON vms.environment = environments.name
            GROUP BY environments.id
            ORDER BY environments.name
        """,
        "hosts": """
            SELECT hosts.*, clusters.name AS cluster_name,
                   COUNT(vms.id) AS assigned_vm_count
            FROM hosts
            JOIN clusters ON clusters.id = hosts.cluster_id
            LEFT JOIN vms ON vms.host_id = hosts.id
            GROUP BY hosts.id
            ORDER BY hosts.hostname
        """,
        "datastores": """
            SELECT datastores.*, clusters.name AS cluster_name,
                   COUNT(vms.id) AS assigned_vm_count,
                   ROUND((used_gb * 100.0) / NULLIF(capacity_gb, 0), 1)
                   AS used_percent
            FROM datastores
            JOIN clusters ON clusters.id = datastores.cluster_id
            LEFT JOIN vms ON vms.datastore_id = datastores.id
            GROUP BY datastores.id
            ORDER BY datastores.name
        """,
        "vlans": """
            SELECT vlans.*, COUNT(vms.id) AS assigned_vm_count
            FROM vlans
            LEFT JOIN vms ON vms.vlan_id = vlans.id
            GROUP BY vlans.id
            ORDER BY vlans.name
        """,
        "backup_jobs": """
            SELECT backup_jobs.*, COUNT(vms.id) AS assigned_vm_count
            FROM backup_jobs
            LEFT JOIN vms ON vms.backup_job_id = backup_jobs.id
            GROUP BY backup_jobs.id
            ORDER BY backup_jobs.name
        """,
        "vms": """
            SELECT vms.*, hosts.hostname, clusters.name AS cluster_name,
                   datastores.name AS datastore_name, vlans.name AS vlan_name,
                   backup_jobs.name AS backup_job_name
            FROM vms
            JOIN hosts ON hosts.id = vms.host_id
            JOIN clusters ON clusters.id = vms.cluster_id
            JOIN datastores ON datastores.id = vms.datastore_id
            JOIN vlans ON vlans.id = vms.vlan_id
            LEFT JOIN backup_jobs ON backup_jobs.id = vms.backup_job_id
            ORDER BY vms.name
        """,
    }
    rows = get_db().execute(query_map[resource]).fetchall()
    return [dict(row) for row in rows]


def create_resource(resource: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    """Create a managed resource and write an audit event."""
    _validate_resource(resource)
    db = get_db()
    creators = {
        "clusters": _create_cluster,
        "environments": _create_environment,
        "hosts": _create_host,
        "datastores": _create_datastore,
        "vlans": _create_vlan,
        "backup_jobs": _create_backup_job,
        "vms": _create_vm,
    }
    created = creators[resource](db, payload)
    _audit(db, actor, "created", resource, created.get("name") or created.get("hostname"))
    db.commit()
    return created


def update_resource(
    resource: str,
    resource_id: int,
    payload: dict[str, Any],
    actor: str,
) -> dict[str, Any]:
    """Update an existing managed resource."""
    _validate_resource(resource)
    db = get_db()
    existing = _resource_row(resource, resource_id)
    if existing is None:
        raise ValueError("Resource not found.")

    if resource == "environments":
        return _update_environment(db, resource_id, payload, actor, existing)

    fields = [
        field for field in UPDATE_FIELDS[resource]
        if field in payload and payload[field] is not None
    ]
    if not fields:
        raise ValueError("No editable fields were provided.")

    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [_normalize_field_value(field, payload[field]) for field in fields]
    values.append(resource_id)
    db.execute(
        f"UPDATE {RESOURCE_TABLES[resource]} SET {assignments} WHERE id = ?",
        values,
    )
    display_name = _resource_name(resource, resource_id) or str(resource_id)
    _audit(db, actor, "updated", resource, display_name)
    db.commit()
    return _resource_row(resource, resource_id) or {}


def delete_resource(resource: str, resource_id: int, actor: str) -> dict[str, Any]:
    """Delete a resource when governance rules allow it."""
    _validate_resource(resource)
    if resource == "vms":
        return _delete_without_guard(resource, resource_id, actor)
    if resource == "environments":
        blockers = _environment_blockers(resource_id)
        if blockers:
            resource_name = _resource_name(resource, resource_id)
            detail = ", ".join(f"{count} {label}(s)" for label, count in blockers)
            return {
                "deleted": False,
                "status": 409,
                "message": (
                    f"{resource_name} is assigned to {detail} and must not be deleted."
                ),
            }
        return _delete_without_guard(resource, resource_id, actor)

    blockers = _assignment_blockers(resource, resource_id)
    if blockers:
        resource_name = _resource_name(resource, resource_id)
        detail = ", ".join(f"{count} {label}(s)" for label, count in blockers)
        return {
            "deleted": False,
            "status": 409,
            "message": (
                f"{resource_name} is assigned to {detail} and must not be deleted."
            ),
        }
    return _delete_without_guard(resource, resource_id, actor)


def _delete_without_guard(resource: str, resource_id: int, actor: str) -> dict[str, Any]:
    """Archive a resource to trash after validation has passed."""
    db = get_db()
    row = _resource_row(resource, resource_id)
    if row is None:
        return {"deleted": False, "status": 404, "message": "Resource not found."}

    resource_name = _display_name(resource, row)
    db.execute(
        """
        INSERT INTO trash_items (
            resource, resource_id, display_name, payload, deleted_by
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            resource,
            resource_id,
            resource_name,
            json.dumps(row),
            actor,
        ),
    )
    db.execute(f"DELETE FROM {RESOURCE_TABLES[resource]} WHERE id = ?", (resource_id,))
    _audit(db, actor, "moved to trash", resource, resource_name)
    db.commit()
    return {
        "deleted": True,
        "status": 200,
        "message": f"{resource_name} moved to Trash.",
    }


def list_trash() -> list[dict[str, Any]]:
    """Return recoverable deleted items."""
    rows = get_db().execute(
        """
        SELECT id, resource, resource_id, display_name, deleted_by, deleted_at
        FROM trash_items
        ORDER BY deleted_at DESC, id DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def restore_trash_item(trash_id: int, actor: str) -> dict[str, Any]:
    """Restore an item from the recycle bin."""
    db = get_db()
    trash_row = db.execute(
        "SELECT * FROM trash_items WHERE id = ?",
        (trash_id,),
    ).fetchone()
    if trash_row is None:
        return {"restored": False, "status": 404, "message": "Trash item not found."}

    resource = trash_row["resource"]
    _validate_resource(resource)
    payload = json.loads(trash_row["payload"])
    fields = list(payload.keys())
    placeholders = ", ".join("?" for _ in fields)
    columns = ", ".join(fields)
    values = [payload[field] for field in fields]
    db.execute(
        f"INSERT INTO {RESOURCE_TABLES[resource]} ({columns}) VALUES ({placeholders})",
        values,
    )
    db.execute("DELETE FROM trash_items WHERE id = ?", (trash_id,))
    _audit(db, actor, "restored", resource, trash_row["display_name"])
    db.commit()
    return {
        "restored": True,
        "status": 200,
        "message": f"{trash_row['display_name']} restored.",
    }


def _create_cluster(db: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_environment(db, payload.get("environment", "Production"))
    db.execute(
        """
        INSERT INTO clusters (name, environment, status, notes)
        VALUES (?, ?, ?, ?)
        """,
        (
            payload["name"],
            payload.get("environment", "Production"),
            payload.get("status", "Active"),
            payload.get("notes", ""),
        ),
    )
    return row_to_dict(db.execute("SELECT * FROM clusters WHERE name = ?", (payload["name"],)).fetchone())


def _create_environment(db: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    name = payload["name"].strip()
    db.execute(
        """
        INSERT INTO environments (name, status, notes)
        VALUES (?, ?, ?)
        """,
        (
            name,
            payload.get("status", "Active"),
            payload.get("notes", ""),
        ),
    )
    return row_to_dict(
        db.execute("SELECT * FROM environments WHERE name = ?", (name,)).fetchone()
    )


def _create_host(db: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    db.execute(
        """
        INSERT INTO hosts (
            hostname, cluster_id, version, build, cpu, memory, nics,
            management_ip, license, health, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["hostname"],
            int(payload["cluster_id"]),
            payload.get("version", "Generic Hypervisor 2026"),
            payload.get("build", "22380479"),
            payload.get("cpu", "2 x Intel Xeon, 32 cores"),
            payload.get("memory", "512 GB"),
            int(payload.get("nics", 4)),
            payload.get("management_ip", ""),
            payload.get("license", "Enterprise Plus"),
            payload.get("health", "Healthy"),
            payload.get("notes", ""),
        ),
    )
    return row_to_dict(db.execute("SELECT * FROM hosts WHERE hostname = ?", (payload["hostname"],)).fetchone())


def _create_datastore(db: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    db.execute(
        """
        INSERT INTO datastores (
            name, datastore_type, cluster_id, capacity_gb, used_gb, notes
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload["name"],
            payload.get("datastore_type", "VMFS"),
            int(payload["cluster_id"]),
            int(payload.get("capacity_gb", 1024)),
            int(payload.get("used_gb", 0)),
            payload.get("notes", ""),
        ),
    )
    return row_to_dict(db.execute("SELECT * FROM datastores WHERE name = ?", (payload["name"],)).fetchone())


def _create_vlan(db: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    db.execute(
        """
        INSERT INTO vlans (name, cidr, security_zone, notes)
        VALUES (?, ?, ?, ?)
        """,
        (
            payload["name"],
            payload.get("cidr", ""),
            payload.get("security_zone", "Internal"),
            payload.get("notes", ""),
        ),
    )
    return row_to_dict(db.execute("SELECT * FROM vlans WHERE name = ?", (payload["name"],)).fetchone())


def _create_backup_job(db: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    db.execute(
        """
        INSERT INTO backup_jobs (name, schedule, repository, retention, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            payload["name"],
            payload.get("schedule", "Daily 22:00"),
            payload.get("repository", "Repo-Primary"),
            payload.get("retention", "30 daily"),
            payload.get("status", "Success"),
        ),
    )
    return row_to_dict(db.execute("SELECT * FROM backup_jobs WHERE name = ?", (payload["name"],)).fetchone())


def _create_vm(db: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_environment(db, payload.get("environment", "Production"))
    db.execute(
        """
        INSERT INTO vms (
            name, description, environment, business_unit, owner, application,
            operating_system, host_id, cluster_id, datastore_id, folder,
            resource_pool, vcpu, ram_gb, disk_gb, ip_address, vlan_id,
            backup_enabled, backup_job_id, snapshot, guest_tools,
            power_state, criticality, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["name"],
            payload.get("description", ""),
            payload.get("environment", "Production"),
            payload.get("business_unit", ""),
            payload.get("owner", ""),
            payload.get("application", ""),
            payload.get("operating_system", "Windows Server 2022"),
            int(payload["host_id"]),
            int(payload["cluster_id"]),
            int(payload["datastore_id"]),
            payload.get("folder", "/Production/Applications"),
            payload.get("resource_pool", "RP-Production"),
            int(payload.get("vcpu", 2)),
            int(payload.get("ram_gb", 8)),
            int(payload.get("disk_gb", 100)),
            payload.get("ip_address", ""),
            int(payload["vlan_id"]),
            1 if payload.get("backup_enabled", True) in (True, "true", "1", 1) else 0,
            _nullable_int(payload.get("backup_job_id")),
            payload.get("snapshot", "No"),
            payload.get("guest_tools", "Current"),
            payload.get("power_state", "Powered On"),
            payload.get("criticality", "Medium"),
            payload.get("notes", ""),
        ),
    )
    return row_to_dict(db.execute("SELECT * FROM vms WHERE name = ?", (payload["name"],)).fetchone())


def _assignment_blockers(resource: str, resource_id: int) -> list[tuple[str, int]]:
    """Return assignment counts that prevent deleting a resource."""
    db = get_db()
    blockers = []
    for table, column, label in DELETE_GUARDS.get(resource, ()):
        count = db.execute(
            f"SELECT COUNT(*) AS count FROM {table} WHERE {column} = ?",
            (resource_id,),
        ).fetchone()["count"]
        if count:
            blockers.append((label, count))
    return blockers


def _environment_blockers(resource_id: int) -> list[tuple[str, int]]:
    """Return assignments that prevent deleting an environment."""
    db = get_db()
    name = _resource_name("environments", resource_id)
    if not name:
        return []
    blockers = []
    for table, label in (("clusters", "cluster"), ("vms", "VM")):
        count = db.execute(
            f"SELECT COUNT(*) AS count FROM {table} WHERE environment = ?",
            (name,),
        ).fetchone()["count"]
        if count:
            blockers.append((label, count))
    return blockers


def _update_environment(
    db: sqlite3.Connection,
    resource_id: int,
    payload: dict[str, Any],
    actor: str,
    existing: dict[str, Any],
) -> dict[str, Any]:
    """Update an environment and propagate name changes to inventory rows."""
    fields = [
        field for field in UPDATE_FIELDS["environments"]
        if field in payload and payload[field] is not None
    ]
    if not fields:
        raise ValueError("No editable fields were provided.")

    old_name = existing["name"]
    new_name = str(payload.get("name", old_name)).strip()
    normalized_payload = {**payload, "name": new_name}
    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [normalized_payload[field] for field in fields]
    values.append(resource_id)
    db.execute(
        f"UPDATE environments SET {assignments} WHERE id = ?",
        values,
    )
    if new_name != old_name:
        db.execute(
            "UPDATE clusters SET environment = ? WHERE environment = ?",
            (new_name, old_name),
        )
        db.execute(
            "UPDATE vms SET environment = ? WHERE environment = ?",
            (new_name, old_name),
        )
    _audit(db, actor, "updated", "environments", new_name)
    db.commit()
    return _resource_row("environments", resource_id) or {}


def _ensure_environment(db: sqlite3.Connection, name: str) -> None:
    """Ensure new free-form environment values are visible in the catalog."""
    clean_name = str(name or "Production").strip()
    db.execute(
        """
        INSERT OR IGNORE INTO environments (name, status, notes)
        VALUES (?, 'Active', 'Imported from inventory')
        """,
        (clean_name,),
    )


def _resource_name(resource: str, resource_id: int) -> str | None:
    """Return a display name for a resource."""
    name_column = "hostname" if resource == "hosts" else "name"
    row = get_db().execute(
        f"SELECT {name_column} AS name FROM {RESOURCE_TABLES[resource]} WHERE id = ?",
        (resource_id,),
    ).fetchone()
    return row["name"] if row else None


def _resource_row(resource: str, resource_id: int) -> dict[str, Any] | None:
    """Return a raw resource row by id."""
    row = get_db().execute(
        f"SELECT * FROM {RESOURCE_TABLES[resource]} WHERE id = ?",
        (resource_id,),
    ).fetchone()
    return row_to_dict(row)


def _display_name(resource: str, row: dict[str, Any]) -> str:
    """Return the best display name for a resource row."""
    if resource == "hosts":
        return str(row.get("hostname", row.get("id", "Unknown")))
    return str(row.get("name", row.get("id", "Unknown")))


def _normalize_field_value(field: str, value: Any) -> Any:
    """Normalize browser form values before database updates."""
    if field == "backup_enabled":
        return 1 if value in (True, "true", "1", 1) else 0
    if field == "backup_job_id" and value in (None, "", "null"):
        return None
    if field in INTEGER_FIELDS and value not in (None, ""):
        return int(value)
    return value


def _select_options(query: str) -> list[dict[str, Any]]:
    """Execute a dropdown query and return plain dictionaries."""
    return [dict(row) for row in get_db().execute(query).fetchall()]


def _distribution(query: str) -> list[dict[str, Any]]:
    """Return a chart-friendly distribution with percentages."""
    rows = _select_options(query)
    total = sum(row["count"] for row in rows)
    for row in rows:
        row["percent"] = round((row["count"] / total) * 100, 1) if total else 0
    return rows


def _dashboard_warnings() -> list[dict[str, Any]]:
    """Return prioritized operational warnings for the dashboard."""
    warnings: list[dict[str, Any]] = []
    high_datastores = _scalar(
        """
        SELECT COUNT(*)
        FROM datastores
        WHERE (used_gb * 100.0) / NULLIF(capacity_gb, 0) >= 80
        """
    )
    snapshots = _scalar("SELECT COUNT(*) FROM vms WHERE snapshot = 'Yes'")
    outdated_tools = _scalar(
        "SELECT COUNT(*) FROM vms WHERE guest_tools != 'Current'"
    )
    backup_disabled = _scalar(
        "SELECT COUNT(*) FROM vms WHERE backup_enabled = 0"
    )
    critical = _scalar(
        "SELECT COUNT(*) FROM vms WHERE criticality = 'Critical'"
    )

    warning_sources = (
        ("Datastores above 80%", high_datastores, "critical"),
        ("VMs with snapshots", snapshots, "warning"),
        ("Outdated Guest Tools", outdated_tools, "warning"),
        ("Backups disabled", backup_disabled, "critical"),
        ("Critical VMs", critical, "critical"),
    )
    for title, count, severity in warning_sources:
        if count:
            warnings.append(
                {
                    "title": title,
                    "count": count,
                    "severity": severity,
                }
            )
    if not warnings:
        warnings.append(
            {
                "title": "No active governance warnings",
                "count": 0,
                "severity": "healthy",
            }
        )
    return warnings


def _scalar(query: str) -> int:
    """Return an integer scalar query result."""
    row = get_db().execute(query).fetchone()
    if isinstance(row, dict):
        return int(next(iter(row.values())))
    return int(row[0])


def _validate_logo_url(value: str) -> None:
    """Validate a company logo URL for safe browser rendering."""
    parsed = urlparse(value)
    if value.startswith("/"):
        return
    if parsed.scheme == "https" and parsed.netloc:
        return
    raise ValueError("Logo path must be blank, same-site, or HTTPS.")


def _memory_capacity_gb(raw_memory_values: str) -> int:
    """Parse summed host memory values like '512 GB,1024 GB' into GB."""
    total = 0
    for item in str(raw_memory_values or "").split(","):
        digits = "".join(character for character in item if character.isdigit())
        if digits:
            total += int(digits)
    return total


def _audit(
    db: sqlite3.Connection,
    actor: str,
    action: str,
    entity_type: str,
    entity_name: str | None,
) -> None:
    """Record a governance audit event."""
    db.execute(
        """
        INSERT INTO audit_events (actor, action, entity_type, entity_name)
        VALUES (?, ?, ?, ?)
        """,
        (actor, action, entity_type, entity_name or "Unknown"),
    )


def _nullable_int(value: Any) -> int | None:
    """Convert empty form values to ``None`` for optional foreign keys."""
    if value in (None, "", "null"):
        return None
    return int(value)


def _validated_password(value: Any) -> str:
    """Return a password that meets the minimum local account policy."""
    password = str(value or "")
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters.")
    if password.strip() != password:
        raise ValueError("Password cannot start or end with spaces.")
    return password


def _validate_resource(resource: str) -> None:
    """Raise for unsupported resource names."""
    if resource not in RESOURCE_TABLES:
        raise ValueError(f"Unsupported resource: {resource}")
