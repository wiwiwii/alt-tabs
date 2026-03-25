import "./style.css";

type StringNumber = 1 | 2 | 3 | 4;

type Theme = {
  boardBase: string;
  boardEdge: string;
  fretColor: string;
  nutColor: string;
  inlayColor: string;
  labelColor: string;
  stringColor: string;
  markerColor: string;
  markerStroke: string;
  hoverFill: string;
  bgTop: string;
  bgBottom: string;
};

type Cell = {
  stringNumber: StringNumber;
  fret: number;
};

type Geometry = {
  viewBoxWidth: number;
  viewBoxHeight: number;
  centerY: number;
  boardLeft: number;
  boardRight: number;
  openAreaLeft: number;
  visibleFrets: number;
  fretBoundaries: number[];
  nutHalfWidth: number;
  bodyHalfWidth: number;
  edgePaddingNut: number;
  edgePaddingBody: number;
  stringCount: number;
};

const theme: Theme = {
  boardBase: "#b98b56",
  boardEdge: "#9a6f42",
  fretColor: "#000111",
  nutColor: "#eee3d1",
  inlayColor: "#111111",
  labelColor: "#2a2119",
  stringColor: "#ffffff",
  markerColor: "#2a2a2a",
  markerStroke: "#f5efe6",
  hoverFill: "rgba(0, 0, 0, 0.08)",
  bgTop: "#191614",
  bgBottom: "#110f0e",
};
const geometry: Geometry = createGeometry({
  viewBoxWidth: 1600,
  viewBoxHeight: 320,
  centerY: 170,
  boardLeft: 150,
  boardRight: 1540,
  openAreaLeft: 56,
  visibleFrets: 14,
  nutHalfWidth: 45,
  bodyHalfWidth: 96,
  edgePaddingNut: 10,
  edgePaddingBody: 14,
  stringCount: 4,
});

let hovered: Cell | null = null;
let selected: Cell = { stringNumber: 4, fret: 3 };

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) {
  throw new Error("#app not found");
}

app.innerHTML = `
  <main class="shell">
    <section class="panel">
      <div class="topbar">
        <div>
          <div class="eyebrow">Bass guitar prototype</div>
          <h1>Jazz Bass-inspired fretboard selector</h1>
        </div>
        <div class="badge" id="selection-badge"></div>
      </div>
      <div class="svg-wrap" id="svg-wrap"></div>
      <div class="legend">
        <span>Click any string/fret cell to select the destination position.</span>
        <span>Theme: maple board · black dots · ivory nut</span>
      </div>
    </section>
  </main>
`;

const svgWrapEl = document.querySelector<HTMLDivElement>("#svg-wrap");
const badgeEl = document.querySelector<HTMLDivElement>("#selection-badge");
if (!svgWrapEl || !badgeEl) {
  throw new Error("UI mount failed");
}
const svgWrap: HTMLDivElement = svgWrapEl;
const badge: HTMLDivElement = badgeEl;

function createGeometry(input: Omit<Geometry, "fretBoundaries">): Geometry {
  const scaleFractions = Array.from(
    { length: input.visibleFrets + 2 },
    (_, idx) => {
      if (idx === 0) return 0;
      return 1 - Math.pow(2, -idx / 12);
    },
  );

  const maxFraction = scaleFractions[scaleFractions.length - 1];
  const boardLength = input.boardRight - input.boardLeft;

  const fretBoundaries = scaleFractions.map(
    (fraction) => input.boardLeft + (fraction / maxFraction) * boardLength,
  );

  return {
    ...input,
    fretBoundaries,
  };
}

