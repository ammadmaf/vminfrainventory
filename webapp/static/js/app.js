const state = {
    role: document.body.dataset.role,
    isSuperuser: document.body.dataset.superuser === "true",
    permissions: JSON.parse(document.body.dataset.permissions || "[]"),
    iconPath: document.body.dataset.iconPath || "/static/assets/icons.svg",
    assetPath: document.body.dataset.assetPath || "/static/assets/",
    csrfToken: document.body.dataset.csrfToken || "",
    branding: JSON.parse(document.body.dataset.branding || "{}"),
    activeView: "overview",
    referenceOptions: {},
    resources: {},
    assignablePermissions: [],
    tableFilters: {},
    tableFilterLabels: {},
    tableColumnFilters: {},
    tableSorts: {},
    globalSearch: "",
};

const endpoints = {
    clusters: "/api/resources/clusters",
    environments: "/api/resources/environments",
    hosts: "/api/resources/hosts",
    datastores: "/api/resources/datastores",
    vlans: "/api/resources/vlans",
    backup_jobs: "/api/resources/backup_jobs",
    vms: "/api/resources/vms",
    users: "/api/users",
    trash: "/api/trash",
};

const operatingSystemOptions = [
    "Windows Server 2025",
    "Windows Server 2022",
    "Windows Server 2019",
    "Windows Server 2016",
    "Windows Server 2012 R2",
    "Windows 11 Enterprise 24H2",
    "Windows 11 Enterprise 23H2",
    "Windows 10 Enterprise LTSC 2021",
    "Ubuntu Server 26.04 LTS",
    "Ubuntu Server 24.04 LTS",
    "Ubuntu Server 22.04 LTS",
    "Ubuntu Server 20.04 LTS",
    "Red Hat Enterprise Linux 10",
    "Red Hat Enterprise Linux 9",
    "Red Hat Enterprise Linux 8",
    "Rocky Linux 10",
    "Rocky Linux 9",
    "Rocky Linux 8",
    "AlmaLinux 10",
    "AlmaLinux 9",
    "AlmaLinux 8",
    "Oracle Linux 10",
    "Oracle Linux 9",
    "Oracle Linux 8",
    "Debian 13",
    "Debian 12",
    "Debian 11",
    "SUSE Linux Enterprise Server 15 SP7",
    "SUSE Linux Enterprise Server 15 SP6",
    "CentOS Stream 10",
    "CentOS Stream 9",
    "Fedora Server 44",
    "Fedora Server 43",
    "Photon OS 5",
    "FreeBSD 14",
    "Kali Linux 2026",
    "Custom / Other",
];

const tableColumns = {
    vms: [
        ["name", "VM Name"],
        ["environment", "Environment"],
        ["operating_system", "OS"],
        ["hostname", "Host"],
        ["cluster_name", "Cluster"],
        ["datastore_name", "Datastore"],
        ["vlan_name", "VLAN"],
        ["power_state", "Power"],
        ["backup_job_name", "Backup Job"],
        ["snapshot", "Snapshot"],
        ["criticality", "Criticality"],
    ],
    hosts: [
        ["hostname", "Hostname"],
        ["cluster_name", "Cluster"],
        ["version", "Version"],
        ["management_ip", "Management IP"],
        ["license", "License"],
        ["health", "Health"],
        ["assigned_vm_count", "Assigned VMs"],
    ],
    datastores: [
        ["name", "Datastore"],
        ["datastore_type", "Type"],
        ["cluster_name", "Cluster"],
        ["capacity_gb", "Capacity GB"],
        ["used_gb", "Used GB"],
        ["used_percent", "% Used"],
        ["assigned_vm_count", "Assigned VMs"],
    ],
    vlans: [
        ["name", "VLAN"],
        ["cidr", "CIDR"],
        ["security_zone", "Security Zone"],
        ["assigned_vm_count", "Assigned VMs"],
    ],
    backup_jobs: [
        ["name", "Backup Job"],
        ["schedule", "Schedule"],
        ["repository", "Repository"],
        ["retention", "Retention"],
        ["status", "Status"],
        ["assigned_vm_count", "Assigned VMs"],
    ],
    clusters: [
        ["name", "Cluster"],
        ["environment", "Environment"],
        ["host_count", "Hosts"],
        ["vm_count", "VMs"],
        ["datastore_count", "Datastores"],
        ["host_names", "Assigned Hosts"],
        ["status", "Status"],
        ["notes", "Notes"],
    ],
    environments: [
        ["name", "Environment"],
        ["status", "Status"],
        ["cluster_count", "Clusters"],
        ["vm_count", "VMs"],
        ["notes", "Notes"],
    ],
    users: [
        ["username", "Username"],
        ["display_name", "Display Name"],
        ["role", "Role"],
    ],
    trash: [
        ["display_name", "Deleted Item"],
        ["resource", "Resource"],
        ["resource_id", "Original ID"],
        ["deleted_by", "Deleted By"],
        ["deleted_at", "Deleted At"],
    ],
};

