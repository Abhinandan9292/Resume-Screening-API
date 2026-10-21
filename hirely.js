/* ==========================================================================
   Hirely — shared UI helpers
   Presentation only: icons, escaping, toasts, modals, view switching,
   validation, drop zones and scroll reveals. No API calls live here —
   every request stays in the page that owns it.
   ========================================================================== */
(function () {
    "use strict";

    const doc = document;
    const root = doc.documentElement;
    root.classList.add("js");

    const motionQuery = window.matchMedia
        ? window.matchMedia("(prefers-reduced-motion: reduce)")
        : { matches: false };
    const reducedMotion = () => motionQuery.matches;

    /* ---------- Icons (24px grid, 1.6 stroke) ---------- */

    const ICONS = {
        grid: '<rect x="3.5" y="3.5" width="7" height="7" rx="1.2"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.2"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.2"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.2"/>',
        briefcase: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8.5 7V5.5A1.5 1.5 0 0 1 10 4h4a1.5 1.5 0 0 1 1.5 1.5V7"/><path d="M3 12.5h18"/>',
        users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.6-3.4 3.2-5.5 6.5-5.5s5.9 2.1 6.5 5.5"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8"/><path d="M18 14.8c1.9.7 3.1 2.5 3.5 5.2"/>',
        user: '<circle cx="12" cy="8" r="4"/><path d="M4 20.5c.8-3.9 4-6.5 8-6.5s7.2 2.6 8 6.5"/>',
        inbox: '<path d="M3.5 13.5 6 5.5A1.5 1.5 0 0 1 7.4 4.5h9.2A1.5 1.5 0 0 1 18 5.5l2.5 8"/><path d="M3.5 13.5V18a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2v-4.5h-5L14 16h-4l-1.5-2.5z"/>',
        search: '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
        upload: '<path d="M12 15V4"/><path d="m7.5 8.5 4.5-4.5 4.5 4.5"/><path d="M4 15v3.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V15"/>',
        file: '<path d="M14 3.5H7A1.5 1.5 0 0 0 5.5 5v14A1.5 1.5 0 0 0 7 20.5h10a1.5 1.5 0 0 0 1.5-1.5V8z"/><path d="M14 3.5V8h4.5"/><path d="M9 13h6M9 16.5h4"/>',
        check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
        "check-circle": '<circle cx="12" cy="12" r="8.5"/><path d="m8.5 12.2 2.4 2.4 4.6-4.8"/>',
        x: '<path d="M6 6l12 12M18 6 6 18"/>',
        "arrow-right": '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
        "arrow-left": '<path d="M19 12H5"/><path d="m11 18-6-6 6-6"/>',
        "arrow-down": '<path d="M12 5v14"/><path d="m6 13 6 6 6-6"/>',
        "arrow-up-right": '<path d="M7 17 17 7"/><path d="M8 7h9v9"/>',
        logout: '<path d="M14.5 4.5h3a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2h-3"/><path d="M10 16.5 5.5 12 10 7.5"/><path d="M5.5 12H16"/>',
        plus: '<path d="M12 5v14M5 12h14"/>',
        download: '<path d="M12 4v11"/><path d="m7.5 10.5 4.5 4.5 4.5-4.5"/><path d="M4.5 19.5h15"/>',
        mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/>',
        branch: '<circle cx="6.5" cy="5.5" r="2.2"/><circle cx="6.5" cy="18.5" r="2.2"/><circle cx="17.5" cy="7.5" r="2.2"/><path d="M6.5 7.7v8.6"/><path d="M17.5 9.7c0 4.3-5.6 3.6-10.2 6.6"/>',
        chart: '<path d="M3.5 20.5h17"/><path d="M6.5 17v-6"/><path d="M11.5 17V6"/><path d="M16.5 17v-4"/>',
        shield: '<path d="M12 3.5 5 6v5.5c0 4.3 2.9 7.6 7 9 4.1-1.4 7-4.7 7-9V6z"/><path d="m9 12 2.2 2.2L15.5 10"/>',
        building: '<rect x="4.5" y="3.5" width="15" height="17" rx="1.5"/><path d="M9 7.5h1M14 7.5h1M9 11h1M14 11h1M9 14.5h1M14 14.5h1"/><path d="M10.5 20.5v-3h3v3"/>',
        edit: '<path d="M15.5 5.5a2.1 2.1 0 0 1 3 3L8 19l-4 1 1-4z"/><path d="m13.5 7.5 3 3"/>',
        eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
        "eye-off": '<path d="M3 3l18 18"/><path d="M10.6 5.6A9.6 9.6 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a16 16 0 0 1-3 3.7M6.4 6.9C3.9 8.6 2.5 12 2.5 12s3.5 6.5 9.5 6.5c1.6 0 3-.4 4.2-1"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
        alert: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v5"/><path d="M12 16h.01"/>',
        info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
        pin: '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
        clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
        cap: '<path d="m2.5 9 9.5-4.5L21.5 9 12 13.5z"/><path d="M6.5 11v4.5c1.5 1.3 3.4 2 5.5 2s4-.7 5.5-2V11"/><path d="M21.5 9v5"/>',
        board: '<rect x="3.5" y="4" width="5" height="16" rx="1"/><rect x="10" y="4" width="5" height="11" rx="1"/><rect x="16.5" y="4" width="4" height="7" rx="1"/>',
        list: '<path d="M8.5 6.5h12M8.5 12h12M8.5 17.5h12"/><path d="M4 6.5h.01M4 12h.01M4 17.5h.01"/>',
        lock: '<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
        refresh: '<path d="M20 11.5A8 8 0 0 0 5.6 7"/><path d="M4 4.5V8h3.5"/><path d="M4 12.5A8 8 0 0 0 18.4 17"/><path d="M20 19.5V16h-3.5"/>',
        activity: '<path d="M3 12h4l2.5-6 5 12 2.5-6H21"/>',
        wallet: '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18"/><path d="M16 14.5h2"/>',
        layers: '<path d="m12 3.5 8.5 4.5-8.5 4.5L3.5 8z"/><path d="m3.5 12 8.5 4.5 8.5-4.5"/><path d="m3.5 16 8.5 4.5 8.5-4.5"/>',
        scan: '<path d="M4.5 8.5V6A1.5 1.5 0 0 1 6 4.5h2.5M15.5 4.5H18A1.5 1.5 0 0 1 19.5 6v2.5M19.5 15.5V18a1.5 1.5 0 0 1-1.5 1.5h-2.5M8.5 19.5H6A1.5 1.5 0 0 1 4.5 18v-2.5"/><path d="M8 12h8"/>',
        target: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r=".6"/>',
        sort: '<path d="M7 4.5v15M4 16.5l3 3 3-3"/><path d="M17 19.5v-15M14 7.5l3-3 3 3"/>'
    };

    function icon(name, className) {
        const body = ICONS[name];
        if (!body) return "";
        return '<svg class="icon' + (className ? " " + className : "") + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + body + "</svg>";
    }

    function hydrateIcons(scope) {
        (scope || doc).querySelectorAll("[data-icon]:not([data-icon-ready])").forEach((el) => {
            el.innerHTML = icon(el.getAttribute("data-icon"));
            el.setAttribute("data-icon-ready", "");
            el.setAttribute("aria-hidden", "true");
        });
    }

    /* ---------- Text & data helpers ---------- */

    const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

    function esc(value) {
        return String(value === null || value === undefined ? "" : value).replace(/[&<>"']/g, (c) => ESCAPES[c]);
    }

    function splitSkills(value) {
        return String(value || "")
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean);
    }

    function fullName(first, last) {
        return [first, last].map((p) => (p || "").trim()).filter(Boolean).join(" ");
    }

    function initials(first, last) {
        const a = (first || "").trim().charAt(0);
        const b = (last || "").trim().charAt(0);
        return (a + b).toUpperCase() || "?";
    }

    /* Only ever link to http(s) URLs; bare domains get https:// */
    function safeUrl(value) {
        let url = String(value || "").trim();
        if (!url) return "";
        if (!/^[a-z][a-z0-9+.-]*:/i.test(url)) url = "https://" + url.replace(/^\/+/, "");
        try {
            const parsed = new URL(url);
            return parsed.protocol === "http:" || parsed.protocol === "https:" ? parsed.href : "";
        } catch (error) {
            return "";
        }
    }

    function formatBytes(bytes) {
        if (!Number.isFinite(bytes)) return "";
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(bytes < 10240 ? 1 : 0) + " KB";
        return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    }

    function formatNumber(value) {
        const n = Number(value);
        return Number.isFinite(n) ? n.toLocaleString() : String(value === undefined || value === null ? "—" : value);
    }

    /* Display-only rounding for averages coming back from SQL */
    function formatDecimal(value, places) {
        const n = Number(value);
        if (value === null || value === undefined || value === "" || !Number.isFinite(n)) return "—";
        return String(Number(n.toFixed(places === undefined ? 2 : places)));
    }

    /* Count occurrences of each (lower-cased) skill across records */
    function skillFrequency(records, limit) {
        const counts = new Map();
        records.forEach((record) => {
            const seen = new Set();
            splitSkills(record && record.skills).forEach((skill) => {
                const key = skill.toLowerCase();
                if (seen.has(key)) return;
                seen.add(key);
                counts.set(key, (counts.get(key) || 0) + 1);
            });
        });
        return Array.from(counts.entries())
            .map(([label, count]) => ({ label, count }))
            .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label))
            .slice(0, limit || 8);
    }

    /* ---------- Shared markup builders ---------- */

    function emptyState(options) {
        const o = options || {};
        return (
            '<div class="empty' + (o.tone === "error" ? " empty--error" : "") + (o.compact ? " empty--compact" : "") + '"' + (o.tone === "error" ? ' role="alert"' : "") + ">" +
            '<div class="empty-icon">' + icon(o.icon || (o.tone === "error" ? "alert" : "inbox")) + "</div>" +
            '<p class="empty-title">' + esc(o.title || "") + "</p>" +
            (o.text ? "<p>" + esc(o.text) + "</p>" : "") +
            (o.action || "") +
            "</div>"
        );
    }

    function tableState(colspan, options) {
        return '<tr class="table-state"><td colspan="' + colspan + '">' + emptyState(options) + "</td></tr>";
    }

    function skeletonRows(cols, rows) {
        const widths = ["62%", "44%", "78%", "36%", "54%"];
        let html = "";
        for (let r = 0; r < (rows || 4); r += 1) {
            html += '<tr class="table-state" aria-hidden="true">';
            for (let c = 0; c < cols; c += 1) {
                if (c === 0) {
                    html += '<td style="padding:14px 16px 14px 20px"><div class="person"><span class="skeleton skeleton--circle"></span><div style="display:grid;gap:7px;flex:1"><span class="skeleton" style="width:' + widths[(r + 1) % 5] + '"></span><span class="skeleton" style="width:' + widths[(r + 3) % 5] + ';height:8px"></span></div></div></td>';
                } else {
                    html += '<td style="padding:14px 16px"><span class="skeleton" style="width:' + widths[(r + c) % 5] + '"></span></td>';
                }
            }
            html += "</tr>";
        }
        return html;
    }

    function barList(items, options) {
        const o = options || {};
        if (!items.length) return emptyState({ compact: true, icon: "chart", title: o.emptyTitle || "Nothing to chart yet", text: o.emptyText || "" });
        const max = Math.max.apply(null, items.map((i) => i.count)) || 1;
        return (
            '<div class="bars" role="list">' +
            items
                .map((item, index) => {
                    const pct = Math.max(2, Math.round((item.count / max) * 100));
                    return (
                        '<div class="bar-row" role="listitem" title="' + esc(item.label) + ": " + esc(item.count) + " " + esc(o.unit || "") + '">' +
                        '<span class="bar-label">' + esc(item.label) + "</span>" +
                        '<span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:' + pct + "%;animation-delay:" + index * 40 + 'ms"></span></span>' +
                        '<span class="bar-value">' + esc(formatNumber(item.count)) + '<span class="sr-only"> ' + esc(o.unit || "") + "</span></span>" +
                        "</div>"
                    );
                })
                .join("") +
            "</div>"
        );
    }

    /* ---------- Buttons: busy / idle ---------- */

    function busy(button, label) {
        if (!button) return;
        if (button.dataset.idleHtml === undefined) button.dataset.idleHtml = button.innerHTML;
        button.disabled = true;
        button.classList.add("is-busy");
        button.setAttribute("aria-busy", "true");
        button.innerHTML = '<span class="spinner" aria-hidden="true"></span><span>' + esc(label) + "</span>";
    }

    function idle(button, html) {
        if (!button) return;
        button.disabled = false;
        button.classList.remove("is-busy");
        button.removeAttribute("aria-busy");
        if (html !== undefined) button.innerHTML = html;
        else if (button.dataset.idleHtml !== undefined) button.innerHTML = button.dataset.idleHtml;
        delete button.dataset.idleHtml;
    }

    /* ---------- Toasts ---------- */

    function toastHost() {
        let host = doc.querySelector(".toast-host");
        if (!host) {
            host = doc.createElement("div");
            host.className = "toast-host";
            doc.body.appendChild(host);
        }
        return host;
    }

    function toast(message, type, options) {
        const kind = type || "info";
        const o = options || {};
        const el = doc.createElement("div");
        el.className = "toast toast--" + kind;
        el.setAttribute("role", kind === "error" ? "alert" : "status");
        el.innerHTML =
            icon(kind === "success" ? "check-circle" : kind === "error" ? "alert" : "info") +
            "<p>" + esc(message) + "</p>" +
            '<button type="button" class="btn btn-icon" aria-label="Dismiss notification">' + icon("x") + "</button>";
        toastHost().appendChild(el);
        void el.offsetWidth; /* commit the start state so the entrance transitions */
        el.classList.add("is-in");

        let timer = null;
        const dismiss = () => {
            clearTimeout(timer);
            el.classList.remove("is-in");
            setTimeout(() => el.remove(), reducedMotion() ? 0 : 260);
        };
        const schedule = () => {
            timer = setTimeout(dismiss, o.timeout || (kind === "error" ? 7000 : 4200));
        };
        el.querySelector("button").addEventListener("click", dismiss);
        el.addEventListener("mouseenter", () => clearTimeout(timer));
        el.addEventListener("mouseleave", schedule);
        schedule();
        return dismiss;
    }

    /* ---------- Inline alert regions ---------- */

    function showAlert(target, message, type) {
        const el = typeof target === "string" ? doc.getElementById(target) : target;
        if (!el) return;
        const kind = type || "error";
        el.className = "alert alert--" + kind;
        el.setAttribute("role", kind === "error" ? "alert" : "status");
        el.innerHTML = icon(kind === "success" ? "check-circle" : kind === "error" ? "alert" : "info") + "<div>" + esc(message) + "</div>";
        el.hidden = false;
    }

    function clearAlert(target) {
        const el = typeof target === "string" ? doc.getElementById(target) : target;
        if (!el) return;
        el.hidden = true;
        el.innerHTML = "";
    }

    /* ---------- Overlays (modal + drawer) ---------- */

    const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
    const openStack = [];

    function openOverlay(el, options) {
        if (!el || el.classList.contains("is-open")) return;
        const o = options || {};
        el._returnFocus = doc.activeElement;
        el._onClose = o.onClose || null;
        el.classList.remove("hidden");
        el.hidden = false;
        el.setAttribute("aria-hidden", "false");
        doc.body.classList.add("has-overlay");
        openStack.push(el);
        void el.offsetWidth; /* commit the hidden state so the entrance transitions */
        el.classList.add("is-open");
        const body = el.querySelector(".modal-body, .drawer-body");
        const target = el.querySelector("[data-autofocus]") || (body && body.querySelector(FOCUSABLE)) || el.querySelector(FOCUSABLE);
        setTimeout(() => target && target.focus({ preventScroll: true }), 40);
    }

    function closeOverlay(el) {
        if (!el || el.classList.contains("hidden")) return;
        el.classList.remove("is-open");
        el.setAttribute("aria-hidden", "true");
        const index = openStack.indexOf(el);
        if (index > -1) openStack.splice(index, 1);
        if (!openStack.length) doc.body.classList.remove("has-overlay");
        const finish = () => {
            if (!el.classList.contains("is-open")) el.classList.add("hidden");
        };
        if (reducedMotion()) finish();
        else setTimeout(finish, 260);
        const returnTo = el._returnFocus;
        if (returnTo && typeof returnTo.focus === "function" && doc.contains(returnTo)) returnTo.focus({ preventScroll: true });
        if (typeof el._onClose === "function") {
            const callback = el._onClose;
            el._onClose = null;
            callback();
        }
    }

    doc.addEventListener("keydown", (event) => {
        const top = openStack[openStack.length - 1];
        if (!top) return;
        if (event.key === "Escape") {
            event.preventDefault();
            closeOverlay(top);
            return;
        }
        if (event.key === "Tab") {
            const items = Array.from(top.querySelectorAll(FOCUSABLE)).filter((n) => n.offsetParent !== null);
            if (!items.length) return;
            const first = items[0];
            const last = items[items.length - 1];
            if (event.shiftKey && doc.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && doc.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        }
    });

    doc.addEventListener("click", (event) => {
        const closer = event.target.closest("[data-overlay-close]");
        if (closer) {
            closeOverlay(closer.closest(".overlay"));
        }
    });

    function confirmDialog(options) {
        const o = options || {};
        return new Promise((resolve) => {
            let settled = false;
            const wrap = doc.createElement("div");
            wrap.className = "overlay modal hidden";
            wrap.setAttribute("role", "alertdialog");
            wrap.setAttribute("aria-modal", "true");
            wrap.setAttribute("aria-labelledby", "confirm-title");
            wrap.setAttribute("aria-describedby", "confirm-body");
            wrap.innerHTML =
                '<div class="overlay-backdrop" data-overlay-close></div>' +
                '<div class="modal-card" style="width:min(440px,100%)">' +
                '<div class="modal-head"><h2 class="modal-title" id="confirm-title">' + esc(o.title || "Are you sure?") + "</h2></div>" +
                '<div class="modal-body"><p id="confirm-body" class="muted">' + esc(o.message || "") + "</p></div>" +
                '<div class="modal-foot">' +
                '<button type="button" class="btn btn-secondary" data-confirm="no">' + esc(o.cancelLabel || "Cancel") + "</button>" +
                '<button type="button" class="btn ' + (o.tone === "danger" ? "btn-danger" : "btn-primary") + '" data-confirm="yes" data-autofocus>' + esc(o.confirmLabel || "Confirm") + "</button>" +
                "</div></div>";
            doc.body.appendChild(wrap);
            const settle = (value) => {
                if (settled) return;
                settled = true;
                resolve(value);
                setTimeout(() => wrap.remove(), 400);
            };
            wrap.addEventListener("click", (event) => {
                const choice = event.target.closest("[data-confirm]");
                if (!choice) return;
                const value = choice.getAttribute("data-confirm") === "yes";
                settled = true;
                resolve(value);
                closeOverlay(wrap);
                setTimeout(() => wrap.remove(), 400);
            });
            openOverlay(wrap, { onClose: () => settle(false) });
        });
    }

    /* ---------- Views (sidebar sections within one page) ---------- */

    function initViews(options) {
        const o = options || {};
        const views = Array.from(doc.querySelectorAll("[data-view]"));
        const links = Array.from(doc.querySelectorAll("[data-view-link]"));
        if (!views.length) return null;
        const names = views.map((v) => v.getAttribute("data-view"));
        let current = null;

        function show(name, settings) {
            const s = settings || {};
            const target = names.indexOf(name) > -1 ? name : names[0];
            const changed = target !== current;
            current = target;
            views.forEach((view) => {
                const active = view.getAttribute("data-view") === target;
                view.hidden = !active;
                view.classList.toggle("is-active", active);
                if (active && changed) {
                    view.style.animation = "none";
                    void view.offsetWidth;
                    view.style.animation = "";
                }
            });
            links.forEach((link) => {
                const active = link.getAttribute("data-view-link") === target;
                link.classList.toggle("is-active", active);
                if (active) link.setAttribute("aria-current", "page");
                else link.removeAttribute("aria-current");
            });
            if (s.push && location.hash.slice(1) !== target) history.pushState(null, "", "#" + target);
            if (changed && s.scroll !== false) window.scrollTo({ top: 0, behavior: "auto" });
            if (s.focus) {
                const heading = doc.querySelector('[data-view="' + target + '"] h1, [data-view="' + target + '"] h2');
                if (heading) {
                    heading.setAttribute("tabindex", "-1");
                    heading.focus({ preventScroll: true });
                }
            }
            if (changed && typeof o.onChange === "function") o.onChange(target);
        }

        links.forEach((link) => {
            link.addEventListener("click", (event) => {
                event.preventDefault();
                show(link.getAttribute("data-view-link"), { push: true, focus: true });
            });
        });
        window.addEventListener("hashchange", () => show(location.hash.slice(1), { scroll: true }));
        show(location.hash.slice(1) || o.initial || names[0], { scroll: false });

        return {
            show: (name, settings) => show(name, Object.assign({ push: true }, settings || {})),
            current: () => current
        };
    }

    /* ---------- Form validation (inline, accessible) ---------- */

    function fieldLabel(input) {
        const field = input.closest(".field");
        const label = field && field.querySelector("label");
        return label ? label.childNodes[0].textContent.trim() : "This field";
    }

    function messageFor(input) {
        const v = input.validity;
        if (input.dataset.error) return input.dataset.error;
        if (v.valueMissing) return fieldLabel(input) + " is required.";
        if (v.typeMismatch && input.type === "email") return "Enter a valid email address, like name@college.edu.";
        if (v.badInput) return "Enter a number.";
        if (v.stepMismatch) return "Use at most " + ((String(input.step).split(".")[1] || "").length || 0) + " decimal places.";
        if (v.rangeUnderflow) return "Must be " + input.min + " or more.";
        if (v.rangeOverflow) return "Must be " + input.max + " or less.";
        return input.validationMessage || "Check this field.";
    }

    function setFieldError(input, message) {
        const field = input.closest(".field");
        if (!field) return;
        field.classList.add("is-invalid");
        input.setAttribute("aria-invalid", "true");
        const id = (input.id || "field") + "-error";
        let error = field.querySelector(".field-error");
        if (!error) {
            error = doc.createElement("p");
            error.className = "field-error";
            error.id = id;
            field.appendChild(error);
        }
        error.innerHTML = icon("alert") + "<span>" + esc(message) + "</span>";
        const described = (input.getAttribute("aria-describedby") || "").split(" ").filter(Boolean);
        if (described.indexOf(id) === -1) described.push(id);
        input.setAttribute("aria-describedby", described.join(" "));
    }

    function clearFieldError(input) {
        const field = input.closest(".field");
        if (!field) return;
        field.classList.remove("is-invalid");
        input.removeAttribute("aria-invalid");
        const error = field.querySelector(".field-error");
        if (error) {
            const described = (input.getAttribute("aria-describedby") || "").split(" ").filter((t) => t && t !== error.id);
            if (described.length) input.setAttribute("aria-describedby", described.join(" "));
            else input.removeAttribute("aria-describedby");
            error.remove();
        }
    }

    function validateForm(form) {
        let first = null;
        form.querySelectorAll("input, textarea, select").forEach((input) => {
            if (input.type === "file" || input.type === "hidden" || input.disabled || input.readOnly) return;
            if (!input.closest(".field")) return;
            if (input.checkValidity()) {
                clearFieldError(input);
            } else {
                setFieldError(input, messageFor(input));
                if (!first) first = input;
            }
        });
        if (first) first.focus();
        return !first;
    }

    /* Capture phase on document runs before any page submit handler,
       so an invalid form never reaches the existing API code. */
    doc.addEventListener(
        "submit",
        (event) => {
            const form = event.target;
            if (!(form instanceof HTMLFormElement) || !form.hasAttribute("data-validate")) return;
            if (!validateForm(form)) {
                event.preventDefault();
                event.stopPropagation();
            }
        },
        true
    );

    doc.addEventListener("input", (event) => {
        const input = event.target;
        if (input && input.closest && input.closest(".field.is-invalid") && input.checkValidity()) clearFieldError(input);
    });

    doc.addEventListener(
        "blur",
        (event) => {
            const input = event.target;
            if (!input || !input.closest || !input.closest("form[data-validate]")) return;
            if (!(input instanceof HTMLInputElement) || input.type === "file" || input.readOnly) return;
            if (input.value && !input.checkValidity()) setFieldError(input, messageFor(input));
        },
        true
    );

    /* ---------- Password visibility ---------- */

    doc.addEventListener("click", (event) => {
        const toggle = event.target.closest("[data-toggle-password]");
        if (!toggle) return;
        const input = doc.getElementById(toggle.getAttribute("aria-controls"));
        if (!input) return;
        const reveal = input.type === "password";
        input.type = reveal ? "text" : "password";
        toggle.setAttribute("aria-pressed", String(reveal));
        toggle.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
        toggle.innerHTML = icon(reveal ? "eye-off" : "eye");
    });

    /* ---------- Drop zone (progressive enhancement over a file input) ---------- */

    function dropZone(zone, input, options) {
        if (!zone || !input) return;
        const o = options || {};
        const hasFiles = (event) => event.dataTransfer && Array.prototype.indexOf.call(event.dataTransfer.types || [], "Files") > -1;

        ["dragenter", "dragover"].forEach((type) => {
            zone.addEventListener(type, (event) => {
                if (!hasFiles(event)) return;
                event.preventDefault();
                event.dataTransfer.dropEffect = "copy";
                zone.classList.add("is-dragover");
            });
        });
        zone.addEventListener("dragleave", (event) => {
            if (!zone.contains(event.relatedTarget)) zone.classList.remove("is-dragover");
        });
        zone.addEventListener("drop", (event) => {
            if (!hasFiles(event)) return;
            event.preventDefault();
            zone.classList.remove("is-dragover");
            const file = event.dataTransfer.files && event.dataTransfer.files[0];
            if (!file) return;
            try {
                const transfer = new DataTransfer();
                transfer.items.add(file);
                input.files = transfer.files;
            } catch (error) {
                /* Older browsers: the file is still handed to onFile below. */
            }
            if (typeof o.onFile === "function") o.onFile(file);
        });
        /* Stop the browser from navigating to a file dropped just outside the zone */
        window.addEventListener("dragover", (event) => {
            if (hasFiles(event)) event.preventDefault();
        });
        window.addEventListener("drop", (event) => {
            if (hasFiles(event) && !zone.contains(event.target)) event.preventDefault();
        });
    }

    /* ---------- Scroll reveal & sticky nav ---------- */

    function initReveal() {
        const items = doc.querySelectorAll("[data-reveal]");
        if (!items.length) return;
        if (!("IntersectionObserver" in window) || reducedMotion()) {
            items.forEach((el) => el.classList.add("is-revealed"));
            return;
        }
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-revealed");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
        );
        items.forEach((el) => observer.observe(el));
    }

    function initStickyNav() {
        const nav = doc.querySelector("[data-sticky-nav]");
        if (!nav) return;
        const update = () => nav.classList.toggle("is-scrolled", window.scrollY > 24);
        update();
        window.addEventListener("scroll", update, { passive: true });
    }

    function initYear() {
        doc.querySelectorAll("[data-year]").forEach((el) => {
            el.textContent = String(new Date().getFullYear());
        });
    }

    /* ---------- Boot ---------- */

    hydrateIcons();
    const boot = () => {
        hydrateIcons();
        initReveal();
        initStickyNav();
        initYear();
    };
    if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", boot);
    else boot();

    window.Hirely = {
        icon,
        hydrateIcons,
        esc,
        splitSkills,
        fullName,
        initials,
        safeUrl,
        formatBytes,
        formatNumber,
        formatDecimal,
        skillFrequency,
        emptyState,
        tableState,
        skeletonRows,
        barList,
        busy,
        idle,
        toast,
        showAlert,
        clearAlert,
        openOverlay,
        closeOverlay,
        confirmDialog,
        initViews,
        validateForm,
        dropZone,
        reducedMotion
    };
})();
