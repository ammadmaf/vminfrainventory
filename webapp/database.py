"""Database persistence for the Virtualization Administration Toolkit web app."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from flask import current_app, g
from werkzeug.security import generate_password_hash

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional outside PostgreSQL deployments.
    psycopg = None
    dict_row = None

DB_INTEGRITY_ERRORS = (
    sqlite3.IntegrityError,
    psycopg.IntegrityError if psycopg is not None else sqlite3.IntegrityError,
)


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'client')),
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS permissions (
    code TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_permissions (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_code TEXT NOT NULL REFERENCES permissions(code) ON DELETE CASCADE,
    PRIMARY KEY (user_id, permission_code)
);

CREATE TABLE IF NOT EXISTS clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    environment TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS environments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'Active',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL UNIQUE,
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    version TEXT NOT NULL,
    build TEXT NOT NULL,
    cpu TEXT NOT NULL,
    memory TEXT NOT NULL,
    nics INTEGER NOT NULL,
    management_ip TEXT NOT NULL,
    license TEXT NOT NULL,
    health TEXT NOT NULL DEFAULT 'Healthy',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS datastores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    datastore_type TEXT NOT NULL,
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    capacity_gb INTEGER NOT NULL,
    used_gb INTEGER NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS vlans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    cidr TEXT NOT NULL,
    security_zone TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS backup_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    schedule TEXT NOT NULL,
    repository TEXT NOT NULL,
    retention TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Success'
);

CREATE TABLE IF NOT EXISTS vms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    environment TEXT NOT NULL,
    business_unit TEXT NOT NULL,
    owner TEXT NOT NULL,
    application TEXT NOT NULL,
    operating_system TEXT NOT NULL,
    host_id INTEGER NOT NULL REFERENCES hosts(id),
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    datastore_id INTEGER NOT NULL REFERENCES datastores(id),
    folder TEXT NOT NULL,
    resource_pool TEXT NOT NULL,
    vcpu INTEGER NOT NULL,
    ram_gb INTEGER NOT NULL,
    disk_gb INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    vlan_id INTEGER NOT NULL REFERENCES vlans(id),
    backup_enabled INTEGER NOT NULL DEFAULT 1,
    backup_job_id INTEGER REFERENCES backup_jobs(id),
    snapshot TEXT NOT NULL DEFAULT 'No',
    guest_tools TEXT NOT NULL DEFAULT 'Current',
    power_state TEXT NOT NULL DEFAULT 'Powered On',
    criticality TEXT NOT NULL DEFAULT 'Medium',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trash_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource TEXT NOT NULL,
    resource_id INTEGER NOT NULL,
    display_name TEXT NOT NULL,
    payload TEXT NOT NULL,
    deleted_by TEXT NOT NULL,
    deleted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_filters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    target_view TEXT NOT NULL,
    search_term TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


POSTGRES_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'client')),
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS permissions (
    code TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_permissions (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_code TEXT NOT NULL REFERENCES permissions(code) ON DELETE CASCADE,
    PRIMARY KEY (user_id, permission_code)
);

CREATE TABLE IF NOT EXISTS clusters (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    environment TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS environments (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'Active',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS hosts (
    id SERIAL PRIMARY KEY,
    hostname TEXT NOT NULL UNIQUE,
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    version TEXT NOT NULL,
    build TEXT NOT NULL,
    cpu TEXT NOT NULL,
    memory TEXT NOT NULL,
    nics INTEGER NOT NULL,
    management_ip TEXT NOT NULL,
    license TEXT NOT NULL,
    health TEXT NOT NULL DEFAULT 'Healthy',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS datastores (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    datastore_type TEXT NOT NULL,
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    capacity_gb INTEGER NOT NULL,
    used_gb INTEGER NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS vlans (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    cidr TEXT NOT NULL,
    security_zone TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS backup_jobs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    schedule TEXT NOT NULL,
    repository TEXT NOT NULL,
    retention TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Success'
);

CREATE TABLE IF NOT EXISTS vms (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    environment TEXT NOT NULL,
    business_unit TEXT NOT NULL,
    owner TEXT NOT NULL,
    application TEXT NOT NULL,
    operating_system TEXT NOT NULL,
    host_id INTEGER NOT NULL REFERENCES hosts(id),
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    datastore_id INTEGER NOT NULL REFERENCES datastores(id),
    folder TEXT NOT NULL,
    resource_pool TEXT NOT NULL,
    vcpu INTEGER NOT NULL,
    ram_gb INTEGER NOT NULL,
    disk_gb INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    vlan_id INTEGER NOT NULL REFERENCES vlans(id),
    backup_enabled INTEGER NOT NULL DEFAULT 1,
    backup_job_id INTEGER REFERENCES backup_jobs(id),
    snapshot TEXT NOT NULL DEFAULT 'No',
    guest_tools TEXT NOT NULL DEFAULT 'Current',
    power_state TEXT NOT NULL DEFAULT 'Powered On',
    criticality TEXT NOT NULL DEFAULT 'Medium',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trash_items (
    id SERIAL PRIMARY KEY,
    resource TEXT NOT NULL,
    resource_id INTEGER NOT NULL,
    display_name TEXT NOT NULL,
    payload TEXT NOT NULL,
    deleted_by TEXT NOT NULL,
    deleted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_filters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    target_view TEXT NOT NULL,
    search_term TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


SEED_SQL = """
INSERT OR IGNORE INTO clusters (name, environment, status, notes) VALUES
('Cluster-Production', 'Production', 'Active', 'Primary production compute'),
('Cluster-Development', 'Development', 'Active', 'Engineering workloads'),
('Cluster-Test', 'Test', 'Active', 'QA and staging workloads');

