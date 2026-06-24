"""Flask web application for enterprise virtualization administration."""

from __future__ import annotations

import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from flask import (
    Flask,
    Response,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.datastructures import FileStorage
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from main import VirtualizationAdministrationToolkit

from .database import close_db, get_db, init_database, row_to_dict
from .services import (
    create_resource,
    create_user_filter,
    create_user,
    delete_user_filter,
    delete_resource,
    get_branding_settings,
    get_dashboard_summary,
    get_reference_options,
    get_user_permissions,
    has_permission,
    list_permissions,
    list_resource,
    list_trash,
    list_user_filters,
    list_users,
    restore_trash_item,
    set_user_permissions,
    update_branding_settings,
    update_resource,
    workbook_export_context,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSRF_SESSION_KEY = "_csrf_token"
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
BRANDING_UPLOAD_FOLDER = Path("uploads") / "branding"
LOGO_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
LOGO_SIGNATURES = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "webp": (b"RIFF",),
}


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_mapping(
        SECRET_KEY=_secret_key(),
        DATABASE_PATH=PROJECT_ROOT / "instance" / "toolkit.sqlite3",
        PROJECT_ROOT=PROJECT_ROOT,
        MAX_CONTENT_LENGTH=1_048_576,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_env_bool("VIRTUALIZATION_TOOLKIT_COOKIE_SECURE"),
    )
    if test_config:
        app.config.update(test_config)

    init_database(app)
    app.teardown_appcontext(close_db)
    _register_request_hooks(app)
    _register_routes(app)
    return app


def _register_request_hooks(app: Flask) -> None:
    """Register request lifecycle hooks."""

    @app.before_request
    def load_logged_in_user() -> Response | None:
        session.setdefault(CSRF_SESSION_KEY, secrets.token_urlsafe(32))
        if request.method in MUTATING_METHODS and not _valid_csrf_token():
            if request.path.startswith("/api/"):
                return jsonify({"message": "Invalid or missing CSRF token."}), 400
            flash("Your session security token expired. Please try again.", "error")
            return redirect(url_for("login"))

        user_id = session.get("user_id")
        g.user = None
        if user_id is not None:
            row = get_db().execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            g.user = row_to_dict(row)
            if g.user is not None:
                g.user["permissions"] = sorted(get_user_permissions(user_id))
        return None

    @app.context_processor
    def inject_security_context() -> dict[str, str]:
        return {"csrf_token": session.get(CSRF_SESSION_KEY, "")}

    @app.after_request
    def set_security_headers(response: Response) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'",
        )
        return response


