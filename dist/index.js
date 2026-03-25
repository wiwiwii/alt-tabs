const P = ":root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif}*{box-sizing:border-box}body{margin:0}.component-root,.fretboard-shell{width:100%}.badge{margin-bottom:8px;display:inline-block;padding:8px 12px;border-radius:999px;background:#ffffff0f;border:1px solid rgba(255,255,255,.08);color:var(--st-text-color, #f2f2f2);font-size:14px}.fretboard{width:100%;display:block}.fret-line{stroke-opacity:.86;stroke-linecap:round;stroke-width:2.5}.nut-line{stroke-opacity:0}.string-line{stroke-linecap:round;opacity:.96}.inlay{opacity:.92}.hover-cell{fill:#fff4d624;stroke:#fff4d638;stroke-width:1}.selected-cell{fill:#d8b36a1c;stroke:#ffeec66b;stroke-width:1.2}.selected-marker-halo{fill:#fff7e826}.selected-marker{stroke-width:2}.hit-cell{fill:transparent;cursor:pointer}.fret-label,.string-label{fill:#d8d0c2;font-size:14px;-webkit-user-select:none;user-select:none}.fret-label{text-anchor:middle}";
function R(t) {
  if (t.querySelector("style[data-alt-tabs-fretboard]"))
    return;
  const e = document.createElement("style");
  e.setAttribute("data-alt-tabs-fretboard", "true"), e.textContent = P, t.appendChild(e);
}
const L = /* @__PURE__ */ new WeakMap();
function H(t) {
  const e = Array.from(
    { length: t.visibleFrets + 2 },
    (n, d) => d === 0 ? 0 : 1 - Math.pow(2, -d / 12)
  ), r = e[e.length - 1], s = t.boardRight - t.boardLeft, o = e.map(
    (n) => t.boardLeft + n / r * s
  );
  return {
    ...t,
    fretBoundaries: o
  };
}
function j(t) {
  return t.instrument === "bass" ? H({
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
  }) : H({
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
function c(t, e, r) {
  const s = (r - t.boardLeft) / (t.boardRight - t.boardLeft), o = Math.max(0, Math.min(1, s)), n = t.centerY - t.nutHalfWidth + t.edgePaddingNut, d = t.centerY + t.nutHalfWidth - t.edgePaddingNut, a = t.centerY - t.bodyHalfWidth + t.edgePaddingBody, h = t.centerY + t.bodyHalfWidth - t.edgePaddingBody, p = t.stringCount === 1 ? 0 : (e - 1) / (t.stringCount - 1), b = n + p * (d - n), x = a + p * (h - a);
  return b + o * (x - b);
}
function u(t, e, r, s) {
  return (c(t, e, s) + c(t, r, s)) / 2;
}
function M(t, e) {
  return t.stringCount === 4 ? [3.6, 4.4, 5.3, 6.5][e - 1] : [1.3, 1.6, 1.9, 2.3, 2.9, 3.6][e - 1];
}
function G(t) {
  const e = t.boardLeft, r = t.boardRight, s = t.centerY - t.nutHalfWidth, o = t.centerY + t.nutHalfWidth, n = t.centerY - t.bodyHalfWidth, d = t.centerY + t.bodyHalfWidth;
  return [
    `M ${e} ${s}`,
    `L ${r} ${n}`,
    `L ${r} ${d}`,
    `L ${e} ${o}`,
    "Z"
  ].join(" ");
}
function W(t, e) {
  const r = e === 1 ? c(t, 1, t.boardLeft) - 12 : u(t, e - 1, e, t.boardLeft), s = e === t.stringCount ? c(t, t.stringCount, t.boardLeft) + 12 : u(t, e, e + 1, t.boardLeft);
  return [
    `${t.openAreaLeft},${r}`,
    `${t.boardLeft},${r}`,
    `${t.boardLeft},${s}`,
    `${t.openAreaLeft},${s}`
  ].join(" ");
}
function Y(t, e, r) {
  const s = t.fretBoundaries[r - 1], o = t.fretBoundaries[r], n = e === 1 ? c(t, 1, s) - 12 : u(t, e - 1, e, s), d = e === 1 ? c(t, 1, o) - 12 : u(t, e - 1, e, o), a = e === t.stringCount ? c(t, t.stringCount, s) + 12 : u(t, e, e + 1, s), h = e === t.stringCount ? c(t, t.stringCount, o) + 12 : u(t, e, e + 1, o);
  return [
    `${s},${n}`,
    `${o},${d}`,
    `${o},${h}`,
    `${s},${a}`
  ].join(" ");
}
function T(t, e) {
  if (e.fret === 0)
    return { x: (t.openAreaLeft + t.boardLeft) / 2, y: c(t, e.stringNumber, t.boardLeft) };
  const r = t.fretBoundaries[e.fret - 1], s = t.fretBoundaries[e.fret], o = (r + s) / 2;
  return { x: o, y: c(t, e.stringNumber, o) };
}
function _(t, e) {
  const r = [3, 5, 7, 9], s = [12], o = [];
  for (const n of r) {
    if (n > t.visibleFrets) continue;
    const d = (t.fretBoundaries[n - 1] + t.fretBoundaries[n]) / 2;
    o.push(
      `<circle cx="${d}" cy="${t.centerY}" r="7" class="inlay" style="fill:${e.inlayColor}" />`
    );
  }
  for (const n of s) {
    if (n > t.visibleFrets) continue;
    const d = (t.fretBoundaries[n - 1] + t.fretBoundaries[n]) / 2;
    o.push(
      `<circle cx="${d}" cy="${t.centerY - 22}" r="6.5" class="inlay" style="fill:${e.inlayColor}" />`
    ), o.push(
      `<circle cx="${d}" cy="${t.centerY + 22}" r="6.5" class="inlay" style="fill:${e.inlayColor}" />`
    );
  }
  return o.join(`
`);
}
function N(t) {
  const e = [];
  e.push(
    `<text x="${(t.openAreaLeft + t.boardLeft) / 2}" y="296" class="fret-label">0</text>`
  );
  for (let r = 1; r <= t.visibleFrets; r += 1) {
    const s = (t.fretBoundaries[r - 1] + t.fretBoundaries[r]) / 2;
    e.push(`<text x="${s}" y="296" class="fret-label">${r}</text>`);
  }
  return e.join(`
`);
}
function q(t) {
  const e = [];
  for (let r = 1; r <= t.stringCount; r += 1) {
    const s = c(t, r, t.boardLeft);
    e.push(`<text x="26" y="${s + 4}" class="string-label">${r}</text>`);
  }
  return e.join(`
`);
}
function g(t, e, r) {
  return `<polygon points="${e.fret === 0 ? W(t, e.stringNumber) : Y(t, e.stringNumber, e.fret)}" class="${r}" />`;
}
const z = (t) => {
  const { parentElement: e, data: r, setStateValue: s } = t;
  R(e);
  let o = e.querySelector(".component-root");
  o || (o = document.createElement("div"), o.className = "component-root", e.appendChild(o));
  const n = j(r), d = {
    stringNumber: r.selectedString ?? r.stringCount,
    fret: r.selectedFret ?? 3
  };
  L.has(e) || L.set(e, {
    selected: d,
    hovered: null
  });
  const a = L.get(e);
  a.selected = {
    stringNumber: r.selectedString ?? a.selected.stringNumber,
    fret: r.selectedFret ?? a.selected.fret
  };
  const h = a.hovered ? g(n, a.hovered, "hover-cell") : "", p = g(
    n,
    a.selected,
    "selected-cell"
  ), { x: b, y: x } = T(
    n,
    a.selected
  ), E = Array.from(
    { length: n.visibleFrets + 1 },
    (i, l) => {
      const f = n.fretBoundaries[l], $ = l / n.visibleFrets, A = n.centerY - n.nutHalfWidth + $ * (n.nutHalfWidth - n.bodyHalfWidth), S = n.centerY + n.nutHalfWidth + $ * (n.bodyHalfWidth - n.nutHalfWidth);
      return `<line
        x1="${f}"
        y1="${A}"
        x2="${f}"
        y2="${S}"
        class="fret-line ${l === 0 ? "nut-line" : ""}"
        style="stroke:${r.theme.fretColor}"
      />`;
    }
  ).join(`
`), F = Array.from({ length: n.stringCount }, (i, l) => {
    const f = l + 1;
    return `
      <line
        x1="${n.openAreaLeft}"
        y1="${c(n, f, n.boardLeft)}"
        x2="${n.boardRight}"
        y2="${c(n, f, n.boardRight)}"
        class="string-line"
        style="stroke:${r.theme.stringColor}; stroke-width:${M(n, f)}"
      />
    `;
  }).join(`
`), v = [];
  for (let i = 1; i <= n.stringCount; i += 1) {
    v.push(
      `<polygon points="${W(n, i)}" class="hit-cell" data-string="${i}" data-fret="0" />`
    );
    for (let l = 1; l <= n.visibleFrets; l += 1)
      v.push(
        `<polygon points="${Y(n, i, l)}" class="hit-cell" data-string="${i}" data-fret="${l}" />`
      );
  }
  o.innerHTML = `
    <div class="fretboard-shell">
      <div class="badge">String ${a.selected.stringNumber} · Fret ${a.selected.fret}</div>
      <svg
        viewBox="0 0 ${n.viewBoxWidth} ${n.viewBoxHeight}"
        class="fretboard"
        role="img"
        aria-label="Fretboard selector"
      >
        <defs>
          <linearGradient id="bg-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${r.theme.bgTop}" />
            <stop offset="100%" stop-color="${r.theme.bgBottom}" />
          </linearGradient>

          <linearGradient id="board-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${r.instrument === "acoustic_guitar" ? "#241f1b" : "#c89a64"}" />
            <stop offset="50%" stop-color="${r.theme.boardBase}" />
            <stop offset="100%" stop-color="${r.instrument === "acoustic_guitar" ? "#191512" : "#a67647"}" />
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
          d="${G(n)}"
          fill="url(#board-gradient)"
          stroke="${r.theme.boardEdge}"
          stroke-width="3"
          filter="url(#soft-shadow)"
        />

        ${h}
        ${p}
        ${E}
        ${_(n, r.theme)}
        ${F}

        <line
          x1="${n.boardLeft}"
          y1="${n.centerY - n.nutHalfWidth}"
          x2="${n.boardLeft}"
          y2="${n.centerY + n.nutHalfWidth}"
          stroke="${r.theme.nutColor}"
          stroke-width="8"
          stroke-linecap="round"
        />

        <circle cx="${b}" cy="${x}" r="11" class="selected-marker-halo" />
        <circle
          cx="${b}"
          cy="${x}"
          r="7.5"
          class="selected-marker"
          style="fill:${r.theme.markerColor}; stroke:${r.theme.markerStroke}"
        />

        ${q(n)}
        ${N(n)}
        ${v.join(`
`)}
      </svg>
    </div>
  `;
  const y = o.querySelectorAll(".hit-cell"), k = [], C = [], B = [];
  y.forEach((i) => {
    const l = () => {
      a.hovered = {
        stringNumber: Number(i.dataset.string),
        fret: Number(i.dataset.fret)
      }, o.dispatchEvent(new CustomEvent("rerender"));
    }, f = () => {
      a.hovered = null, o.dispatchEvent(new CustomEvent("rerender"));
    }, $ = () => {
      a.selected = {
        stringNumber: Number(i.dataset.string),
        fret: Number(i.dataset.fret)
      }, s("selectedString", a.selected.stringNumber), s("selectedFret", a.selected.fret), o.dispatchEvent(new CustomEvent("rerender"));
    };
    i.addEventListener("mouseenter", l), i.addEventListener("mouseleave", f), i.addEventListener("click", $), k.push(() => i.removeEventListener("mouseenter", l)), C.push(() => i.removeEventListener("mouseleave", f)), B.push(() => i.removeEventListener("click", $));
  });
  const w = () => {
    z(t);
  };
  return o.addEventListener("rerender", w, { once: !0 }), () => {
    k.forEach((i) => i()), C.forEach((i) => i()), B.forEach((i) => i()), o?.removeEventListener("rerender", w);
  };
};
export {
  z as default
};
