const S = ":root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif}*{box-sizing:border-box}body{margin:0}.component-root,.fretboard-shell{width:100%}.badge{margin-bottom:8px;display:inline-block;padding:8px 12px;border-radius:999px;background:#ffffff0f;border:1px solid rgba(255,255,255,.08);color:var(--st-text-color, #f2f2f2);font-size:14px}.fretboard{width:100%;display:block}.fret-line{stroke-opacity:.86;stroke-linecap:round;stroke-width:2.5}.nut-line{stroke-opacity:0}.string-line{stroke-linecap:round;opacity:.96}.inlay{opacity:.92}.hover-cell{fill:#fff4d624;stroke:#fff4d638;stroke-width:1}.selected-cell{fill:#d8b36a1c;stroke:#ffeec66b;stroke-width:1.2}.selected-marker-halo{fill:#fff7e826}.selected-marker{stroke-width:2}.hit-cell{fill:transparent;cursor:pointer}.fret-label,.string-label{fill:#d8d0c2;font-size:14px;-webkit-user-select:none;user-select:none}.fret-label{text-anchor:middle}";
function Y(t) {
  if (t.querySelector("style[data-alt-tabs-fretboard]"))
    return;
  const n = document.createElement("style");
  n.setAttribute("data-alt-tabs-fretboard", "true"), n.textContent = S, t.appendChild(n);
}
const L = /* @__PURE__ */ new WeakMap();
function H(t) {
  const n = Array.from(
    { length: t.visibleFrets + 2 },
    (e, a) => a === 0 ? 0 : 1 - Math.pow(2, -a / 12)
  ), o = n[n.length - 1], s = t.boardRight - t.boardLeft, r = n.map(
    (e) => t.boardLeft + e / o * s
  );
  return {
    ...t,
    fretBoundaries: r
  };
}
function A(t) {
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
    nutHalfWidth: 72,
    bodyHalfWidth: 102,
    edgePaddingNut: 10,
    edgePaddingBody: 16,
    stringCount: t.stringCount
  });
}
function c(t, n, o) {
  const s = (o - t.boardLeft) / (t.boardRight - t.boardLeft), r = t.nutHalfWidth + s * (t.bodyHalfWidth - t.nutHalfWidth);
  if (t.stringCount === 1)
    return t.centerY;
  const e = (n - 1) / (t.stringCount - 1);
  return t.centerY - r + e * (r * 2);
}
function j(t, n) {
  const o = t.stringCount === 4 ? 4.6 : 3.8, s = t.stringCount === 4 ? 2.2 : 1.6;
  if (t.stringCount === 1)
    return o;
  const r = (n - 1) / (t.stringCount - 1);
  return s + r * (o - s);
}
function G(t) {
  const n = t.boardLeft, o = t.boardRight, s = t.centerY, r = s - t.nutHalfWidth - t.edgePaddingNut, e = s + t.nutHalfWidth + t.edgePaddingNut, a = s - t.bodyHalfWidth - t.edgePaddingBody, l = s + t.bodyHalfWidth + t.edgePaddingBody;
  return [
    `M ${n} ${r}`,
    `L ${o} ${a}`,
    `L ${o} ${l}`,
    `L ${n} ${e}`,
    "Z"
  ].join(" ");
}
function E(t, n) {
  const o = t.openAreaLeft, s = t.boardLeft, r = 10, e = c(t, n, o), a = c(t, n, s), l = n > 1 ? c(t, n - 1, s) : a - 22, u = n < t.stringCount ? c(t, n + 1, s) : a + 22, h = (l + a) / 2, b = (a + u) / 2;
  return [
    `${o},${e - r}`,
    `${s},${h}`,
    `${s},${b}`,
    `${o},${e + r}`
  ].join(" ");
}
function F(t, n, o) {
  const s = t.fretBoundaries[o - 1], r = t.fretBoundaries[o], e = c(t, n, s), a = c(t, n, r), l = n > 1 ? c(t, n - 1, s) : e - 22, u = n < t.stringCount ? c(t, n + 1, s) : e + 22, h = n > 1 ? c(t, n - 1, r) : a - 22, b = n < t.stringCount ? c(t, n + 1, r) : a + 22, v = (l + e) / 2, x = (e + u) / 2, g = (h + a) / 2, $ = (a + b) / 2;
  return [
    `${s},${v}`,
    `${r},${g}`,
    `${r},${$}`,
    `${s},${x}`
  ].join(" ");
}
function M(t, n) {
  const o = n.fret === 0 ? (t.openAreaLeft + t.boardLeft) / 2 : (t.fretBoundaries[n.fret - 1] + t.fretBoundaries[n.fret]) / 2;
  return { x: o, y: c(t, n.stringNumber, o) };
}
function m(t, n) {
  const o = [3, 5, 7, 9], s = [12], r = [];
  for (const e of o) {
    if (e > t.visibleFrets) continue;
    const a = (t.fretBoundaries[e - 1] + t.fretBoundaries[e]) / 2;
    r.push(
      `<circle cx="${a}" cy="${t.centerY}" r="7" class="inlay" style="fill:${n.inlayColor}" />`
    );
  }
  for (const e of s) {
    if (e > t.visibleFrets) continue;
    const a = (t.fretBoundaries[e - 1] + t.fretBoundaries[e]) / 2;
    r.push(
      `<circle cx="${a}" cy="${t.centerY - 22}" r="6.5" class="inlay" style="fill:${n.inlayColor}" />`
    ), r.push(
      `<circle cx="${a}" cy="${t.centerY + 22}" r="6.5" class="inlay" style="fill:${n.inlayColor}" />`
    );
  }
  return r.join(`
`);
}
function N(t) {
  const n = [];
  n.push(
    `<text x="${(t.openAreaLeft + t.boardLeft) / 2}" y="296" class="fret-label">0</text>`
  );
  for (let o = 1; o <= t.visibleFrets; o += 1) {
    const s = (t.fretBoundaries[o - 1] + t.fretBoundaries[o]) / 2;
    n.push(`<text x="${s}" y="296" class="fret-label">${o}</text>`);
  }
  return n.join(`
`);
}
function _(t) {
  const n = [];
  for (let o = 1; o <= t.stringCount; o += 1) {
    const s = c(t, o, t.boardLeft);
    n.push(`<text x="26" y="${s + 4}" class="string-label">${o}</text>`);
  }
  return n.join(`
`);
}
function W(t, n, o) {
  return `<polygon points="${n.fret === 0 ? E(t, n.stringNumber) : F(t, n.stringNumber, n.fret)}" class="${o}" />`;
}
const I = (t) => {
  const { parentElement: n, data: o, setStateValue: s } = t;
  Y(n);
  let r = n.querySelector(".component-root");
  r || (r = document.createElement("div"), r.className = "component-root", n.appendChild(r));
  const e = A(o), a = o.selectedString != null && o.selectedFret != null ? {
    stringNumber: o.selectedString,
    fret: o.selectedFret
  } : null;
  L.has(n) || L.set(n, {
    selected: a,
    hovered: null
  });
  const l = L.get(n);
  l.selected = a;
  const u = l.hovered ? W(e, l.hovered, "hover-cell") : "", h = l.selected != null ? W(e, l.selected, "selected-cell") : "", b = l.selected != null ? (() => {
    const { x: i, y: d } = M(
      e,
      l.selected
    );
    return `
            <circle cx="${i}" cy="${d}" r="11" class="selected-marker-halo" />
            <circle
              cx="${i}"
              cy="${d}"
              r="7.5"
              class="selected-marker"
              style="fill:${o.theme.markerColor}; stroke:${o.theme.markerStroke}"
            />
          `;
  })() : "", v = l.selected != null ? `<div class="badge">String ${l.selected.stringNumber} · Fret ${l.selected.fret}</div>` : '<div class="badge">No target selected</div>', x = Array.from(
    { length: e.visibleFrets + 1 },
    (i, d) => {
      const f = e.fretBoundaries[d], p = d / e.visibleFrets, k = e.centerY - e.nutHalfWidth + p * (e.nutHalfWidth - e.bodyHalfWidth), P = e.centerY + e.nutHalfWidth + p * (e.bodyHalfWidth - e.nutHalfWidth);
      return `<line
        x1="${f}"
        y1="${k}"
        x2="${f}"
        y2="${P}"
        class="fret-line ${d === 0 ? "nut-line" : ""}"
        style="stroke:${o.theme.fretColor}"
      />`;
    }
  ).join(`
`), g = Array.from({ length: e.stringCount }, (i, d) => {
    const f = d + 1;
    return `
      <line
        x1="${e.openAreaLeft}"
        y1="${c(e, f, e.boardLeft)}"
        x2="${e.boardRight}"
        y2="${c(e, f, e.boardRight)}"
        class="string-line"
        style="stroke:${o.theme.stringColor}; stroke-width:${j(e, f)}"
      />
    `;
  }).join(`
`), $ = [];
  for (let i = 1; i <= e.stringCount; i += 1) {
    $.push(
      `<polygon points="${E(e, i)}" class="hit-cell" data-string="${i}" data-fret="0" />`
    );
    for (let d = 1; d <= e.visibleFrets; d += 1)
      $.push(
        `<polygon points="${F(e, i, d)}" class="hit-cell" data-string="${i}" data-fret="${d}" />`
      );
  }
  r.innerHTML = `
    <div class="fretboard-shell">
      ${v}
      <svg
        viewBox="0 0 ${e.viewBoxWidth} ${e.viewBoxHeight}"
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
          width="${e.viewBoxWidth}"
          height="${e.viewBoxHeight}"
          fill="url(#bg-gradient)"
          rx="24"
        />

        <path
          d="${G(e)}"
          fill="url(#board-gradient)"
          stroke="${o.theme.boardEdge}"
          stroke-width="3"
          filter="url(#soft-shadow)"
        />

        ${u}
        ${h}
        ${x}
        ${m(e, o.theme)}
        ${g}

        <line
          x1="${e.boardLeft}"
          y1="${e.centerY - e.nutHalfWidth}"
          x2="${e.boardLeft}"
          y2="${e.centerY + e.nutHalfWidth}"
          stroke="${o.theme.nutColor}"
          stroke-width="8"
          stroke-linecap="round"
        />

        ${b}

        ${_(e)}
        ${N(e)}
        ${$.join(`
`)}
      </svg>
    </div>
  `;
  const R = r.querySelectorAll(".hit-cell"), C = [], y = [], w = [];
  R.forEach((i) => {
    const d = () => {
      l.hovered = {
        stringNumber: Number(i.dataset.string),
        fret: Number(i.dataset.fret)
      }, r.dispatchEvent(new CustomEvent("rerender"));
    }, f = () => {
      l.hovered = null, r.dispatchEvent(new CustomEvent("rerender"));
    }, p = () => {
      console.log("CLICK", i.dataset.string, i.dataset.fret);
      const k = {
        stringNumber: Number(i.dataset.string),
        fret: Number(i.dataset.fret)
      };
      s("selectedPosition", k), console.log("SENDING", {
        string: i.dataset.string,
        fret: i.dataset.fret
      });
    };
    i.addEventListener("mouseenter", d), i.addEventListener("mouseleave", f), i.addEventListener("click", p), C.push(() => i.removeEventListener("mouseenter", d)), y.push(() => i.removeEventListener("mouseleave", f)), w.push(() => i.removeEventListener("click", p));
  });
  const B = () => {
    I(t);
  };
  return r.addEventListener("rerender", B, { once: !0 }), () => {
    C.forEach((i) => i()), y.forEach((i) => i()), w.forEach((i) => i()), r?.removeEventListener("rerender", B);
  };
};
export {
  I as default
};
