# Virtualization Administration Toolkit

Virtualization Administration Toolkit is a Python 3.12 project designed to manage
enterprise virtualization inventory and generate professional workbook-based
operational summaries.

The project now includes both a workbook generator and a Flask web console for
live VM, host, datastore, VLAN, backup, and reference administration.

## Features

Implemented workbook modules include:

- Cover page generation
- Instructions worksheet
- Executive dashboard worksheet
- Virtual machine inventory worksheet
- host inventory worksheet
- Datastore reporting worksheet
- Capacity planning worksheet
- Snapshot reporting worksheet
- Backup reporting worksheet
- License reporting worksheet
- Reusable workbook styling
- Commercial PDF and PNG preview assets
- Flask-based enterprise web console
- PostgreSQL persistence for Docker/production deployments
- SQLite fallback for local development without `DATABASE_URL`
- Admin and client role-based access
- Assignable user permissions from the admin panel
- Dynamic dropdowns backed by live source tables
- Protected delete workflow for assigned resources
- Docker-ready deployment files

## Requirements

- Python 3.12
- openpyxl
- Flask
- gunicorn for Linux container deployment

## Folder Structure

```text
virtualization-toolkit/
|-- main.py
|-- web.py
|-- Dockerfile
|-- requirements.txt
|-- README.md
|-- src/
|   |-- styles.py
|   |-- dashboard.py
|   |-- vm_inventory.py
|   |-- host_inventory.py
|   |-- datastore.py
|   |-- capacity.py
|   |-- snapshot.py
|   |-- backup.py
|   |-- license.py
|   |-- cover.py
|   `-- instructions.py
|-- webapp/
|   |-- app.py
|   |-- database.py
|   |-- services.py
|   |-- templates/
|   `-- static/
|-- assets/
|   `-- .gitkeep
`-- output/
    `-- .gitkeep
```

## How to Run

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the Excel workbook generator:

```powershell
python main.py
```

The generated workbook is saved to:

```text
output/Premium_Virtualization_Administration_Toolkit.xlsx
```

Run the web console:

```powershell
$env:VIRTUALIZATION_TOOLKIT_SECRET_KEY="replace-with-a-secure-secret"
$env:VIRTUALIZATION_TOOLKIT_ADMIN_PASSWORD="replace-with-admin-password"
$env:VIRTUALIZATION_TOOLKIT_CLIENT_PASSWORD="replace-with-client-password"
python web.py
```

Open:

```text
http://127.0.0.1:5000
```

For a new database, set secure environment variables before the first run:

```powershell
$env:VIRTUALIZATION_TOOLKIT_SECRET_KEY="replace-with-a-secure-secret"
$env:VIRTUALIZATION_TOOLKIT_ADMIN_PASSWORD="replace-with-admin-password"
$env:VIRTUALIZATION_TOOLKIT_CLIENT_PASSWORD="replace-with-client-password"
```

The first launch creates `admin` and `client` accounts with the passwords above.
For existing local databases, update user passwords from the admin panel.

## Docker

Copy the example environment file and set strong secrets before first start:

```bash
cp .env.example .env
```

Required values:

```text
POSTGRES_PASSWORD
VIRTUALIZATION_TOOLKIT_SECRET_KEY
VIRTUALIZATION_TOOLKIT_ADMIN_PASSWORD
VIRTUALIZATION_TOOLKIT_CLIENT_PASSWORD
```

Run the production-style Postgres stack:

```bash
docker compose up -d --build
```

Open:

```text
http://127.0.0.1:5000
```

Persistent Docker volumes:

- `vminfrainventory_postgres` stores the PostgreSQL database.
- `vminfrainventory_branding_uploads` stores uploaded company logos.
- `vminfrainventory_output` stores generated workbook exports.

The first launch creates `admin` and `client` users using the password
environment variables. After the database volume exists, changing those
environment variables does not reset existing user passwords; update users from
the admin panel or recreate the database volume.

Set `VIRTUALIZATION_TOOLKIT_COOKIE_SECURE=true` only when the app is served
through HTTPS. Keep it `false` for direct plain HTTP access.

Build and run the app container manually with SQLite fallback:

```powershell
docker build -t virtualization-administration-toolkit .
docker run -p 5000:5000 `
  -e VIRTUALIZATION_TOOLKIT_SECRET_KEY="replace-with-a-secure-secret" `
  -e VIRTUALIZATION_TOOLKIT_ADMIN_PASSWORD="replace-with-admin-password" `
  -e VIRTUALIZATION_TOOLKIT_CLIENT_PASSWORD="replace-with-client-password" `
  virtualization-administration-toolkit
```

For SQLite fallback persistence, mount `/app/instance` to a managed volume.
For production, prefer the Compose Postgres stack above.

## Web Console Capabilities

- Add clusters, hosts, datastores, VLANs, backup jobs, and VMs.
- VM creation forms use live dropdowns from the source resource tables.
- Newly added hosts and datastores become available immediately.
- Admin users are superusers.
- Client users are read-only by default.
- Admins can create users and grant or revoke permissions.
- Grantable permissions include resource creation, resource deletion, workbook
  export, and user management.
- Assigned hosts, datastores, VLANs, backup jobs, and clusters cannot be
  deleted until dependent VMs or child resources are reassigned.
- Export the existing premium Excel workbook from the web console.

## Screenshots

Preview images are included in `assets/preview`.

### Dashboard Preview

`assets/preview/dashboard-preview.png`

### Workbook Output Preview

`assets/preview/cover-preview.png`

### Web Console Preview

`assets/preview/web-console-preview.png`

## Development Standards

- Enterprise-style modular architecture
- Object-oriented design where appropriate
- PEP 8 compliant source formatting
- Clear module docstrings and method comments
- GitHub-ready project documentation