const modalDefinitions = {
    cluster: {
        title: "Add Cluster",
        resource: "clusters",
        fields: [
            ["name", "Cluster Name", "text", { required: true }],
            ["environment", "Environment", "reference-label", { source: "environments", required: true }],
            ["status", "Status", "select", { options: ["Active", "Maintenance", "Retired"] }],
            ["notes", "Notes", "textarea", { full: true }],
        ],
    },
    environment: {
        title: "Add Environment",
        resource: "environments",
        fields: [
            ["name", "Environment Name", "text", { required: true }],
            ["status", "Status", "select", { options: ["Active", "Maintenance", "Retired"] }],
            ["notes", "Notes", "textarea", { full: true }],
        ],
    },
    host: {
        title: "Add Host",
        resource: "hosts",
        fields: [
            ["hostname", "Hostname", "text", { required: true }],
            ["cluster_id", "Cluster", "reference", { source: "clusters", required: true }],
            ["version", "Hypervisor Version", "text", { value: "Generic Hypervisor 2026" }],
            ["build", "Build", "text", { value: "22380479" }],
            ["cpu", "CPU", "text", { value: "2 x Intel Xeon, 32 cores" }],
            ["memory", "Memory", "text", { value: "512 GB" }],
            ["nics", "NICs", "number", { value: 4 }],
            ["management_ip", "Management IP", "text", { required: true }],
            ["license", "License", "select", {
                options: [
                    "Enterprise Plus",
                    "Enterprise",
                    "Standard",
                    "Community",
                    "Subscription",
                    "Evaluation",
                ],
            }],
            ["health", "Health", "select", {
                options: ["Healthy", "Warning", "Degraded", "Critical", "Disconnected"],
            }],
            ["notes", "Notes", "textarea", { full: true }],
        ],
    },
    datastore: {
        title: "Add Datastore",
        resource: "datastores",
        fields: [
            ["name", "Datastore Name", "text", { required: true }],
            ["datastore_type", "Type", "select", { options: ["VMFS", "NFS", "vSAN", "VVol"] }],
            ["cluster_id", "Cluster", "reference", { source: "clusters", required: true }],
            ["capacity_gb", "Capacity GB", "number", { required: true, value: 1024 }],
            ["used_gb", "Used GB", "number", { required: true, value: 0 }],
            ["notes", "Notes", "textarea", { full: true }],
        ],
    },
    vlan: {
        title: "Add VLAN",
        resource: "vlans",
        fields: [
            ["name", "VLAN Name", "text", { required: true }],
            ["cidr", "CIDR", "text", { value: "10.0.0.0/24" }],
            ["security_zone", "Security Zone", "select", {
                options: ["Restricted", "Internal", "Development", "Test", "DMZ"],
            }],
            ["notes", "Notes", "textarea", { full: true }],
        ],
    },
    backup: {
        title: "Add Backup Job",
        resource: "backup_jobs",
        fields: [
            ["name", "Backup Job", "text", { required: true }],
            ["schedule", "Schedule", "text", { value: "Daily 22:00" }],
            ["repository", "Repository", "text", { value: "Repo-Primary" }],
            ["retention", "Retention", "text", { value: "30 daily" }],
            ["status", "Status", "select", { options: ["Success", "Warning", "Failed"] }],
        ],
    },
    vm: {
        title: "Add Virtual Machine",
        resource: "vms",
        fields: [
            ["name", "VM Name", "text", { required: true }],
            ["description", "Description", "text"],
            ["environment", "Environment", "reference-label", { source: "environments", required: true }],
            ["business_unit", "Business Unit", "text", { value: "Infrastructure" }],
            ["owner", "Owner", "text", { value: "Infrastructure Operations" }],
            ["application", "Application", "text", { value: "Platform Services" }],
            ["operating_system", "Operating System", "select-custom", {
                options: operatingSystemOptions,
                value: "Windows Server 2025",
            }],
            ["host_id", "Host", "reference", { source: "hosts", required: true }],
            ["cluster_id", "Cluster", "reference", { source: "clusters", required: true }],
            ["datastore_id", "Datastore", "reference", { source: "datastores", required: true }],
            ["folder", "Folder", "text", { value: "/Production/Applications" }],
            ["resource_pool", "Resource Pool", "text", { value: "RP-Production" }],
            ["vcpu", "vCPU", "number", { value: 2 }],
            ["ram_gb", "RAM GB", "number", { value: 8 }],
            ["disk_gb", "Disk GB", "number", { value: 100 }],
            ["ip_address", "IP Address", "text"],
            ["vlan_id", "VLAN", "reference", { source: "vlans", required: true }],
            ["backup_enabled", "Backup Enabled", "select", { options: ["true", "false"] }],
            ["backup_job_id", "Backup Job", "reference", { source: "backup_jobs" }],
            ["snapshot", "Snapshot", "select", { options: ["No", "Yes"] }],
            ["guest_tools", "Guest Tools", "select", {
                options: ["Current", "Outdated", "Not Installed", "Not Running"],
            }],
            ["power_state", "Power State", "select", {
                options: ["Powered On", "Powered Off", "Suspended"],
            }],
            ["criticality", "Criticality", "select", {
                options: ["Critical", "High", "Medium", "Low"],
            }],
            ["notes", "Notes", "textarea", { full: true }],
        ],
    },
    user: {
        title: "Add User",
        resource: "users",
        fields: [
            ["username", "Username", "text", { required: true }],
            ["display_name", "Display Name", "text", { required: true }],
            ["role", "Role", "select", { options: ["client", "admin"] }],
            ["password", "Temporary Password", "password", { required: true }],
        ],
    },
};

async function initializeApp() {
    if (document.body.dataset.appInitialized === "true") {
        return;
    }
    document.body.dataset.appInitialized = "true";
    refreshPermissionControls();
    bindNavigation();
    bindTopbarActions();
    bindTechnologyActions();
    bindCardActions();
    initializeOverviewLayout();
    bindLayoutEditor();
    bindBrandingForm();
    bindPasswordForm();
    bindGlobalSearch();
    bindRefreshActions();
    bindModals();
    await refreshAll();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeApp);
} else {
    initializeApp();
}

function bindNavigation() {
    document.querySelectorAll(".nav-item").forEach((button) => {
        button.addEventListener("click", () => {
            switchView(button.dataset.view);
        });
    });
}

function bindTechnologyActions() {
    document.querySelectorAll("[data-tech-view]").forEach((button) => {
        button.addEventListener("click", () => {
            const view = button.dataset.techView;
            const filter = button.dataset.techFilter || "";
            document.querySelectorAll("[data-tech-view]").forEach((item) => {
                item.classList.remove("active");
            });
            button.classList.add("active");
            state.tableFilters[view] = filter;
            switchView(view);
            renderTable(view);
            const message = filter
                ? `Filtered ${viewLabel(view)} by ${button.textContent.trim()}.`
                : `Opened ${viewLabel(view)} from ${button.textContent.trim()}.`;
            showToast(message);
        });
    });
}

function bindTopbarActions() {
    const menuButton = document.querySelector("[data-toggle-menu]");
    if (menuButton) {
        menuButton.addEventListener("click", () => {
            const collapsed = document.body.classList.toggle("sidebar-collapsed");
            menuButton.setAttribute("aria-expanded", String(!collapsed));
            closeNotifications();
            showToast(collapsed ? "Navigation hidden." : "Navigation shown.");
        });
    }

    const notificationsButton = document.querySelector("[data-notifications-toggle]");
    const notificationPanel = document.getElementById("notification-panel");
    if (!notificationsButton || !notificationPanel) {
        return;
    }

    notificationsButton.addEventListener("click", (event) => {
        event.stopPropagation();
        const willOpen = notificationPanel.hidden;
        closeNotifications();
        notificationPanel.hidden = !willOpen;
        notificationsButton.setAttribute("aria-expanded", String(willOpen));
    });

    notificationPanel.addEventListener("click", (event) => {
        event.stopPropagation();
        const action = event.target.closest("[data-notification-view]");
        if (!action) {
            return;
        }
        applyTableFilter(
            action.dataset.notificationView,
            action.dataset.notificationFilter || "",
            action.dataset.notificationLabel || action.textContent.trim(),
        );
        closeNotifications();
    });

    document.addEventListener("click", (event) => {
        if (notificationPanel.hidden || notificationPanel.contains(event.target) || notificationsButton.contains(event.target)) {
            return;
        }
        closeNotifications();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeNotifications();
        }
    });
}

function closeNotifications() {
    const notificationPanel = document.getElementById("notification-panel");
    const notificationsButton = document.querySelector("[data-notifications-toggle]");
    if (notificationPanel) {
        notificationPanel.hidden = true;
    }
    if (notificationsButton) {
        notificationsButton.setAttribute("aria-expanded", "false");
    }
}

function bindCardActions() {
    document.querySelectorAll("[data-card-view]").forEach((card) => {
        card.setAttribute("role", "button");
        card.setAttribute("tabindex", "0");
        card.addEventListener("click", () => openCardTarget(card));
        card.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openCardTarget(card);
            }
        });
    });
}

function initializeOverviewLayout() {
    clearLegacyOverviewDragState();
    prepareLayoutItems(".kpi-grid");
    prepareLayoutItems(".dashboard-grid");
    applySavedLayout();
}

function clearLegacyOverviewDragState() {
    window.localStorage.removeItem("vtOverviewKpiOrder");
    window.localStorage.removeItem("vtOverviewPanelOrder");
}

function prepareLayoutItems(containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) {
        return;
    }
    Array.from(container.children).forEach((card, index) => {
        const id = overviewCardId(card, index);
        card.dataset.layoutId = id;
    });
    container.dataset.defaultOrder = JSON.stringify(
        Array.from(container.children).map((card) => card.dataset.layoutId),
    );
}

function overviewCardId(card, index) {
    if (card.dataset.cardLabel) {
        return slugify(card.dataset.cardLabel);
    }
    const heading = card.querySelector("h2")?.textContent || card.querySelector("span")?.textContent;
    return slugify(heading || `card-${index}`);
}

