/* ==========================================================================
   Hirely — Plate I: a sample résumé, marked up the way Hirely reads it
   Draws freehand ink marks (a loop, underlines, a brace, highlighter) on the
   fields Hirely extracts, writes margin notes, then sets down the profile
   draft. The sheet is decorative (aria-hidden); the draft card holds the text.
   ========================================================================== */
(function () {
    "use strict";

    const stage = document.getElementById("specimen");
    if (!stage) return;

    const sheet = stage.querySelector(".specimen-sheet");
    const sheetInk = stage.querySelector(".sheet-ink");
    const stageInk = stage.querySelector(".stage-ink");
    const notes = Array.from(stage.querySelectorAll("[data-note]"));
    const fields = Array.from(stage.querySelectorAll("[data-field]"));
    const replay = stage.querySelector("[data-specimen-replay]");
    const NS = "http://www.w3.org/2000/svg";
    const ORDER = ["name", "email", "github", "summary", "skills"];
    const STEP = 520;
    const reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
    let timers = [];
    let hasRun = false;

    stage.querySelectorAll(".cv-skills mark").forEach((mark, index) => mark.style.setProperty("--i", index));

    /* ---------- A steady hand: seeded randomness per mark ---------- */

    function hand(key) {
        let seed = 7;
        for (const ch of key) seed = (seed * 31 + ch.charCodeAt(0)) >>> 0;
        return () => {
            seed = (seed * 1664525 + 1013904223) >>> 0;
            return seed / 4294967296 - 0.5;
        };
    }

    const fmt = (n) => n.toFixed(1);

    /* Catmull-Rom through the points, as cubic Béziers */
    function smooth(points) {
        let d = "M" + fmt(points[0][0]) + " " + fmt(points[0][1]);
        for (let i = 0; i < points.length - 1; i += 1) {
            const p0 = points[i - 1] || points[i];
            const p1 = points[i];
            const p2 = points[i + 1];
            const p3 = points[i + 2] || p2;
            d += " C" + fmt(p1[0] + (p2[0] - p0[0]) / 6) + " " + fmt(p1[1] + (p2[1] - p0[1]) / 6) +
                " " + fmt(p2[0] - (p3[0] - p1[0]) / 6) + " " + fmt(p2[1] - (p3[1] - p1[1]) / 6) +
                " " + fmt(p2[0]) + " " + fmt(p2[1]);
        }
        return d;
    }

    /* ---------- Marks ---------- */

    function loop(r, jitter) {
        const cx = r.x + r.w / 2;
        const cy = r.y + r.h / 2;
        const rx = r.w / 2 + 16;
        const ry = r.h / 2 + 9;
        const start = Math.PI * 1.08;
        const sweep = Math.PI * 2 * 1.1;
        const points = [];
        for (let i = 0; i <= 30; i += 1) {
            const t = i / 30;
            const a = start + sweep * t;
            const grow = 1 + t * 0.06 + jitter() * 0.05;
            points.push([cx + Math.cos(a) * rx * grow, cy + Math.sin(a) * ry * grow - t * 3]);
        }
        return { d: smooth(points), anchor: [cx + rx + 2, cy] };
    }

    function underline(r, jitter) {
        const y = r.y + r.h + 1.5;
        const x0 = r.x - 3;
        const x1 = r.x + r.w + 5;
        const points = [];
        for (let i = 0; i <= 6; i += 1) {
            const t = i / 6;
            points.push([x0 + (x1 - x0) * t, y + jitter() * 2.4 - t * 1.6]);
        }
        return { d: smooth(points), anchor: points[points.length - 1] };
    }

    function brace(r, jitter) {
        const x = r.x + r.w + 10;
        const top = r.y - 2;
        const bottom = r.y + r.h + 2;
        const mid = (top + bottom) / 2;
        const points = [
            [x - 6, top + jitter()],
            [x + 1, top + 7],
            [x + 2 + jitter(), mid - 7],
            [x + 8, mid],
            [x + 2 + jitter(), mid + 7],
            [x + 1, bottom - 7],
            [x - 6, bottom + jitter()]
        ];
        return { d: smooth(points), anchor: [x + 9, mid] };
    }

    function tick(rects, jitter) {
        const last = rects[rects.length - 1];
        const x = last.x + last.w + 8;
        const y = last.y + last.h / 2;
        const points = [[x, y - 1], [x + 4, y + 4 + jitter()], [x + 13, y - 7]];
        return { d: smooth(points), anchor: [x + 14, y - 4] };
    }

    /* ---------- Geometry ---------- */

    function measure() {
        const previous = sheet.style.transform;
        sheet.style.transform = "none";
        const base = sheet.getBoundingClientRect();
        const offsetX = base.left + sheet.clientLeft;
        const offsetY = base.top + sheet.clientTop;
        const targets = {};
        stage.querySelectorAll("[data-target]").forEach((el) => {
            targets[el.getAttribute("data-target")] = Array.from(el.getClientRects()).map((r) => ({
                x: r.left - offsetX,
                y: r.top - offsetY,
                w: r.width,
                h: r.height
            }));
        });
        sheet.style.transform = previous;
        return { targets, width: sheet.clientWidth, height: sheet.clientHeight };
    }

    /* Sheet-local point → stage point, through the sheet's rotation */
    function toStage(point) {
        const style = getComputedStyle(sheet);
        const matrix = style.transform && style.transform !== "none" ? new DOMMatrixReadOnly(style.transform) : new DOMMatrixReadOnly();
        const origin = style.transformOrigin.split(" ").map(parseFloat);
        const local = new DOMPoint(point[0] + sheet.clientLeft - origin[0], point[1] + sheet.clientTop - origin[1]);
        const turned = matrix.transformPoint(local);
        return [sheet.offsetLeft + origin[0] + turned.x, sheet.offsetTop + origin[1] + turned.y];
    }

    function path(svg, d, key, animate) {
        const el = document.createElementNS(NS, "path");
        el.setAttribute("d", d);
        el.setAttribute("data-key", key);
        svg.appendChild(el);
        if (animate) {
            el.style.setProperty("--len", Math.ceil(el.getTotalLength()) + 1);
            el.style.setProperty("--delay", animate.delay + "ms");
            el.style.setProperty("--dur", animate.duration + "ms");
            el.classList.add("ink-anim");
        }
        return el;
    }

    function clearTimers() {
        timers.forEach(clearTimeout);
        timers = [];
    }

    function draw(animate) {
        clearTimers();
        const geo = measure();
        sheetInk.setAttribute("viewBox", "0 0 " + geo.width + " " + geo.height);
        stageInk.setAttribute("viewBox", "0 0 " + stage.clientWidth + " " + stage.clientHeight);
        sheetInk.textContent = "";
        stageInk.textContent = "";

        const shapes = {};
        ORDER.forEach((key) => {
            const rects = geo.targets[key];
            if (!rects || !rects.length) return;
            const jitter = hand(key);
            if (key === "name") shapes[key] = loop(rects[0], jitter);
            else if (key === "summary") shapes[key] = brace(rects[0], jitter);
            else if (key === "skills") shapes[key] = tick(rects, jitter);
            else shapes[key] = underline(rects[0], jitter);
        });

        /* Margin notes to the right of the sheet, kept apart vertically */
        const corners = [[geo.width, 0], [geo.width, geo.height]].map(toStage);
        const noteX = Math.max(corners[0][0], corners[1][0]) + 26;
        let lastY = -Infinity;
        const placed = ORDER.filter((key) => shapes[key]).map((key, index) => ({ key, index, anchor: toStage(shapes[key].anchor) }));
        /* Top to bottom; marks on the same line keep reading order so leaders never cross */
        placed.sort((a, b) => (Math.abs(a.anchor[1] - b.anchor[1]) < 12 ? a.index - b.index : a.anchor[1] - b.anchor[1]));
        placed.forEach((item) => {
            item.y = Math.max(item.anchor[1], lastY + 30);
            lastY = item.y;
        });

        ORDER.forEach((key, index) => {
            const shape = shapes[key];
            if (!shape) return;
            const delay = 250 + index * STEP;
            path(sheetInk, shape.d, key, animate && { delay, duration: key === "name" ? 760 : 520 });

            const item = placed.find((p) => p.key === key);
            const [ax, ay] = item.anchor;
            const leader = "M" + fmt(ax + 3) + " " + fmt(ay) +
                " C" + fmt(ax + 28) + " " + fmt(ay + 2) + " " + fmt(noteX - 34) + " " + fmt(item.y) + " " + fmt(noteX - 7) + " " + fmt(item.y);
            path(stageInk, leader, key, animate && { delay: delay + 260, duration: 420 });

            const note = notes.find((n) => n.getAttribute("data-note") === key);
            if (note) {
                note.style.setProperty("--x", fmt(noteX) + "px");
                note.style.setProperty("--y", fmt(item.y) + "px");
                note.style.setProperty("--delay", animate ? delay + 520 + "ms" : "0ms");
                note.classList.add("is-shown");
            }
        });

        if (animate) {
            stage.classList.remove("is-marked", "is-carded");
            const skillsAt = 250 + ORDER.indexOf("skills") * STEP - 260;
            timers.push(setTimeout(() => stage.classList.add("is-marked"), skillsAt));
            timers.push(setTimeout(() => stage.classList.add("is-carded"), 250 + ORDER.length * STEP + 260));
        } else {
            stage.classList.add("is-marked", "is-carded");
        }
    }

    function run() {
        hasRun = true;
        notes.forEach((note) => note.classList.remove("is-shown"));
        draw(!reduceQuery.matches);
    }

    /* ---------- Pointing at a field lights up where it came from ---------- */

    function setHot(key, on) {
        stage.querySelectorAll('[data-key="' + key + '"]').forEach((el) => el.classList.toggle("is-hot", on));
        notes.concat(fields).forEach((el) => {
            if (el.getAttribute("data-note") === key || el.getAttribute("data-field") === key) el.classList.toggle("is-hot", on);
        });
    }

    fields.forEach((field) => {
        const key = field.getAttribute("data-field");
        field.addEventListener("mouseenter", () => setHot(key, true));
        field.addEventListener("mouseleave", () => setHot(key, false));
    });

    if (replay) replay.addEventListener("click", run);

    /* Redraw (without animating) when the plate changes size */
    let frame = 0;
    if ("ResizeObserver" in window) {
        new ResizeObserver(() => {
            if (!hasRun) return;
            cancelAnimationFrame(frame);
            frame = requestAnimationFrame(() => draw(false));
        }).observe(stage);
    }

    /* Start once the fonts are in and the plate is on screen */
    const fontsReady = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
    fontsReady.then(() => {
        const begin = () => setTimeout(run, reduceQuery.matches ? 0 : 700);
        if (!("IntersectionObserver" in window)) return begin();
        const observer = new IntersectionObserver((entries) => {
            if (entries.some((entry) => entry.isIntersecting)) {
                observer.disconnect();
                begin();
            }
        }, { threshold: 0.35 });
        observer.observe(stage);
    });
})();