INSERT OR IGNORE INTO environments (name, status, notes) VALUES
('Production', 'Active', 'Production workloads'),
('Development', 'Active', 'Engineering and development workloads'),
('Test', 'Active', 'QA and staging workloads'),
('DR', 'Active', 'Disaster recovery workloads');

INSERT OR IGNORE INTO hosts (
    hostname, cluster_id, version, build, cpu, memory, nics,
    management_ip, license, health, notes
) VALUES
(
    'host-prd-01.company.local',
    (SELECT id FROM clusters WHERE name = 'Cluster-Production'),
    'Generic Hypervisor 2026', '260624', '2 x Intel Xeon Gold, 56 cores',
    '1024 GB', 8, '10.10.1.21', 'Enterprise Plus',
    'Healthy', 'Primary production host'
),
(
    'host-dev-01.company.local',
    (SELECT id FROM clusters WHERE name = 'Cluster-Development'),
    'Generic Hypervisor 2025', '250624', '2 x Intel Xeon Silver, 32 cores',
    '512 GB', 6, '10.20.1.31', 'Standard',
    'Healthy', 'Development host'
);

INSERT OR IGNORE INTO datastores (
    name, datastore_type, cluster_id, capacity_gb, used_gb, notes
) VALUES
(
    'DS-PRD-01', 'VMFS',
    (SELECT id FROM clusters WHERE name = 'Cluster-Production'),
    12000, 9300, 'Primary production datastore'
),
(
    'DS-DEV-01', 'NFS',
    (SELECT id FROM clusters WHERE name = 'Cluster-Development'),
    8000, 4200, 'Development datastore'
),
(
    'DS-TST-01', 'VMFS',
    (SELECT id FROM clusters WHERE name = 'Cluster-Test'),
    6000, 4850, 'Test datastore'
);

INSERT OR IGNORE INTO vlans (name, cidr, security_zone, notes) VALUES
('VLAN-120', '10.10.20.0/24', 'Restricted', 'Production app network'),
('VLAN-230', '10.20.30.0/24', 'Development', 'Development services'),
('VLAN-340', '10.30.40.0/24', 'Test', 'Test web tier');

INSERT OR IGNORE INTO backup_jobs (
    name, schedule, repository, retention, status
) VALUES
('Daily-Production', 'Daily 22:00', 'Repo-Primary', '30 daily, 12 monthly', 'Success'),
('Weekly-Development', 'Saturday 20:00', 'Repo-Development', '8 weekly', 'Warning'),
('Critical-SQL-Logs', 'Every 4 hours', 'Repo-Primary', '14 days', 'Success');