function bindLayoutEditor() {
    document.querySelector("[data-open-layout-editor]")?.addEventListener("click", openLayoutEditor);
    document.querySelector("[data-close-layout-editor]")?.addEventListener("click", closeLayoutEditor);
    document.querySelector("[data-save-layout]")?.addEventListener("click", saveLayoutEditor);
    document.querySelector("[data-reset-layout]")?.addEventListener("click", resetOverviewLayout);
    document.getElementById("layout-editor")?.addEventListener("click", (event) => {
        if (event.target.id === "layout-editor") {
            closeLayoutEditor();
        }
    });
}

function applySavedLayout() {
    applyLayoutOrder(".kpi-grid", getSavedLayout().kpis);
    applyLayoutOrder(".dashboard-grid", getSavedLayout().panels);
}

function getSavedLayout() {
    try {
        return JSON.parse(window.localStorage.getItem("vtOverviewLayoutV2") || "{}");
    } catch {
        return {};
    }
}

function openLayoutEditor() {
    const editor = document.getElementById("layout-editor");
    if (!editor) {
        return;
    }
    populateLayoutBoard("kpis", ".kpi-grid");
    populateLayoutBoard("panels", ".dashboard-grid");
    editor.hidden = false;
    document.body.classList.add("layout-editor-open");
}

function closeLayoutEditor() {
    const editor = document.getElementById("layout-editor");
    if (!editor) {
        return;
    }
    editor.hidden = true;
    document.body.classList.remove("layout-editor-open");
}

function populateLayoutBoard(boardName, sourceSelector) {
    const board = document.querySelector(`[data-layout-board="${boardName}"]`);
    const source = document.querySelector(sourceSelector);
    if (!board || !source) {
        return;
    }
    board.innerHTML = "";
    Array.from(source.children).forEach((card) => {
        const item = document.createElement("article");
        item.className = "layout-editor-card";
        item.draggable = true;
        item.dataset.layoutId = card.dataset.layoutId;
        item.innerHTML = `
            <span class="layout-drag-handle">${icon("more")}</span>
            <strong>${escapeHtml(layoutItemTitle(card))}</strong>
            <em>${escapeHtml(layoutItemMeta(card))}</em>
        `;
        board.appendChild(item);
    });
    bindLayoutBoard(board);
}

function bindLayoutBoard(board) {
    if (board.dataset.bound === "true") {
        return;
    }
    board.dataset.bound = "true";
    board.addEventListener("dragstart", (event) => {
        const item = event.target.closest(".layout-editor-card");
        if (!item || !board.contains(item)) {
            return;
        }
        item.classList.add("dragging");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", item.dataset.layoutId);
    });
    board.addEventListener("dragover", (event) => {
        const dragging = board.querySelector(".dragging");
        if (!dragging) {
            return;
        }
        event.preventDefault();
        const afterElement = getEditorDragAfterElement(board, event.clientY);
        board.querySelectorAll(".drag-over").forEach((item) => item.classList.remove("drag-over"));
        if (afterElement == null) {
            board.appendChild(dragging);
        } else {
            afterElement.classList.add("drag-over");
            board.insertBefore(dragging, afterElement);
        }
    });
    board.addEventListener("drop", (event) => {
        event.preventDefault();
        board.querySelectorAll(".dragging, .drag-over").forEach((item) => {
            item.classList.remove("dragging", "drag-over");
        });
    });
    board.addEventListener("dragend", () => {
        board.querySelectorAll(".dragging, .drag-over").forEach((item) => {
            item.classList.remove("dragging", "drag-over");
        });
    });
}

function saveLayoutEditor() {
    const layout = {
        kpis: readLayoutBoard("kpis"),
        panels: readLayoutBoard("panels"),
    };
    window.localStorage.setItem("vtOverviewLayoutV2", JSON.stringify(layout));
    applySavedLayout();
    closeLayoutEditor();
    showToast("Overview layout saved.");
}

function resetOverviewLayout() {
    window.localStorage.removeItem("vtOverviewLayoutV2");
    applyLayoutOrder(".kpi-grid", defaultLayoutOrder(".kpi-grid"));
    applyLayoutOrder(".dashboard-grid", defaultLayoutOrder(".dashboard-grid"));
    openLayoutEditor();
    showToast("Overview layout reset.");
}

function readLayoutBoard(boardName) {
    return Array.from(document.querySelectorAll(`[data-layout-board="${boardName}"] .layout-editor-card`))
        .map((item) => item.dataset.layoutId)
        .filter(Boolean);
}

function defaultLayoutOrder(containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) {
        return [];
    }
    return JSON.parse(container.dataset.defaultOrder || "[]");
}

function applyLayoutOrder(containerSelector, order = []) {
    const container = document.querySelector(containerSelector);
    if (!container || !Array.isArray(order) || !order.length) {
        return;
    }
    const byId = new Map(Array.from(container.children).map((card) => [card.dataset.layoutId, card]));
    const applied = new Set();
    order.forEach((id) => {
        const card = byId.get(id);
        if (card) {
            container.appendChild(card);
            applied.add(id);
        }
    });
    byId.forEach((card, id) => {
        if (!applied.has(id)) {
            container.appendChild(card);
        }
    });
}

function layoutItemTitle(card) {
    return card.dataset.cardLabel || card.querySelector("h2")?.textContent || card.querySelector("span")?.textContent || "Dashboard item";
}

function layoutItemMeta(card) {
    if (card.classList.contains("kpi-card")) {
        return "KPI card";
    }
    return "Dashboard panel";
}

function getEditorDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll(".layout-editor-card:not(.dragging)")];
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset, element: child };
        }
        return closest;
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function bindGlobalSearch() {
    const search = document.querySelector("[data-global-search]");
    if (!search) {
        return;
    }
    search.addEventListener("input", () => {
        state.globalSearch = search.value.trim();
        const target = tableColumns[state.activeView] ? state.activeView : "vms";
        if (state.activeView !== "overview") {
            renderTable(target);
        }
    });
    search.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") {
            return;
        }
        event.preventDefault();
        if (state.globalSearch) {
            state.tableFilters.vms = state.globalSearch;
            state.tableFilterLabels.vms = `Search: ${state.globalSearch}`;
            switchView("vms");
            renderTable("vms");
        }
    });
}

function bindRefreshActions() {
    document.querySelectorAll("[data-refresh-dashboard]").forEach((button) => {
        button.addEventListener("click", async () => {
            await refreshAll();
            showToast("Dashboard refreshed.");
        });
    });
}

function openCardTarget(card) {
    if (state.suppressCardClickUntil && Date.now() < state.suppressCardClickUntil) {
        return;
    }
    const view = card.dataset.cardView;
    const filter = card.dataset.cardFilter || "";
    const label = card.dataset.cardLabel || card.textContent.trim();
    applyTableFilter(view, filter, label);
}

function switchView(view) {
    state.activeView = view;
    document.querySelectorAll(".nav-item").forEach((item) => {
        item.classList.toggle("active", item.dataset.view === view);
    });
    document.querySelectorAll(".view").forEach((section) => section.classList.remove("active"));
    document.getElementById(`view-${view}`).classList.add("active");
}