function yOnString(stringNumber: StringNumber, x: number): number {
  const t =
    (x - geometry.boardLeft) / (geometry.boardRight - geometry.boardLeft);
  const clampedT = Math.max(0, Math.min(1, t));

  const nutTop =
    geometry.centerY - geometry.nutHalfWidth + geometry.edgePaddingNut;
  const nutBottom =
    geometry.centerY + geometry.nutHalfWidth - geometry.edgePaddingNut;

  const bodyTop =
    geometry.centerY - geometry.bodyHalfWidth + geometry.edgePaddingBody;
  const bodyBottom =
    geometry.centerY + geometry.bodyHalfWidth - geometry.edgePaddingBody;

  const fraction = (stringNumber - 1) / (geometry.stringCount - 1);
  const yAtNut = nutTop + fraction * (nutBottom - nutTop);
  const yAtBody = bodyTop + fraction * (bodyBottom - bodyTop);

  return yAtNut + clampedT * (yAtBody - yAtNut);
}

function midpointY(a: StringNumber, b: StringNumber, x: number): number {
  return (yOnString(a, x) + yOnString(b, x)) / 2;
}

function stringGauge(stringNumber: StringNumber): number {
  return [3.6, 4.4, 5.3, 6.5][stringNumber - 1];
}

function boardPath(): string {
  const left = geometry.boardLeft;
  const right = geometry.boardRight;
  const topLeft = geometry.centerY - geometry.nutHalfWidth;
  const bottomLeft = geometry.centerY + geometry.nutHalfWidth;
  const topRight = geometry.centerY - geometry.bodyHalfWidth;
  const bottomRight = geometry.centerY + geometry.bodyHalfWidth;

  return [
    `M ${left} ${topLeft}`,
    `L ${right} ${topRight}`,
    `L ${right} ${bottomRight}`,
    `L ${left} ${bottomLeft}`,
    "Z",
  ].join(" ");
}

function openCellPolygon(stringNumber: StringNumber): string {
  const topY =
    stringNumber === 1
      ? yOnString(1, geometry.boardLeft) - 12
      : midpointY(
          (stringNumber - 1) as StringNumber,
          stringNumber,
          geometry.boardLeft,
        );

  const bottomY =
    stringNumber === geometry.stringCount
      ? yOnString(geometry.stringCount, geometry.boardLeft) + 12
      : midpointY(
          stringNumber,
          (stringNumber + 1) as StringNumber,
          geometry.boardLeft,
        );

  return [
    `${geometry.openAreaLeft},${topY}`,
    `${geometry.boardLeft},${topY}`,
    `${geometry.boardLeft},${bottomY}`,
    `${geometry.openAreaLeft},${bottomY}`,
  ].join(" ");
}

function fretCellPolygon(stringNumber: StringNumber, fret: number): string {
  const x1 = geometry.fretBoundaries[fret - 1];
  const x2 = geometry.fretBoundaries[fret];

  const topLeftY =
    stringNumber === 1
      ? yOnString(1, x1) - 12
      : midpointY((stringNumber - 1) as StringNumber, stringNumber, x1);

  const topRightY =
    stringNumber === 1
      ? yOnString(1, x2) - 12
      : midpointY((stringNumber - 1) as StringNumber, stringNumber, x2);

  const bottomLeftY =
    stringNumber === geometry.stringCount
      ? yOnString(geometry.stringCount, x1) + 12
      : midpointY(stringNumber, (stringNumber + 1) as StringNumber, x1);

  const bottomRightY =
    stringNumber === geometry.stringCount
      ? yOnString(geometry.stringCount, x2) + 12
      : midpointY(stringNumber, (stringNumber + 1) as StringNumber, x2);

  return [
    `${x1},${topLeftY}`,
    `${x2},${topRightY}`,
    `${x2},${bottomRightY}`,
    `${x1},${bottomLeftY}`,
  ].join(" ");
}

function markerPosition(cell: Cell): { x: number; y: number } {
  if (cell.fret === 0) {
    const x = (geometry.openAreaLeft + geometry.boardLeft) / 2;
    return { x, y: yOnString(cell.stringNumber, geometry.boardLeft) };
  }

  const x1 = geometry.fretBoundaries[cell.fret - 1];
  const x2 = geometry.fretBoundaries[cell.fret];
  const x = (x1 + x2) / 2;

  return { x, y: yOnString(cell.stringNumber, x) };
}

