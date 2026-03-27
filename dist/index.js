const R = ":root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif}*{box-sizing:border-box}body{margin:0}.component-root,.fretboard-shell{width:100%}.badge{margin-bottom:8px;display:inline-block;padding:8px 12px;border-radius:999px;background:#ffffff0f;border:1px solid rgba(255,255,255,.08);color:var(--st-text-color, #f2f2f2);font-size:14px}.fretboard{width:100%;display:block}.fret-line{stroke-opacity:.86;stroke-linecap:round;stroke-width:2.5}.nut-line{stroke-opacity:0}.string-line{stroke-linecap:round;opacity:.96}.inlay{opacity:.92}.hover-cell{fill:#fff4d624;stroke:#fff4d638;stroke-width:1}.selected-cell{fill:#d8b36a1c;stroke:#ffeec66b;stroke-width:1.2}.selected-marker-halo{fill:#fff7e826}.selected-marker{stroke-width:2}.hit-cell{fill:transparent;cursor:pointer}.fret-label,.string-label{fill:#d8d0c2;font-size:14px;-webkit-user-select:none;user-select:none}.fret-label{text-anchor:middle}";
function M(t) {
  if (t.querySelector("style[data-alt-tabs-fretboard]"))
    return;
  const e = document.createElement("style");
  e.setAttribute("data-alt-tabs-fretboard", "true"), e.textContent = R, t.appendChild(e);
}
const k = /* @__PURE__ */ new WeakMap();
function g(t) {
  const e = Array.from(
    { length: t.visibleFrets + 2 },
    (n, d) => d === 0 ? 0 : 1 - Math.pow(2, -d / 12)
  ), o = e[e.length - 1], s = t.boardRight - t.boardLeft, r = e.map(
    (n) => t.boardLeft + n / o * s
  );
  return {
    ...t,
    fretBoundaries: r
  };
}
function j(t) {
  return t.instrument === "bass" ? g({
    viewBoxWidth: 1600,
    viewBoxHeight: 320,
    centerY: 170,
    boardLeft: 150,
    boardRight: 1540,
    openAreaLeft: 56,
    visibleFrets: t.visibleFrets,
    nutHalfWidth: 52,
    bodyHalfWidth: 96,
    edgePaddingNut: 10,
    edgePaddingBody: 14,
    stringCount: t.stringCount
  }) : g({
    viewBoxWidth: 1600,
    viewBoxHeight: 320,
    centerY: 170,
    boardLeft: 150,
    boardRight: 1540,
    openAreaLeft: 56,
    visibleFrets: t.visibleFrets,
    nutHalfWidth: 70,
    bodyHalfWidth: 96,
    edgePaddingNut: 10,
    edgePaddingBody: 14,
    stringCount: t.stringCount
  });
}
function c(t, e, o) {
  const s = (o - t.boardLeft) / (t.boardRight - t.boardLeft), r = Math.max(0, Math.min(1, s)), n = t.centerY - t.nutHalfWidth + t.edgePaddingNut, d = t.centerY + t.nutHalfWidth - t.edgePaddingNut, a = t.centerY - t.bodyHalfWidth + t.edgePaddingBody, $ = t.centerY + t.bodyHalfWidth - t.edgePaddingBody, v = t.stringCount === 1 ? 0 : (e - 1) / (t.stringCount - 1), u = n + v * (d - n), x = a + v * ($ - a);
  return u + r * (x - u);
}
function b(t, e, o, s) {
  return (c(t, e, s) + c(t, o, s)) / 2;
}
function G(t, e) {
  return t.stringCount === 4 ? [3.6, 4.4, 5.3, 6.5][e - 1] : [1.3, 1.6, 1.9, 2.3, 2.9, 3.6][e - 1];
}
function T(t) {
  const e = t.boardLeft, o = t.boardRight, s = t.centerY - t.nutHalfWidth, r = t.centerY + t.nutHalfWidth, n = t.centerY - t.bodyHalfWidth, d = t.centerY + t.bodyHalfWidth;
  return [
    `M ${e} ${s}`,
    `L ${o} ${n}`,
    `L ${o} ${d}`,
    `L ${e} ${r}`,
    "Z"
  ].join(" ");
}
function Y(t, e) {
  const o = e === 1 ? c(t, 1, t.boardLeft) - 12 : b(t, e - 1, e, t.boardLeft), s = e === t.stringCount ? c(t, t.stringCount, t.boardLeft) + 12 : b(t, e, e + 1, t.boardLeft);
  return [
    `${t.openAreaLeft},${o}`,
    `${t.boardLeft},${o}`,
    `${t.boardLeft},${s}`,
    `${t.openAreaLeft},${s}`
  ].join(" ");
}
function E(t, e, o) {
  const s = t.fretBoundaries[o - 1], r = t.fretBoundaries[o], n = e === 1 ? c(t, 1, s) - 12 : b(t, e - 1, e, s), d = e === 1 ? c(t, 1, r) - 12 : b(t, e - 1, e, r), a = e === t.stringCount ? c(t, t.stringCount, s) + 12 : b(t, e, e + 1, s), $ = e === t.stringCount ? c(t, t.stringCount, r) + 12 : b(t, e, e + 1, r);
  return [
    `${s},${n}`,
    `${r},${d}`,
    `${r},${$}`,
    `${s},${a}`
  ].join(" ");
}
function _(t, e) {
  if (e.fret === 0)
    return { x: (t.openAreaLeft + t.boardLeft) / 2, y: c(t, e.stringNumber, t.boardLeft) };
  const o = t.fretBoundaries[e.fret - 1], s = t.fretBoundaries[e.fret], r = (o + s) / 2;
  return { x: r, y: c(t, e.stringNumber, r) };
}
function q(t, e) {
  const o = [3, 5, 7, 9], s = [12], r = [];
  for (const n of o) {
    if (n > t.visibleFrets) continue;
    const d = (t.fretBoundaries[n - 1] + t.fretBoundaries[n]) / 2;
    r.push(
      `<circle cx="${d}" cy="${t.centerY}" r="7" class="inlay" style="fill:${e.inlayColor}" />`
    );
  }
  for (const n of s) {
    if (n > t.visibleFrets) continue;
    const d = (t.fretBoundaries[n - 1] + t.fretBoundaries[n]) / 2;
    r.push(
      `<circle cx="${d}" cy="${t.centerY - 22}" r="6.5" class="inlay" style="fill:${e.inlayColor}" />`
    ), r.push(
      `<circle cx="${d}" cy="${t.centerY + 22}" r="6.5" class="inlay" style="fill:${e.inlayColor}" />`
    );
  }
  return r.join(`
`);
}
function z(t) {
  const e = [];
  e.push(
    `<text x="${(t.openAreaLeft + t.boardLeft) / 2}" y="296" class="fret-label">0</text>`
  );
  for (let o = 1; o <= t.visibleFrets; o += 1) {
    const s = (t.fretBoundaries[o - 1] + t.fretBoundaries[o]) / 2;
    e.push(`<text x="${s}" y="296" class="fret-label">${o}</text>`);
  }
  return e.join(`
`);
}
function N(t) {
  const e = [];
  for (let o = 1; o <= t.stringCount; o += 1) {
    const s = c(t, o, t.boardLeft);
    e.push(`<text x="26" y="${s + 4}" class="string-label">${o}</text>`);
  }
  return e.join(`
`);
}
function W(t, e, o) {
  return `<polygon points="${e.fret === 0 ? Y(t, e.stringNumber) : E(t, e.stringNumber, e.fret)}" class="${o}" />`;
}
const D = (t) => {
  const { parentElement: e, data: o, setStateValue: s } = t;
  M(e);
  let r = e.querySelector(".component-root");
  r || (r = document.createElement("div"), r.className = "component-root", e.appendChild(r));
  const n = j(o), d = o.selectedString != null && o.selectedFret != null ? {
    stringNumber: o.selectedString,
    fret: o.selectedFret
  } : null;
  k.has(e) || k.set(e, {
    selected: d,
    hovered: null
  });
  const a = k.get(e);
  a.selected = d;
  const $ = a.hovered ? W(n, a.hovered, "hover-cell") : "", v = a.selected ? W(n, a.selected, "selected-cell") : "", u = a.selected ? _(n, a.selected) : null, x = a.selected ? `<div class="badge">String ${a.selected.stringNumber} · Fret ${a.selected.fret}</div>` : '<div class="badge">No target selected</div>', F = u ? `
        <circle cx="${u.x}" cy="${u.y}" r="11" class="selected-marker-halo" />
        <circle
          cx="${u.x}"
          cy="${u.y}"
          r="7.5"
          class="selected-marker"
          style="fill:${o.theme.markerColor}; stroke:${o.theme.markerStroke}"
        />
      ` : "", y = Array.from(
    { length: n.visibleFrets + 1 },
    (i, l) => {
      const f = n.fretBoundaries[l], p = l / n.visibleFrets, h = n.centerY - n.nutHalfWidth + p * (n.nutHalfWidth - n.bodyHalfWidth), S = n.centerY + n.nutHalfWidth + p * (n.bodyHalfWidth - n.nutHalfWidth);
      return `<line
        x1="${f}"
        y1="${h}"
        x2="${f}"
        y2="${S}"
        class="fret-line ${l === 0 ? "nut-line" : ""}"
        style="stroke:${o.theme.fretColor}"
      />`;
    }
  ).join(`
`), A = Array.from({ length: n.stringCount }, (i, l) => {
    const f = l + 1;
    return `
      <line
        x1="${n.openAreaLeft}"
        y1="${c(n, f, n.boardLeft)}"
        x2="${n.boardRight}"
        y2="${c(n, f, n.boardRight)}"
        class="string-line"
        style="stroke:${o.theme.stringColor}; stroke-width:${G(n, f)}"
      />
    `;
  }).join(`
`), L = [];
  for (let i = 1; i <= n.stringCount; i += 1) {
    L.push(
      `<polygon points="${Y(n, i)}" class="hit-cell" data-string="${i}" data-fret="0" />`
    );
    for (let l = 1; l <= n.visibleFrets; l += 1)
      L.push(
        `<polygon points="${E(n, i, l)}" class="hit-cell" data-string="${i}" data-fret="${l}" />`
      );
  }
  r.innerHTML = `
    <div class="fretboard-shell">
      ${x}
      <svg
        viewBox="0 0 ${n.viewBoxWidth} ${n.viewBoxHeight}"
        class="fretboard"
        role="img"
        aria-label="Fretboard selector"
      >
        <defs>
          <linearGradient id="bg-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${o.theme.bgTop}" />
            <stop offset="100%" stop-color="${o.theme.bgBottom}" />
          </linearGradient>

          <linearGradient id="board-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${o.instrument === "acoustic_guitar" ? "#241f1b" : "#c89a64"}" />
            <stop offset="50%" stop-color="${o.theme.boardBase}" />
            <stop offset="100%" stop-color="${o.instrument === "acoustic_guitar" ? "#191512" : "#a67647"}" />
          </linearGradient>

          <filter id="soft-shadow" x="-20%" y="-50%" width="140%" height="200%">
            <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.35" />
          </filter>
        </defs>

        <rect
          x="0"
          y="0"
          width="${n.viewBoxWidth}"
          height="${n.viewBoxHeight}"
          fill="url(#bg-gradient)"
          rx="24"
        />

        <path
          d="${T(n)}"
          fill="url(#board-gradient)"
          stroke="${o.theme.boardEdge}"
          stroke-width="3"
          filter="url(#soft-shadow)"
        />

        ${$}
        ${v}
        ${y}
        ${q(n, o.theme)}
        ${A}

        <line
          x1="${n.boardLeft}"
          y1="${n.centerY - n.nutHalfWidth}"
          x2="${n.boardLeft}"
          y2="${n.centerY + n.nutHalfWidth}"
          stroke="${o.theme.nutColor}"
          stroke-width="8"
          stroke-linecap="round"
        />

        ${F}

        ${N(n)}
        ${z(n)}
        ${L.join(`
`)}
      </svg>
    </div>
  `;
  const P = r.querySelectorAll(".hit-cell"), C = [], B = [], w = [];
  P.forEach((i) => {
    const l = () => {
      a.hovered = {
        stringNumber: Number(i.dataset.string),
        fret: Number(i.dataset.fret)
      }, r.dispatchEvent(new CustomEvent("rerender"));
    }, f = () => {
      a.hovered = null, r.dispatchEvent(new CustomEvent("rerender"));
    }, p = () => {
      const h = {
        stringNumber: Number(i.dataset.string),
        fret: Number(i.dataset.fret)
      };
      a.selected = h, s("selectedPosition", h), s("selectedString", h.stringNumber), s("selectedFret", h.fret), r.dispatchEvent(new CustomEvent("rerender"));
    };
    i.addEventListener("mouseenter", l), i.addEventListener("mouseleave", f), i.addEventListener("click", p), C.push(() => i.removeEventListener("mouseenter", l)), B.push(() => i.removeEventListener("mouseleave", f)), w.push(() => i.removeEventListener("click", p));
  });
  const H = () => {
    D(t);
  };
  return r.addEventListener("rerender", H, { once: !0 }), () => {
    C.forEach((i) => i()), B.forEach((i) => i()), w.forEach((i) => i()), r?.removeEventListener("rerender", H);
  };
};
export {
  D as default
};