function bindModals() {
    document.querySelectorAll("[data-modal]").forEach((button) => {
        button.addEventListener("click", () => openModal(button.dataset.modal));
    });
    document.querySelector("[data-close-modal]").addEventListener("click", closeModal);
    document.getElementById("modal-backdrop").addEventListener("click", (event) => {
        if (event.target.id === "modal-backdrop") {
            closeModal();
        }
    });
}

async function refreshAll() {
    await refreshBranding();
    await refreshReferences();
    if (hasPermission("users.manage")) {
        state.assignablePermissions = await getJson("/api/permissions");
    }
    const resources = Object.keys(endpoints).filter((resource) => {
        if (resource === "users") {
            return hasPermission("users.manage");
        }
        if (resource === "trash") {
            return hasPermission("resource.delete");
        }
        return true;
    });
    await Promise.all(resources.map(loadResource));
    await refreshSummary();
}

async function refreshReferences() {
    state.referenceOptions = await getJson("/api/reference-options");
}

async function refreshBranding() {
    try {
        state.branding = await getJson("/api/branding");
    } catch (error) {
        // Keep server-rendered defaults when branding is unavailable.
    }
    applyBranding();
}

async function refreshSummary() {
    const summary = await getJson("/api/summary");
    Object.entries(summary).forEach(([key, value]) => {
        document.querySelectorAll(`[data-summary="${key}"]`).forEach((node) => {
            node.textContent = key.endsWith("percent") ? `${value}%` : value;
        });
    });
    const meter = document.querySelector("[data-meter='storage']");
    if (meter) {
        meter.style.width = `${summary.storage_used_percent}%`;
    }
    renderDashboardCharts(summary);
}

async function loadResource(resource) {
    state.resources[resource] = await getJson(endpoints[resource]);
    renderTable(resource);
}

function bindBrandingForm() {
    const form = document.getElementById("branding-form");
    if (!form) {
        applyBranding();
        return;
    }
    const logoInput = form.elements.logo_file;
    const removeLogo = form.elements.remove_logo;
    let previewUrl = "";
    if (logoInput) {
        logoInput.addEventListener("change", () => {
            if (previewUrl) {
                URL.revokeObjectURL(previewUrl);
                previewUrl = "";
            }
            const file = logoInput.files && logoInput.files[0];
            if (!file) {
                applyBranding();
                return;
            }
            if (removeLogo) {
                removeLogo.checked = false;
            }
            previewUrl = URL.createObjectURL(file);
            document.querySelectorAll("[data-brand-logo]").forEach((image) => {
                image.src = previewUrl;
                image.alt = `${file.name} preview`;
            });
        });
    }
    if (removeLogo) {
        removeLogo.addEventListener("change", () => {
            if (removeLogo.checked && logoInput) {
                logoInput.value = "";
            }
            applyBranding();
        });
    }
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = new FormData(form);
        if (removeLogo && !removeLogo.checked) {
            payload.delete("remove_logo");
        }
        try {
            const response = await fetch("/api/branding", {
                method: "PUT",
                headers: csrfHeaders(),
                body: payload,
            });
            const body = await response.json();
            if (!response.ok) {
                throw new Error(body.message || "Unable to save branding.");
            }
            state.branding = body;
            if (form.elements.logo_url) {
                form.elements.logo_url.value = body.logo_url || "";
            }
            if (logoInput) {
                logoInput.value = "";
            }
            if (removeLogo) {
                removeLogo.checked = false;
            }
            if (previewUrl) {
                URL.revokeObjectURL(previewUrl);
                previewUrl = "";
            }
            applyBranding();
            showToast("Branding updated.");
        } catch (error) {
            showToast(error.message, true);
        }
    });
    applyBranding();
}

function bindPasswordForm() {
    const form = document.getElementById("password-form");
    if (!form) {
        return;
    }
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(form).entries());
        if (payload.new_password !== payload.confirm_password) {
            showToast("New password and confirmation do not match.", true);
            return;
        }
        try {
            const response = await fetch("/api/account/password", {
                method: "PUT",
                headers: jsonHeaders(),
                body: JSON.stringify({
                    current_password: payload.current_password,
                    new_password: payload.new_password,
                }),
            });
            const body = await response.json();
            if (!response.ok) {
                throw new Error(body.message || "Unable to update password.");
            }
            form.reset();
            showToast(body.message || "Password updated.");
        } catch (error) {
            showToast(error.message, true);
        }
    });
}

function applyBranding() {
    const branding = {
        company_name: "Virtualization Administration Toolkit",
        tagline: "Secure enterprise console for governed VM, host, datastore, backup, and access administration.",
        logo_url: "",
        report_title: "Infrastructure Overview Report",
        report_author: "Infrastructure Admin",
        ...state.branding,
    };
    document.title = branding.company_name;
    document.querySelectorAll("[data-brand-company]").forEach((node) => {
        node.textContent = branding.company_name;
    });
    document.querySelectorAll("[data-brand-tagline]").forEach((node) => {
        node.textContent = branding.tagline;
    });
    document.querySelectorAll("[data-brand-report-title]").forEach((node) => {
        node.textContent = branding.report_title;
    });
    document.querySelectorAll("[data-brand-logo]").forEach((image) => {
        if (!image.dataset.defaultSrc) {
            image.dataset.defaultSrc = image.getAttribute("src") || "";
        }
        image.src = branding.logo_url || image.dataset.defaultSrc;
        image.alt = branding.company_name;
    });
}

function renderTable(resource) {
    const table = document.getElementById(`table-${resource}`);
    if (!table) {
        return;
    }
    if (resource === "users") {
        renderUsersTable(table);
        return;
    }
    if (resource === "trash") {
        renderTrashTable(table);
        return;
    }
    const columns = tableColumns[resource];
    const rows = sortedRows(resource, columns, filteredRows(resource, columns, state.resources[resource] || []));
    const actionHeader = hasRowActions() ? "<th>Action</th>" : "";
    const colspan = columns.length + (hasRowActions() ? 1 : 0);
    table.innerHTML = `
        <thead>
            ${state.tableFilters[resource] ? `<tr><th colspan="${colspan}"><button class="clear-filter" data-clear-filter="${resource}">Clear filter: ${escapeHtml(state.tableFilterLabels[resource] || state.tableFilters[resource])}</button></th></tr>` : ""}
            ${renderHeaderRow(resource, columns, hasRowActions())}
            ${renderColumnFilterRow(resource, columns, hasRowActions())}
        </thead>
        <tbody>
            ${rows.length ? rows.map((row) => renderRow(resource, columns, row)).join("") : renderEmptyRow(colspan)}
        </tbody>
    `;
    bindTableControls(table, resource);
    table.querySelectorAll("[data-clear-filter]").forEach((button) => {
        button.addEventListener("click", () => {
            delete state.tableFilters[button.dataset.clearFilter];
            delete state.tableFilterLabels[button.dataset.clearFilter];
            document.querySelectorAll("[data-tech-view]").forEach((item) => {
                item.classList.remove("active");
            });
            renderTable(button.dataset.clearFilter);
        });
    });
    table.querySelectorAll("[data-edit]").forEach((button) => {
        button.addEventListener("click", () => {
            openEditModal(button.dataset.resource, button.dataset.id);
        });
    });
    table.querySelectorAll("[data-delete]").forEach((button) => {
        button.addEventListener("click", () => deleteRow(button.dataset.resource, button.dataset.id));
    });
}