def _register_routes(app: Flask) -> None:
    """Register HTML and JSON routes."""

    @app.route("/login", methods=("GET", "POST"))
    def login() -> str | Response:
        if request.method == "POST":
            username = request.form["username"].strip()
            password = request.form["password"]
            user = get_db().execute(
                "SELECT * FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session[CSRF_SESSION_KEY] = secrets.token_urlsafe(32)
                return redirect(url_for("dashboard"))
            flash("Invalid username or password.", "error")
        return render_template("login.html", branding=get_branding_settings())

    @app.route("/logout")
    def logout() -> Response:
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def dashboard() -> str:
        return render_template(
            "dashboard.html",
            summary=get_dashboard_summary(),
            user=g.user,
            permissions=list_permissions(),
            branding=get_branding_settings(),
        )

    @app.get("/api/summary")
    @login_required
    def api_summary() -> Response:
        return jsonify(get_dashboard_summary())

    @app.get("/api/reference-options")
    @login_required
    def api_reference_options() -> Response:
        return jsonify(get_reference_options())

    @app.get("/api/branding")
    @login_required
    def api_branding() -> Response:
        return jsonify(get_branding_settings())

    @app.put("/api/branding")
    @login_required
    @permission_required("branding.manage")
    def api_update_branding() -> Response:
        try:
            payload = _branding_payload(app)
            return jsonify(update_branding_settings(payload, g.user["username"]))
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 400

    @app.get("/api/filters")
    @login_required
    def api_filters() -> Response:
        return jsonify(list_user_filters(g.user["id"]))

    @app.post("/api/filters")
    @login_required
    def api_create_filter() -> Response:
        payload = request.get_json(silent=True) or {}
        try:
            created = create_user_filter(
                g.user["id"],
                payload,
                g.user["username"],
            )
            return jsonify(created), 201
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 400

    @app.delete("/api/filters/<int:filter_id>")
    @login_required
    def api_delete_filter(filter_id: int) -> Response:
        try:
            result = delete_user_filter(
                filter_id,
                g.user["id"],
                g.user["username"],
            )
            return jsonify({"message": result["message"]})
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 404

    @app.get("/api/resources/<resource>")
    @login_required
    def api_list_resource(resource: str) -> Response:
        try:
            return jsonify(list_resource(resource))
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 404

    @app.post("/api/resources/<resource>")
    @login_required
    @permission_required("resource.create")
    def api_create_resource(resource: str) -> Response:
        payload = request.get_json(silent=True) or {}
        try:
            created = create_resource(resource, payload, g.user["username"])
            return jsonify(created), 201
        except KeyError as exc:
            return jsonify({"message": f"Missing required field: {exc}"}), 400
        except sqlite3.IntegrityError as exc:
            return jsonify({"message": f"Database rule failed: {exc}"}), 409
        except (TypeError, ValueError) as exc:
            return jsonify({"message": str(exc)}), 400

    @app.put("/api/resources/<resource>/<int:resource_id>")
    @login_required
    @permission_required("resource.create")
    def api_update_resource(resource: str, resource_id: int) -> Response:
        payload = request.get_json(silent=True) or {}
        try:
            updated = update_resource(
                resource,
                resource_id,
                payload,
                g.user["username"],
            )
            return jsonify(updated)
        except sqlite3.IntegrityError as exc:
            return jsonify({"message": f"Database rule failed: {exc}"}), 409
        except (TypeError, ValueError) as exc:
            return jsonify({"message": str(exc)}), 400

    @app.delete("/api/resources/<resource>/<int:resource_id>")
    @login_required
    @permission_required("resource.delete")
    def api_delete_resource(resource: str, resource_id: int) -> Response:
        try:
            result = delete_resource(resource, resource_id, g.user["username"])
            return jsonify({"message": result["message"]}), result["status"]
        except sqlite3.IntegrityError as exc:
            return jsonify({"message": f"Database rule failed: {exc}"}), 409
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 404

    @app.get("/api/trash")
    @login_required
    @permission_required("resource.delete")
    def api_trash() -> Response:
        return jsonify(list_trash())

    @app.post("/api/trash/<int:trash_id>/restore")
    @login_required
    @permission_required("resource.delete")
    def api_restore_trash_item(trash_id: int) -> Response:
        try:
            result = restore_trash_item(trash_id, g.user["username"])
            return jsonify({"message": result["message"]}), result["status"]
        except sqlite3.IntegrityError as exc:
            return jsonify({"message": f"Restore failed: {exc}"}), 409
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 400

    @app.get("/export/workbook")
    @login_required
    @permission_required("workbook.export")
    def export_workbook() -> Response:
        toolkit = VirtualizationAdministrationToolkit(
            PROJECT_ROOT,
            **workbook_export_context(),
        )
        toolkit.run()
        return send_file(
            toolkit.output_path,
            as_attachment=True,
            download_name=toolkit.output_path.name,
        )

    @app.get("/api/permissions")
    @login_required
    @permission_required("users.manage")
    def api_permissions() -> Response:
        return jsonify(list_permissions())

    @app.get("/api/users")
    @login_required
    @permission_required("users.manage")
    def api_users() -> Response:
        return jsonify(list_users())

    @app.post("/api/users")
    @login_required
    @permission_required("users.manage")
    def api_create_user() -> Response:
        payload = request.get_json(silent=True) or {}
        try:
            created = create_user(payload, g.user["username"])
            return jsonify(created), 201
        except KeyError as exc:
            return jsonify({"message": f"Missing required field: {exc}"}), 400
        except sqlite3.IntegrityError as exc:
            return jsonify({"message": f"Database rule failed: {exc}"}), 409
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 400

    @app.put("/api/users/<int:user_id>/permissions")
    @login_required
    @permission_required("users.manage")
    def api_set_user_permissions(user_id: int) -> Response:
        payload = request.get_json(silent=True) or {}
        try:
            updated = set_user_permissions(
                user_id,
                payload.get("permissions", []),
                g.user["username"],
            )
            return jsonify(updated)
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 400


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    """Require an authenticated session for a view."""

    @wraps(view)
    def wrapped_view(**kwargs: Any) -> Any:
        if g.get("user") is None:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


def permission_required(permission_code: str) -> Callable[..., Any]:
    """Require the current user to have a permission or administrator role."""

    def decorator(view: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view)
        def wrapped_view(**kwargs: Any) -> Any:
            if not has_permission(g.user, permission_code):
                return jsonify({"message": "You do not have permission."}), 403
            return view(**kwargs)

        return wrapped_view

    return decorator


def _secret_key() -> str:
    """Return the configured Flask signing key or a process-local dev key."""
    configured_secret = os.getenv("VIRTUALIZATION_TOOLKIT_SECRET_KEY")
    if configured_secret:
        return configured_secret
    return secrets.token_urlsafe(32)


def _env_bool(name: str) -> bool:
    """Return true for common truthy environment flag values."""
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _valid_csrf_token() -> bool:
    """Validate CSRF tokens for form and JSON mutation requests."""
    expected = session.get(CSRF_SESSION_KEY, "")
    provided = (
        request.headers.get("X-CSRF-Token")
        or request.form.get("csrf_token")
        or ""
    )
    return bool(expected) and secrets.compare_digest(str(expected), str(provided))


def _branding_payload(app: Flask) -> dict[str, Any]:
    """Return branding payload from JSON or multipart form requests."""
    if request.files:
        payload = request.form.to_dict()
        remove_logo = payload.pop("remove_logo", "") == "1"
        logo_file = request.files.get("logo_file")
        if logo_file and logo_file.filename:
            payload["logo_url"] = _store_branding_logo(app, logo_file)
        elif remove_logo:
            _delete_uploaded_logo(payload.get("logo_url", ""))
            payload["logo_url"] = ""
        return payload
    return request.get_json(silent=True) or {}


def _store_branding_logo(app: Flask, logo_file: FileStorage) -> str:
    """Validate and store a company logo upload in the static assets tree."""
    original_name = secure_filename(logo_file.filename or "")
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in LOGO_EXTENSIONS:
        raise ValueError("Logo must be a PNG, JPG, JPEG, or WEBP image.")

    head = logo_file.stream.read(16)
    logo_file.stream.seek(0)
    signatures = LOGO_SIGNATURES.get(extension, ())
    if not any(head.startswith(signature) for signature in signatures):
        raise ValueError("Logo file type does not match the selected image.")
    if extension == "webp" and head[8:12] != b"WEBP":
        raise ValueError("Logo file type does not match the selected image.")

    upload_root = Path(app.static_folder or "") / BRANDING_UPLOAD_FOLDER
    upload_root.mkdir(parents=True, exist_ok=True)
    filename = f"company-logo-{secrets.token_hex(8)}.{extension}"
    destination = upload_root / filename
    logo_file.save(destination)

    old_logo_url = request.form.get("logo_url", "")
    _delete_uploaded_logo(old_logo_url)
    return url_for("static", filename=f"{BRANDING_UPLOAD_FOLDER.as_posix()}/{filename}")


def _delete_uploaded_logo(logo_url: str) -> None:
    """Delete a previously uploaded logo when it belongs to the branding folder."""
    static_prefix = "/static/"
    if not logo_url.startswith(static_prefix):
        return
    relative = logo_url[len(static_prefix):].split("?", 1)[0]
    if not relative.startswith(BRANDING_UPLOAD_FOLDER.as_posix() + "/"):
        return
    target = (PROJECT_ROOT / "webapp" / "static" / relative).resolve()
    allowed_root = (PROJECT_ROOT / "webapp" / "static" / BRANDING_UPLOAD_FOLDER).resolve()
    try:
        target.relative_to(allowed_root)
    except ValueError:
        return
    if target.is_file():
        target.unlink()


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)