function inlayMarkup(): string {
  const single = [3, 5, 7, 9];
  const double = [12];
  const circles: string[] = [];

  for (const fret of single) {
    const x =
      (geometry.fretBoundaries[fret - 1] + geometry.fretBoundaries[fret]) / 2;
    circles.push(
      `<circle cx="${x}" cy="${geometry.centerY}" r="7" class="inlay" style="fill:${theme.inlayColor}" />`,
    );
  }

  for (const fret of double) {
    const x =
      (geometry.fretBoundaries[fret - 1] + geometry.fretBoundaries[fret]) / 2;
    circles.push(
      `<circle cx="${x}" cy="${geometry.centerY - 22}" r="6.5" class="inlay" style="fill:${theme.inlayColor}" />`,
    );
    circles.push(
      `<circle cx="${x}" cy="${geometry.centerY + 22}" r="6.5" class="inlay" style="fill:${theme.inlayColor}" />`,
    );
  }

  return circles.join("\n");
}

function fretLabels(): string {
  const labels: string[] = [];

  labels.push(
    `<text x="${(geometry.openAreaLeft + geometry.boardLeft) / 2}" y="296" class="fret-label">0</text>`,
  );

  for (let fret = 1; fret <= geometry.visibleFrets; fret += 1) {
    const x =
      (geometry.fretBoundaries[fret - 1] + geometry.fretBoundaries[fret]) / 2;
    labels.push(`<text x="${x}" y="296" class="fret-label">${fret}</text>`);
  }

  return labels.join("\n");
}

function stringLabels(): string {
  const labels: string[] = [];

  for (let n = 1 as StringNumber; n <= geometry.stringCount; n += 1) {
    const y = yOnString(n, geometry.boardLeft);
    labels.push(`<text x="26" y="${y + 4}" class="string-label">${n}</text>`);
  }

  return labels.join("\n");
}

function renderCellOverlay(cell: Cell, className: string): string {
  const points =
    cell.fret === 0
      ? openCellPolygon(cell.stringNumber)
      : fretCellPolygon(cell.stringNumber, cell.fret);

  return `<polygon points="${points}" class="${className}" />`;
}