function renderTrashTable(table) {
    const columns = tableColumns.trash;
    const rows = sortedRows("trash", columns, filteredRows("trash", columns, state.resources.trash || []));
    table.innerHTML = `
        <thead>
            ${renderHeaderRow("trash", columns, true)}
            ${renderColumnFilterRow("trash", columns, true)}
        </thead>
        <tbody>
            ${rows.length ? rows.map((row) => renderTrashRow(columns, row)).join("") : renderEmptyRow(columns.length + 1)}
        </tbody>
    `;
    bindTableControls(table, "trash");
    table.querySelectorAll("[data-restore]").forEach((button) => {
        button.addEventListener("click", () => restoreTrashItem(button.dataset.id));
    });
}

function renderHeaderRow(resource, columns, hasActionColumn = false) {
    return `<tr>${renderHeaderCells(resource, columns)}${hasActionColumn ? '<th class="action-column">Action</th>' : ""}</tr>`;
}

function renderHeaderCells(resource, columns) {
    const sort = state.tableSorts[resource];
    return columns.map(([key, label]) => {
        const active = sort?.key === key;
        const directionLabel = active && sort.direction === "desc" ? "descending" : "ascending";
        const indicator = active ? (sort.direction === "desc" ? "down" : "up") : "idle";
        return `
            <th>
                <button
                    class="table-sort ${active ? "active" : ""}"
                    type="button"
                    data-sort-resource="${escapeHtml(resource)}"
                    data-sort-key="${escapeHtml(key)}"
                    aria-label="Sort ${escapeHtml(label)} ${directionLabel}"
                >
                    <span>${escapeHtml(label)}</span>
                    <i aria-hidden="true" data-sort-indicator="${indicator}"></i>
                </button>
            </th>
        `;
    }).join("");
}

function renderColumnFilterRow(resource, columns, hasActionColumn = false) {
    return `<tr class="column-filter-row">${renderColumnFilterCells(resource, columns)}${hasActionColumn ? '<th class="column-filter-cell action-column"></th>' : ""}</tr>`;
}

function renderColumnFilterCells(resource, columns) {
    const filters = state.tableColumnFilters[resource] || {};
    return columns.map(([key, label]) => `
        <th class="column-filter-cell">
            <input
                data-column-filter-resource="${escapeHtml(resource)}"
                data-column-filter-key="${escapeHtml(key)}"
                value="${escapeHtml(filters[key] || "")}"
                placeholder="Filter ${escapeHtml(label)}"
                aria-label="Filter ${escapeHtml(label)}"
                autocomplete="off"
            >
        </th>
    `).join("");
}

function bindTableControls(table, resource) {
    table.querySelectorAll("[data-sort-key]").forEach((button) => {
        button.addEventListener("click", () => {
            const key = button.dataset.sortKey;
            const rows = state.resources[resource] || [];
            const current = state.tableSorts[resource];
            const nextDirection = current?.key === key
                ? (current.direction === "asc" ? "desc" : "asc")
                : defaultSortDirection(rows, key);
            state.tableSorts[resource] = { key, direction: nextDirection };
            renderTable(resource);
        });
    });
    table.querySelectorAll("[data-column-filter-key]").forEach((input) => {
        input.addEventListener("input", () => {
            const key = input.dataset.columnFilterKey;
            if (!state.tableColumnFilters[resource]) {
                state.tableColumnFilters[resource] = {};
            }
            const value = input.value.trim();
            if (value) {
                state.tableColumnFilters[resource][key] = value;
            } else {
                delete state.tableColumnFilters[resource][key];
                if (!Object.keys(state.tableColumnFilters[resource]).length) {
                    delete state.tableColumnFilters[resource];
                }
            }
            renderTable(resource);
            const nextInput = document.querySelector(`[data-column-filter-resource="${cssEscape(resource)}"][data-column-filter-key="${cssEscape(key)}"]`);
            nextInput?.focus();
            nextInput?.setSelectionRange(nextInput.value.length, nextInput.value.length);
        });
    });
}

function filteredRows(resource, columns, rows) {
    const filter = state.tableFilters[resource] || (resource === state.activeView ? state.globalSearch : "");
    const isOtherOsFilter = resource === "vms" && filter === "__other_os__";
    const normalizedTerms = String(isOtherOsFilter ? "" : filter || "")
        .toLowerCase()
        .split("|")
        .map((term) => term.trim())
        .filter(Boolean);
    const columnFilters = state.tableColumnFilters[resource] || {};
    return rows.filter((row) => {
        if (isOtherOsFilter && !isOtherOperatingSystem(row.operating_system)) {
            return false;
        }
        if (normalizedTerms.length) {
            const searchable = Object.values(row)
                .map((value) => String(value ?? "").toLowerCase())
                .join(" ");
            if (!normalizedTerms.some((term) => searchable.includes(term))) {
                return false;
            }
        }
        return columns.every(([key]) => {
            const columnFilter = columnFilters[key];
            if (!columnFilter) {
                return true;
            }
            return searchableValue(row[key]).includes(columnFilter.toLowerCase());
        });
    });
}

function sortedRows(resource, columns, rows) {
    const sort = state.tableSorts[resource];
    if (!sort || !columns.some(([key]) => key === sort.key)) {
        return rows;
    }
    return [...rows].sort((left, right) => {
        const comparison = compareValues(left[sort.key], right[sort.key]);
        return sort.direction === "desc" ? -comparison : comparison;
    });
}

function compareValues(left, right) {
    const leftNumber = numericValue(left);
    const rightNumber = numericValue(right);
    if (leftNumber !== null && rightNumber !== null) {
        return leftNumber - rightNumber;
    }
    return searchableValue(left).localeCompare(searchableValue(right), undefined, {
        numeric: true,
        sensitivity: "base",
    });
}

function defaultSortDirection(rows, key) {
    return rows.some((row) => numericValue(row[key]) !== null) ? "desc" : "asc";
}

function numericValue(value) {
    if (typeof value === "number") {
        return Number.isFinite(value) ? value : null;
    }
    if (value === null || value === undefined || value === "") {
        return null;
    }
    const text = String(value).trim().replace(/,/g, "");
    if (!/^-?\d+(\.\d+)?%?$/.test(text)) {
        return null;
    }
    const number = Number(text.replace("%", ""));
    return Number.isFinite(number) ? number : null;
}

function searchableValue(value) {
    return String(value ?? "").toLowerCase();
}

function isOtherOperatingSystem(value) {
    const text = searchableValue(value);
    return !["windows", "linux", "ubuntu", "red hat", "photon"].some((term) => text.includes(term));
}