INSERT OR IGNORE INTO vms (
    name, description, environment, business_unit, owner, application,
    operating_system, host_id, cluster_id, datastore_id, folder,
    resource_pool, vcpu, ram_gb, disk_gb, ip_address, vlan_id,
    backup_enabled, backup_job_id, snapshot, guest_tools,
    power_state, criticality, notes
) VALUES
(
    'APP-PRD-001', 'Revenue application server', 'Production', 'Finance',
    'Application Operations', 'Revenue Suite', 'Windows Server 2022',
    (SELECT id FROM hosts WHERE hostname = 'host-prd-01.company.local'),
    (SELECT id FROM clusters WHERE name = 'Cluster-Production'),
    (SELECT id FROM datastores WHERE name = 'DS-PRD-01'),
    '/Production/Applications', 'RP-Production', 8, 96, 1500,
    '10.10.20.15', (SELECT id FROM vlans WHERE name = 'VLAN-120'),
    1, (SELECT id FROM backup_jobs WHERE name = 'Daily-Production'),
    'No', 'Current', 'Powered On', 'Critical', 'Tier 1 business service'
),
(
    'SQL-DEV-002', 'Development database', 'Development', 'Engineering',
    'Database Services', 'Analytics Lab', 'Ubuntu Server 24.04',
    (SELECT id FROM hosts WHERE hostname = 'host-dev-01.company.local'),
    (SELECT id FROM clusters WHERE name = 'Cluster-Development'),
    (SELECT id FROM datastores WHERE name = 'DS-DEV-01'),
    '/Development/Databases', 'RP-Development', 4, 16, 250,
    '10.20.30.22', (SELECT id FROM vlans WHERE name = 'VLAN-230'),
    1, (SELECT id FROM backup_jobs WHERE name = 'Weekly-Development'),
    'Yes', 'Outdated', 'Powered On', 'Medium', 'Patch window pending'
);
"""


POSTGRES_SEED_SQL = (
    SEED_SQL.replace("INSERT OR IGNORE INTO", "INSERT INTO")
    .replace(";\n\nINSERT INTO", "\nON CONFLICT DO NOTHING;\n\nINSERT INTO")
    .rstrip()
    .removesuffix(";")
    + "\nON CONFLICT DO NOTHING;"
)


class DatabaseConnection:
    """Small compatibility wrapper for SQLite and PostgreSQL connections."""

    def __init__(self, connection: Any, dialect: str) -> None:
        self.connection = connection
        self.dialect = dialect

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> Any:
        return self.connection.execute(self._translate_sql(sql), params)

    def executemany(self, sql: str, params: list[tuple[Any, ...]]) -> Any:
        return self.connection.executemany(self._translate_sql(sql), params)

    def executescript(self, script: str) -> None:
        if self.dialect == "sqlite":
            self.connection.executescript(script)
            return
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement)

    def commit(self) -> None:
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "DatabaseConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if exc_type is None:
            self.commit()
        self.close()

    def _translate_sql(self, sql: str) -> str:
        if self.dialect == "sqlite":
            return sql
        translated = sql.replace("?", "%s")
        translated = translated.replace("INSERT OR IGNORE INTO", "INSERT INTO")
        if "INSERT INTO" in translated and "OR IGNORE" not in sql and "ON CONFLICT" not in translated:
            pass
        elif "INSERT INTO" in translated and "OR IGNORE" in sql and "ON CONFLICT" not in translated:
            translated = translated.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
        translated = translated.replace(
            "GROUP_CONCAT(DISTINCT datastores.name)",
            "STRING_AGG(DISTINCT datastores.name, ',')",
        )
        translated = translated.replace(
            "GROUP_CONCAT(hosts.memory)",
            "STRING_AGG(hosts.memory, ',')",
        )
        translated = translated.replace(
            "GROUP_CONCAT(DISTINCT hosts.hostname)",
            "STRING_AGG(DISTINCT hosts.hostname, ',')",
        )
        return translated


def database_path() -> Path:
    """Return the configured SQLite database path."""
    configured_path = current_app.config.get("DATABASE_PATH")
    return Path(configured_path)


def database_url() -> str:
    """Return the configured PostgreSQL URL, when production DB mode is enabled."""
    return str(current_app.config.get("DATABASE_URL") or "")


def database_backend() -> str:
    """Return the active database backend name."""
    return "postgres" if database_url() else "sqlite"


def connect_database() -> DatabaseConnection:
    """Create a database connection for the configured backend."""
    if database_backend() == "postgres":
        if psycopg is None:
            raise RuntimeError("psycopg is required when DATABASE_URL is set.")
        connection = psycopg.connect(database_url(), row_factory=dict_row)
        return DatabaseConnection(connection, "postgres")
    connection = sqlite3.connect(database_path())
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return DatabaseConnection(connection, "sqlite")


def get_db() -> DatabaseConnection:
    """Return a request-scoped database connection."""
    if "db" not in g:
        g.db = connect_database()
    return g.db


def close_db(_: BaseException | None = None) -> None:
    """Close the request-scoped database connection."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_database(app) -> None:
    """Create the database schema and seed demo enterprise data."""
    if app.config.get("DATABASE_URL"):
        with app.app_context(), connect_database() as connection:
            connection.executescript(POSTGRES_SCHEMA_SQL)
            _seed_permissions(connection)
            _seed_users(connection)
            _seed_app_settings(connection)
            connection.executescript(POSTGRES_SEED_SQL)
            _sync_environments(connection)
            _normalize_virtualization_terms(connection)
        return

    db_path = Path(app.config["DATABASE_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with app.app_context(), connect_database() as connection:
        connection.executescript(SCHEMA_SQL)
        _migrate_schema(connection)
        _seed_permissions(connection)
        _seed_users(connection)
        _seed_app_settings(connection)
        connection.executescript(SEED_SQL)
        _sync_environments(connection)
        _normalize_virtualization_terms(connection)
        connection.commit()


def _migrate_schema(connection: DatabaseConnection) -> None:
    """Apply lightweight schema upgrades for existing local databases."""
    if connection.dialect != "sqlite":
        return
    vm_columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(vms)").fetchall()
    }
    legacy_guest_tools_column = "vm" + "ware_tools"
    if (
        "guest_tools" not in vm_columns
        and legacy_guest_tools_column in vm_columns
    ):
        connection.execute(
            "ALTER TABLE vms ADD COLUMN guest_tools TEXT NOT NULL "
            "DEFAULT 'Current'"
        )
        connection.execute(
            f"UPDATE vms SET guest_tools = {legacy_guest_tools_column}"
        )
        vm_columns.add("guest_tools")

    if (
        "guest_tools" in vm_columns
        and legacy_guest_tools_column in vm_columns
    ):
        connection.execute(
            f"ALTER TABLE vms DROP COLUMN {legacy_guest_tools_column}"
        )


def _normalize_virtualization_terms(connection: DatabaseConnection) -> None:
    """Normalize existing demo/user data to vendor-neutral terminology."""
    replacements = (
        ("VM" + "ware ES" + "Xi", "Generic Hypervisor"),
        ("VM" + "ware", "Virtualization"),
        ("ES" + "XI", "HOST"),
        ("ES" + "Xi", "Host"),
        ("es" + "xi", "host"),
        ("v" + "Sphere", "hypervisor suite"),
        ("v" + "Center", "management server"),
    )
    _normalize_hostnames(connection, replacements)
    for table_name in _application_tables(connection):
        for column_name in _text_columns(connection, table_name):
            if table_name == "hosts" and column_name == "hostname":
                continue
            quoted_table = _quote_identifier(table_name)
            quoted_column = _quote_identifier(column_name)
            for old_value, new_value in replacements:
                connection.execute(
                    f"""
                    UPDATE {quoted_table}
                    SET {quoted_column} = REPLACE(
                        {quoted_column},
                        ?,
                        ?
                    )
                    WHERE {quoted_column} LIKE ?
                    """,
                    (old_value, new_value, f"%{old_value}%"),
                )


def _normalize_hostnames(
    connection: DatabaseConnection,
    replacements: tuple[tuple[str, str], ...],
) -> None:
    """Normalize hostnames while preserving uniqueness."""
    rows = connection.execute(
        "SELECT id, hostname FROM hosts ORDER BY id"
    ).fetchall()
    used_hostnames = {_row_value(row, "hostname", 1) for row in rows}
    for row in rows:
        row_id = _row_value(row, "id", 0)
        current_hostname = _row_value(row, "hostname", 1)
        neutral_hostname = _neutralize_text(current_hostname, replacements)
        if neutral_hostname == current_hostname:
            continue

        used_hostnames.discard(current_hostname)
        final_hostname = neutral_hostname
        suffix = 1
        while final_hostname in used_hostnames:
            final_hostname = f"{neutral_hostname}-legacy-{suffix}"
            suffix += 1

        connection.execute(
            "UPDATE hosts SET hostname = ? WHERE id = ?",
            (final_hostname, row_id),
        )
        used_hostnames.add(final_hostname)


def _neutralize_text(
    value: str,
    replacements: tuple[tuple[str, str], ...],
) -> str:
    """Apply virtualization-neutral replacements to a value."""
    neutral_value = value
    for old_value, new_value in replacements:
        neutral_value = neutral_value.replace(old_value, new_value)
    return neutral_value


def _application_tables(connection: DatabaseConnection) -> list[str]:
    """Return application-owned tables that can contain display text."""
    if connection.dialect == "postgres":
        rows = connection.execute(
            """
            SELECT table_name AS name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            """
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
    return [_row_value(row, "name", 0) for row in rows]


def _text_columns(
    connection: DatabaseConnection,
    table_name: str,
) -> list[str]:
    """Return text columns for a table."""
    if connection.dialect == "postgres":
        rows = connection.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = ?
              AND data_type IN ('text', 'character varying')
            """,
            (table_name,),
        ).fetchall()
        return [row["column_name"] for row in rows]
    rows = connection.execute(f"PRAGMA table_info({_quote_identifier(table_name)})").fetchall()
    return [row[1] for row in rows if "TEXT" in str(row[2]).upper()]


def _quote_identifier(identifier: str) -> str:
    """Quote a SQLite identifier from the application schema."""
    return '"' + identifier.replace('"', '""') + '"'


def _seed_permissions(connection: DatabaseConnection) -> None:
    """Seed assignable application permissions."""
    permissions = (
        (
            "resource.create",
            "Create resources",
            "Create VMs, hosts, datastores, VLANs, backup jobs, and clusters.",
        ),
        (
            "resource.delete",
            "Delete resources",
            "Delete resources when dependency protection allows it.",
        ),
        (
            "workbook.export",
            "Export workbook",
            "Download the premium Excel workbook from the web console.",
        ),
        (
            "users.manage",
            "Manage users",
            "Create users and assign or revoke permissions.",
        ),
        (
            "branding.manage",
            "Manage branding",
            "Update company name, logo, and workbook report branding.",
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO permissions (code, label, description)
        VALUES (?, ?, ?)
        """,
        permissions,
    )


def _seed_users(connection: DatabaseConnection) -> None:
    """Seed admin and client users for role-based access demos."""
    existing_user_count = _row_value(connection.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone(), "count", 0)
    if existing_user_count:
        return

    admin_password = _required_seed_password(
        "VIRTUALIZATION_TOOLKIT_ADMIN_PASSWORD"
    )
    client_password = _required_seed_password(
        "VIRTUALIZATION_TOOLKIT_CLIENT_PASSWORD"
    )
    users = (
        (
            "admin",
            "Infrastructure Admin",
            "admin",
            generate_password_hash(admin_password),
        ),
        (
            "client",
            "Read Only Client",
            "client",
            generate_password_hash(client_password),
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO users (
            username, display_name, role, password_hash
        )
        VALUES (?, ?, ?, ?)
        """,
        users,
    )


def _required_seed_password(env_var: str) -> str:
    """Return a first-run seed password from an explicit environment variable."""
    password = os.getenv(env_var, "")
    if not password:
        raise RuntimeError(
            f"{env_var} must be set before initializing a new toolkit database."
        )
    return password


def _row_value(row: Any, key: str, index: int) -> Any:
    """Read a value from either a dict row or DB-API positional row."""
    if isinstance(row, dict):
        return row.get(key) if key in row else next(iter(row.values()))
    return row[index]


def _seed_app_settings(connection: DatabaseConnection) -> None:
    """Seed configurable branding defaults without overwriting user choices."""
    settings = (
        ("company_name", "Virtualization Administration Toolkit"),
        (
            "tagline",
            "Secure enterprise console for governed VM, host, datastore, backup, and access administration.",
        ),
        ("logo_url", ""),
        ("report_title", "Infrastructure Overview Report"),
        ("report_author", "Infrastructure Admin"),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO app_settings (key, value)
        VALUES (?, ?)
        """,
        settings,
    )


def _sync_environments(connection: DatabaseConnection) -> None:
    """Keep the environment catalog aligned with existing inventory values."""
    connection.execute(
        """
        INSERT OR IGNORE INTO environments (name, status, notes)
        SELECT DISTINCT environment, 'Active', 'Imported from clusters'
        FROM clusters
        WHERE environment IS NOT NULL AND TRIM(environment) != ''
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO environments (name, status, notes)
        SELECT DISTINCT environment, 'Active', 'Imported from VMs'
        FROM vms
        WHERE environment IS NOT NULL AND TRIM(environment) != ''
        """
    )


def row_to_dict(row: Any | None) -> dict[str, Any] | None:
    """Convert a database row to a plain dictionary."""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return {key: row[key] for key in row.keys()}