function render(): void {
  const hoverMarkup = hovered ? renderCellOverlay(hovered, "hover-cell") : "";
  const selectedMarkup = renderCellOverlay(selected, "selected-cell");
  const { x: markerX, y: markerY } = markerPosition(selected);

  const fretLines = Array.from(
    { length: geometry.visibleFrets + 1 },
    (_, idx) => {
      const x = geometry.fretBoundaries[idx];
      const t = idx / geometry.visibleFrets;
      const y1 =
        geometry.centerY -
        geometry.nutHalfWidth +
        t * (geometry.nutHalfWidth - geometry.bodyHalfWidth);
      const y2 =
        geometry.centerY +
        geometry.nutHalfWidth +
        t * (geometry.bodyHalfWidth - geometry.nutHalfWidth);

      return `<line
  x1="${x}"
  y1="${y1}"
  x2="${x}"
  y2="${y2}"
  class="fret-line ${idx === 0 ? "nut-line" : ""}"
  style="stroke:${theme.fretColor}"
/>`;
    },
  ).join("\n");

  const stringLines = Array.from({ length: geometry.stringCount }, (_, idx) => {
    const n = (idx + 1) as StringNumber;
    return `
      <line
        x1="${geometry.openAreaLeft}"
        y1="${yOnString(n, geometry.boardLeft)}"
        x2="${geometry.boardRight}"
        y2="${yOnString(n, geometry.boardRight)}"
        class="string-line"
style="stroke:${theme.stringColor}; stroke-width:${stringGauge(n)}"
      />
    `;
  }).join("\n");

  const hitRegions: string[] = [];
  for (let n = 1 as StringNumber; n <= geometry.stringCount; n += 1) {
    hitRegions.push(
      `<polygon points="${openCellPolygon(n)}" class="hit-cell" data-string="${n}" data-fret="0" />`,
    );

    for (let fret = 1; fret <= geometry.visibleFrets; fret += 1) {
      hitRegions.push(
        `<polygon points="${fretCellPolygon(n, fret)}" class="hit-cell" data-string="${n}" data-fret="${fret}" />`,
      );
    }
  }

  svgWrap.innerHTML = `
    <svg
      viewBox="0 0 ${geometry.viewBoxWidth} ${geometry.viewBoxHeight}"
      class="fretboard"
      role="img"
      aria-label="Bass guitar fretboard selector"
    >
      <defs>
        <linearGradient id="bg-gradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${theme.bgTop}" />
          <stop offset="100%" stop-color="${theme.bgBottom}" />
        </linearGradient>

        <linearGradient id="board-gradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#c89a64" />
          <stop offset="50%" stop-color="${theme.boardBase}" />
          <stop offset="100%" stop-color="#a67647" />
        </linearGradient>
        <filter id="soft-shadow" x="-20%" y="-50%" width="140%" height="200%">
          <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.35" />
        </filter>

        <pattern id="grain" width="180" height="30" patternUnits="userSpaceOnUse">
          <rect width="180" height="30" fill="transparent" />
          <path
            d="M 0 14 C 20 9, 40 20, 60 14 S 100 8, 120 14 S 160 18, 180 14"
            stroke="rgba(255,255,255,0.03)"
            fill="none"
            stroke-width="1"
          />
          <path
            d="M 0 22 C 24 18, 44 26, 68 22 S 112 17, 138 22 S 160 26, 180 22"
            stroke="rgba(255,255,255,0.018)"
            fill="none"
            stroke-width="1"
          />
        </pattern>
      </defs>

      <rect
        x="0"
        y="0"
        width="${geometry.viewBoxWidth}"
        height="${geometry.viewBoxHeight}"
        fill="url(#bg-gradient)"
        rx="24"
      />

      <path
        d="${boardPath()}"
        fill="url(#board-gradient)"
        stroke="${theme.boardEdge}"
        stroke-width="3"
        filter="url(#soft-shadow)"
      />

      <path d="${boardPath()}" fill="url(#grain)" opacity="0.8" />

      ${hoverMarkup}
      ${selectedMarkup}
      ${fretLines}
      ${inlayMarkup()}
      ${stringLines}

      <line
        x1="${geometry.boardLeft}"
        y1="${geometry.centerY - geometry.nutHalfWidth}"
        x2="${geometry.boardLeft}"
        y2="${geometry.centerY + geometry.nutHalfWidth}"
        stroke="${theme.nutColor}"
        stroke-width="8"
        stroke-linecap="round"
      />

      <circle cx="${markerX}" cy="${markerY}" r="11" class="selected-marker-halo" />
      <circle cx="${markerX}" cy="${markerY}" r="7.5" class="selected-marker" />

      <text x="18" y="34" class="section-label">String</text>
      <text x="${geometry.boardRight - 28}" y="34" class="section-label" text-anchor="end">Fret</text>

      ${stringLabels()}
      ${fretLabels()}
      ${hitRegions.join("\n")}
    </svg>
  `;

  badge.textContent = `String ${selected.stringNumber} · Fret ${selected.fret}`;

  const cells = svgWrap.querySelectorAll<SVGPolygonElement>(".hit-cell");
  cells.forEach((cell) => {
    cell.addEventListener("mouseenter", () => {
      hovered = {
        stringNumber: Number(cell.dataset.string) as StringNumber,
        fret: Number(cell.dataset.fret),
      };
      render();
    });

    cell.addEventListener("mouseleave", () => {
      hovered = null;
      render();
    });

    cell.addEventListener("click", () => {
      selected = {
        stringNumber: Number(cell.dataset.string) as StringNumber,
        fret: Number(cell.dataset.fret),
      };
      render();
    });
  });
}

render();