function cssEscape(value) {
    if (window.CSS?.escape) {
        return window.CSS.escape(value);
    }
    return String(value).replace(/["\\]/g, "\\$&");
}

function applyTableFilter(view, filter, label) {
    document.querySelectorAll("[data-tech-view]").forEach((item) => {
        item.classList.remove("active");
    });
    if (filter) {
        state.tableFilters[view] = filter;
        state.tableFilterLabels[view] = label;
    } else {
        delete state.tableFilters[view];
        delete state.tableFilterLabels[view];
    }
    switchView(view);
    renderTable(view);
    showToast(filter ? `Opened ${viewLabel(view)}: ${label}.` : `Opened ${viewLabel(view)}.`);
}

function renderEmptyRow(colspan) {
    return `<tr><td colspan="${colspan}" class="empty-table-cell">No matching records.</td></tr>`;
}

function hasRowActions() {
    return hasPermission("resource.create") || hasPermission("resource.delete");
}

function renderDashboardCharts(summary) {
    renderDistribution("chart-power", summary.power_distribution);
    renderDistribution("chart-environment", summary.environment_distribution);
    renderDistribution("chart-os", summary.os_distribution);
    renderDistribution("chart-backup", summary.backup_distribution);
    renderDistribution("chart-criticality", summary.criticality_distribution);
    renderStorageRows(summary.storage_by_datastore);
    renderOsInventory(summary.os_inventory);
    renderWarnings(summary.risk_warnings);
    renderRecentVms(summary.recent_vms);
}

function renderDistribution(targetId, rows = []) {
    const target = document.getElementById(targetId);
    if (!target) {
        return;
    }
    if (!rows.length) {
        target.innerHTML = `<div class="empty-state">No data available</div>`;
        return;
    }
    target.innerHTML = rows.map((row) => `
        <div class="bar-row">
            <div class="bar-row-label">
                <strong>${distributionLabelIcon(targetId, row.name)}${escapeHtml(row.name)}</strong>
                <span>${row.count} (${row.percent}%)</span>
            </div>
            <div class="mini-meter">
                <div style="width: ${Math.max(row.percent, 4)}%"></div>
            </div>
        </div>
    `).join("");
}

function renderStorageRows(rows = []) {
    const target = document.getElementById("storage-by-datastore");
    if (!target) {
        return;
    }
    target.innerHTML = rows.map((row) => `
        <div class="bar-row">
            <div class="bar-row-label">
                <strong>${icon("datastore")}${escapeHtml(row.name)}</strong>
                <span>${row.used_gb} / ${row.capacity_gb} GB (${row.used_percent}%)</span>
            </div>
            <div class="mini-meter storage-meter">
                <div style="width: ${Math.max(row.used_percent || 0, 4)}%"></div>
            </div>
        </div>
    `).join("");
}

function renderOsInventory(rows = []) {
    const target = document.getElementById("os-inventory");
    if (!target) {
        return;
    }
    target.innerHTML = rows.length ? rows.map((row) => `
        <tr class="clickable-row" data-inline-view="vms" data-inline-filter="${escapeHtml(row.name)}">
            <td><span class="os-chip ${osClass(row.name)}">${osIcon(row.name)}<strong>${escapeHtml(row.name)}</strong></span></td>
            <td>${row.vm_count}</td>
        </tr>
    `).join("") : '<tr><td colspan="2" class="empty-table-cell">No operating systems found.</td></tr>';
    bindInlineTableNavigation(target);
}

function bindInlineTableNavigation(target) {
    target.querySelectorAll("[data-inline-view]").forEach((row) => {
        row.addEventListener("click", () => {
            applyTableFilter(
                row.dataset.inlineView,
                row.dataset.inlineFilter,
                row.dataset.inlineFilter,
            );
        });
    });
}

function renderWarnings(rows = []) {
    const target = document.getElementById("risk-warnings");
    if (!target) {
        return;
    }
    target.innerHTML = rows.map((row) => `
        <div class="warning-row ${escapeHtml(row.severity)}">
            <span>${warningIcon(row)}${escapeHtml(row.title)}</span>
            <strong>${row.count}</strong>
        </div>
    `).join("");
}

function renderRecentVms(rows = []) {
    const target = document.getElementById("recent-vms");
    if (!target) {
        return;
    }
    target.innerHTML = rows.map((row) => `
        <tr>
            <td><strong>${escapeHtml(row.name)}</strong></td>
            <td>${formatValue("environment", row.environment)}</td>
            <td>${formatValue("operating_system", recentVmOperatingSystem(row))}</td>
            <td>${formatValue("power_state", row.power_state)}</td>
            <td>${formatValue("criticality", row.criticality)}</td>
            <td>${escapeHtml(row.hostname)}</td>
            <td>${escapeHtml(row.datastore_name)}</td>
        </tr>
    `).join("");
}

function renderRow(resource, columns, row) {
    const cells = columns.map(([key]) => `<td>${formatValue(key, row[key])}</td>`).join("");
    const actions = [];
    if (hasPermission("resource.create")) {
        actions.push(`<button class="row-action edit" data-edit data-resource="${resource}" data-id="${row.id}">${icon("edit")}Edit</button>`);
    }
    if (hasPermission("resource.delete")) {
        actions.push(`<button class="row-action" data-delete data-resource="${resource}" data-id="${row.id}">${icon("delete")}Delete</button>`);
    }
    const action = actions.length
        ? `<td><div class="row-actions">${actions.join("")}</div></td>`
        : "";
    return `<tr>${cells}${action}</tr>`;
}

function renderTrashRow(columns, row) {
    const cells = columns.map(([key]) => `<td>${formatValue(key, row[key])}</td>`).join("");
    return `
        <tr>
            ${cells}
            <td>
                <button class="row-action restore" data-restore data-id="${row.id}">${icon("restore")}Restore</button>
            </td>
        </tr>
    `;
}

function renderUsersTable(table) {
    const columns = tableColumns.users;
    const users = sortedRows("users", columns, filteredRows("users", columns, state.resources.users || []));
    const permissionHeaders = state.assignablePermissions.map((permission) => {
        return `<th class="permission-cell">${escapeHtml(permission.label)}</th>`;
    }).join("");
    const permissionFilterCells = state.assignablePermissions.map(() => '<th class="column-filter-cell permission-cell"></th>').join("");
    const passwordHeader = hasPermission("users.manage") ? '<th class="action-column">Password</th>' : "";
    const passwordFilterCell = hasPermission("users.manage") ? '<th class="column-filter-cell action-column"></th>' : "";
    table.innerHTML = `
        <thead>
            <tr>${renderHeaderCells("users", columns)}${permissionHeaders}${passwordHeader}</tr>
            <tr class="column-filter-row">${renderColumnFilterCells("users", columns)}${permissionFilterCells}${passwordFilterCell}</tr>
        </thead>
        <tbody>
            ${users.map(renderUserRow).join("")}
        </tbody>
    `;
    bindTableControls(table, "users");
    table.querySelectorAll("[data-permission-toggle]").forEach((toggle) => {
        toggle.addEventListener("change", () => updateUserPermissions(toggle.dataset.userId));
    });
    table.querySelectorAll("[data-reset-password]").forEach((button) => {
        button.addEventListener("click", () => resetUserPassword(button.dataset.userId, button.dataset.username));
    });
}

function renderUserRow(user) {
    const permissionCells = state.assignablePermissions.map((permission) => {
        const checked = user.role === "admin" || user.permissions.includes(permission.code);
        const disabled = user.role === "admin" ? "disabled" : "";
        return `
            <td class="permission-cell">
                <label class="permission-toggle">
                    <input
                        type="checkbox"
                        data-permission-toggle
                        data-user-id="${user.id}"
                        value="${escapeHtml(permission.code)}"
                        ${checked ? "checked" : ""}
                        ${disabled}
                    >
                    ${user.role === "admin" ? "Superuser" : "Granted"}
                </label>
            </td>
        `;
    }).join("");
    const passwordCell = hasPermission("users.manage")
        ? `<td><button class="row-action" data-reset-password data-user-id="${user.id}" data-username="${escapeHtml(user.username)}">${icon("restore")}Reset</button></td>`
        : "";
    return `
        <tr>
            <td>${escapeHtml(user.username)}</td>
            <td>${escapeHtml(user.display_name)}</td>
            <td>${formatValue("role", user.role)}</td>
            ${permissionCells}
            ${passwordCell}
        </tr>
    `;
}

function formatValue(key, value) {
    const raw = value ?? "";
    if (["health", "status", "power_state", "criticality", "snapshot"].includes(key)) {
        const text = escapeHtml(String(raw));
        return `<span class="status-pill ${statusClass(String(raw))}">${icon(statusIcon(key, String(raw)))}${text}</span>`;
    }
    if (key === "environment" && raw !== "") {
        return `<span class="env-pill">${escapeHtml(String(raw))}</span>`;
    }
    if (key === "operating_system" && raw !== "") {
        const name = String(raw);
        return `<span class="os-chip ${osClass(name)}">${osIcon(name)}${escapeHtml(name)}</span>`;
    }
    if (key === "used_percent" && raw !== "") {
        return `${raw}%`;
    }
    return escapeHtml(String(raw));
}

function statusClass(value) {
    const normalized = value.toLowerCase();
    if (["healthy", "success", "powered on", "low", "no"].includes(normalized)) {
        return "status-green";
    }
    if (["warning", "medium", "yes", "suspended"].includes(normalized)) {
        return "status-amber";
    }
    if (["critical", "failed", "powered off", "high"].includes(normalized)) {
        return "status-red";
    }
    return "status-amber";
}

async function openModal(type, row = null) {
    await refreshReferences();
    const definition = modalDefinitions[type];
    const isEdit = Boolean(row);
    document.getElementById("modal-title").textContent = isEdit
        ? definition.title.replace("Add", "Edit")
        : definition.title;
    const form = document.getElementById("resource-form");
    form.innerHTML = `
        ${definition.fields.map((field) => renderField(field, row)).join("")}
        <div class="modal-actions">
            <button class="ghost-button" type="button" data-cancel-modal>${icon("close")}Cancel</button>
            <button class="primary-button" type="submit">${icon("status")}Save</button>
        </div>
    `;
    form.onsubmit = (event) => submitResource(event, definition, row?.id || null);
    form.querySelector("[data-cancel-modal]").addEventListener("click", closeModal);
    initializeCustomSelects(form);
    const hostSelect = form.querySelector('[name="host_id"]');
    if (hostSelect) {
        hostSelect.addEventListener("change", syncClusterFromHost);
    }
    document.getElementById("modal-backdrop").hidden = false;
}

function openEditModal(resource, id) {
    const modalType = modalTypeForResource(resource);
    const row = (state.resources[resource] || []).find((item) => {
        return String(item.id) === String(id);
    });
    if (!modalType || !row) {
        showToast("Unable to open edit form.", true);
        return;
    }
    openModal(modalType, row);
}

function closeModal() {
    document.getElementById("modal-backdrop").hidden = true;
}

function renderField([name, label, type, options = {}], row = null) {
    const required = options.required ? "required" : "";
    const full = options.full ? " full" : "";
    const rawValue = row && Object.prototype.hasOwnProperty.call(row, name)
        ? row[name]
        : options.value;
    const fieldValue = normalizedFormValue(name, rawValue);
    if (type === "textarea") {
        return `
            <label class="${full}">
                ${label}
                <textarea name="${name}" rows="3" ${required}>${escapeHtml(fieldValue || "")}</textarea>
            </label>
        `;
    }
    if (type === "select") {
        const choices = options.options || [];
        return `
            <label class="${full}">
                ${label}
                <select name="${name}" ${required}>
                    ${choices.map((choice) => {
                        const selected = String(choice) === String(fieldValue) ? "selected" : "";
                        return `<option value="${escapeHtml(choice)}" ${selected}>${escapeHtml(choice)}</option>`;
                    }).join("")}
                </select>
            </label>
        `;
    }
    if (type === "select-custom") {
        const choices = (options.options || []).filter((choice) => choice !== "Custom / Other");
        const currentValue = String(fieldValue || "");
        const isKnownValue = choices.includes(currentValue);
        const selectValue = currentValue && !isKnownValue ? "__custom__" : currentValue;
        const customValue = currentValue && !isKnownValue ? currentValue : "";
        const customHidden = selectValue === "__custom__" ? "" : "hidden";
        return `
            <label class="${full}">
                ${label}
                <select name="${name}" data-custom-select="${name}" ${required}>
                    ${choices.map((choice) => {
                        const selected = String(choice) === String(selectValue) ? "selected" : "";
                        return `<option value="${escapeHtml(choice)}" ${selected}>${escapeHtml(choice)}</option>`;
                    }).join("")}
                    <option value="__custom__" ${selectValue === "__custom__" ? "selected" : ""}>Custom / Other</option>
                </select>
            </label>
            <label class="${full} custom-field" data-custom-field="${name}" ${customHidden}>
                Custom ${label}
                <input
                    name="${name}_custom"
                    type="text"
                    value="${escapeHtml(customValue)}"
                    placeholder="Type custom operating system"
                >
            </label>
        `;
    }
    if (type === "reference") {
        const choices = state.referenceOptions[options.source] || [];
        return `
            <label class="${full}">
                ${label}
                <select name="${name}" ${required}>
                    <option value="">Select ${escapeHtml(label)}</option>
                    ${choices.map((choice) => {
                        const selected = String(choice.id) === String(fieldValue) ? "selected" : "";
                        return `<option value="${choice.id}" ${selected}>${escapeHtml(choice.label)}</option>`;
                    }).join("")}
                </select>
            </label>
        `;
    }
    if (type === "reference-label") {
        const choices = state.referenceOptions[options.source] || [];
        return `
            <label class="${full}">
                ${label}
                <select name="${name}" ${required}>
                    <option value="">Select ${escapeHtml(label)}</option>
                    ${choices.map((choice) => {
                        const selected = String(choice.label) === String(fieldValue) ? "selected" : "";
                        return `<option value="${escapeHtml(choice.label)}" ${selected}>${escapeHtml(choice.label)}</option>`;
                    }).join("")}
                </select>
            </label>
        `;
    }
    return `
        <label class="${full}">
            ${label}
            <input name="${name}" type="${type}" value="${escapeHtml(fieldValue ?? "")}" ${required}>
        </label>
    `;
}

function normalizedFormValue(name, value) {
    if (name === "backup_enabled") {
        return value === 1 || value === true || value === "true" ? "true" : "false";
    }
    return value ?? "";
}

function syncClusterFromHost() {
    const selectedHost = state.referenceOptions.hosts.find((host) => String(host.id) === this.value);
    if (!selectedHost) {
        return;
    }
    const cluster = state.referenceOptions.clusters.find((item) => item.label === selectedHost.cluster);
    const clusterSelect = document.querySelector('[name="cluster_id"]');
    if (clusterSelect && cluster) {
        clusterSelect.value = String(cluster.id);
    }
}

async function submitResource(event, definition, resourceId = null) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const payload = Object.fromEntries(formData.entries());
    normalizeCustomPayload(payload);
    try {
        const response = await fetch(
            resourceId
                ? `${endpoints[definition.resource]}/${resourceId}`
                : endpoints[definition.resource],
            {
            method: resourceId ? "PUT" : "POST",
            headers: jsonHeaders(),
            body: JSON.stringify(payload),
            },
        );
        const body = await response.json();
        if (!response.ok) {
            throw new Error(body.message || "Unable to create resource.");
        }
        closeModal();
        showToast(
            resourceId
                ? `${definition.title.replace("Add ", "")} updated.`
                : `${definition.title.replace("Add ", "")} created.`,
        );
        await refreshAll();
    } catch (error) {
        showToast(error.message, true);
    }
}

function initializeCustomSelects(form) {
    form.querySelectorAll("[data-custom-select]").forEach((select) => {
        const fieldName = select.dataset.customSelect;
        const customField = form.querySelector(`[data-custom-field="${fieldName}"]`);
        const customInput = form.querySelector(`[name="${fieldName}_custom"]`);
        const syncVisibility = () => {
            const isCustom = select.value === "__custom__";
            if (customField) {
                customField.hidden = !isCustom;
            }
            if (customInput) {
                customInput.required = isCustom;
            }
        };
        select.addEventListener("change", syncVisibility);
        syncVisibility();
    });
}

function normalizeCustomPayload(payload) {
    Object.keys(payload).forEach((key) => {
        if (!key.endsWith("_custom")) {
            return;
        }
        const baseKey = key.replace(/_custom$/, "");
        if (payload[baseKey] === "__custom__") {
            payload[baseKey] = payload[key].trim();
        }
        delete payload[key];
    });
}

async function restoreTrashItem(id) {
    try {
        const response = await fetch(`/api/trash/${id}/restore`, {
            method: "POST",
            headers: csrfHeaders(),
        });
        const body = await response.json();
        if (!response.ok) {
            throw new Error(body.message || "Unable to restore item.");
        }
        showToast(body.message);
        await refreshAll();
    } catch (error) {
        showToast(error.message, true);
    }
}

async function updateUserPermissions(userId) {
    const checkedPermissions = Array.from(
        document.querySelectorAll(`[data-permission-toggle][data-user-id="${userId}"]:checked`),
    ).map((input) => input.value);
    try {
        const response = await fetch(`/api/users/${userId}/permissions`, {
            method: "PUT",
            headers: jsonHeaders(),
            body: JSON.stringify({ permissions: checkedPermissions }),
        });
        const body = await response.json();
        if (!response.ok) {
            throw new Error(body.message || "Unable to update permissions.");
        }
        showToast(`Permissions updated for ${body.username}.`);
        await loadResource("users");
    } catch (error) {
        showToast(error.message, true);
        await loadResource("users");
    }
}

async function resetUserPassword(userId, username) {
    const newPassword = window.prompt(`Enter a new password for ${username}. Minimum 10 characters.`);
    if (newPassword === null) {
        return;
    }
    if (newPassword.length < 10) {
        showToast("Password must be at least 10 characters.", true);
        return;
    }
    try {
        const response = await fetch(`/api/users/${userId}/password`, {
            method: "PUT",
            headers: jsonHeaders(),
            body: JSON.stringify({ new_password: newPassword }),
        });
        const body = await response.json();
        if (!response.ok) {
            throw new Error(body.message || "Unable to reset password.");
        }
        showToast(body.message || `Password reset for ${username}.`);
    } catch (error) {
        showToast(error.message, true);
    }
}

async function deleteRow(resource, id) {
    try {
        const response = await fetch(`${endpoints[resource]}/${id}`, {
            method: "DELETE",
            headers: csrfHeaders(),
        });
        const body = await response.json();
        if (!response.ok) {
            throw new Error(body.message || "Unable to delete resource.");
        }
        showToast(body.message);
        await refreshAll();
    } catch (error) {
        showToast(error.message, true);
    }
}

async function getJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
}

function csrfHeaders(headers = {}) {
    return {
        ...headers,
        "X-CSRF-Token": state.csrfToken,
    };
}

function jsonHeaders() {
    return csrfHeaders({ "Content-Type": "application/json" });
}

function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 3600);
}

function refreshPermissionControls() {
    document.querySelectorAll("[data-required-permission]").forEach((element) => {
        const permission = element.dataset.requiredPermission;
        element.classList.toggle("permission-hidden", !hasPermission(permission));
    });
}

function hasPermission(permission) {
    return state.isSuperuser || state.permissions.includes(permission);
}

function viewLabel(view) {
    return {
        backup_jobs: "Backup Register",
        clusters: "Clusters",
        datastores: "Datastores",
        environments: "Environments",
        hosts: "Hosts",
        vms: "VM Inventory",
    }[view] || view;
}

function icon(name, className = "") {
    return `<svg class="icon ${escapeHtml(className)}" aria-hidden="true"><use href="${state.iconPath}#icon-${escapeHtml(name)}"></use></svg>`;
}

function assetUrl(fileName) {
    return `${state.assetPath}${fileName}`;
}

function osIcon(value, className = "") {
    const name = osIconName(value);
    return `<img class="os-image-icon ${escapeHtml(className)}" src="${assetUrl(`os-${name}.png`)}" alt="" loading="lazy">`;
}

function distributionLabelIcon(targetId, value) {
    if (targetId === "chart-os") {
        return osIcon(value);
    }
    return icon(distributionIcon(targetId, value));
}

function recentVmOperatingSystem(row) {
    if (row.operating_system || row.os) {
        return row.operating_system || row.os;
    }
    const match = (state.resources.vms || []).find((vm) => String(vm.name) === String(row.name));
    return match?.operating_system || "Custom / Other";
}

function warningIcon(row) {
    return icon(warningIconName(row), "warning-icon");
}

function warningIconName(row) {
    const title = String(row.title || "").toLowerCase();
    if (row.severity === "healthy") {
        return "status";
    }
    if (title.includes("datastore") || title.includes("storage") || title.includes("capacity")) {
        return "datastore";
    }
    if (title.includes("snapshot")) {
        return "camera";
    }
    if (title.includes("backup")) {
        return "backup";
    }
    if (title.includes("guest") || title.includes("tool")) {
        return "tools";
    }
    if (title.includes("critical") || title.includes("vm")) {
        return "alert";
    }
    return "alert";
}

function distributionIcon(targetId, value) {
    const text = String(value || "").toLowerCase();
    if (targetId === "chart-os") {
        return osIconName(text);
    }
    if (targetId === "chart-power") {
        return "power";
    }
    if (targetId === "chart-backup") {
        return "backup";
    }
    if (targetId === "chart-criticality") {
        return text.includes("critical") || text.includes("high") ? "alert" : "shield";
    }
    return "environments";
}

function osIconName(value) {
    const text = String(value || "").toLowerCase();
    if (text.includes("windows")) {
        return "windows";
    }
    if (text.includes("ubuntu")) {
        return "ubuntu";
    }
    if (text.includes("red hat") || text.includes("rhel")) {
        return "redhat";
    }
    if (text.includes("proxmox")) {
        return "proxmox";
    }
    if (
        text.includes("linux") ||
        text.includes("rocky") ||
        text.includes("alma") ||
        text.includes("centos") ||
        text.includes("debian") ||
        text.includes("suse") ||
        text.includes("fedora") ||
        text.includes("photon") ||
        text.includes("oracle") ||
        text.includes("kali")
    ) {
        return "linux";
    }
    return "other";
}

function osClass(value) {
    return `os-${osIconName(value)}`;
}

function statusIcon(key, value) {
    const normalized = value.toLowerCase();
    if (key === "power_state") {
        return "power";
    }
    if (key === "snapshot") {
        return "camera";
    }
    if (normalized.includes("critical") || normalized.includes("failed") || normalized.includes("high")) {
        return "alert";
    }
    if (normalized.includes("warning") || normalized.includes("medium") || normalized.includes("suspended")) {
        return "alert";
    }
    return "status";
}

function modalTypeForResource(resource) {
    return {
        backup_jobs: "backup",
        clusters: "cluster",
        datastores: "datastore",
        environments: "environment",
        hosts: "host",
        vlans: "vlan",
        vms: "vm",
    }[resource];
}

function slugify(value) {
    return String(value || "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
}

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    }[character]));
}
