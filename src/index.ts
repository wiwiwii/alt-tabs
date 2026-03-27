import {
  FrontendRenderer,
  FrontendRendererArgs,
} from "@streamlit/component-v2-lib";
import componentCss from "./style.css?inline";

function ensureStyles(parentElement: HTMLElement | ShadowRoot): void {
  if (parentElement.querySelector("style[data-alt-tabs-fretboard]")) {
    return;
  }

  const style = document.createElement("style");
  style.setAttribute("data-alt-tabs-fretboard", "true");
  style.textContent = componentCss;
  parentElement.appendChild(style);
}
type StringNumber = number;

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

type ComponentData = {
  instrument: "acoustic_guitar" | "electric_guitar" | "bass";
  stringCount: number;
  visibleFrets: number;
  selectedString: number | null;
  selectedFret: number | null;
  theme: Theme;
};

type FrontendState = {
  selectedPosition: Cell | null;
  selectedString: number | null;
  selectedFret: number | null;
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

type InstanceState = {
  selected: Cell | null;
  hovered: Cell | null;
};

const instances: WeakMap<FrontendRendererArgs["parentElement"], InstanceState> =
  new WeakMap();

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

function geometryForInstrument(data: ComponentData): Geometry {
  if (data.instrument === "bass") {
    return createGeometry({
      viewBoxWidth: 1600,
      viewBoxHeight: 320,
      centerY: 170,
      boardLeft: 150,
      boardRight: 1540,
      openAreaLeft: 56,
      visibleFrets: data.visibleFrets,
      nutHalfWidth: 52,
      bodyHalfWidth: 96,
      edgePaddingNut: 10,
      edgePaddingBody: 14,
      stringCount: data.stringCount,
    });
  }

  return createGeometry({
    viewBoxWidth: 1600,
    viewBoxHeight: 320,
    centerY: 170,
    boardLeft: 150,
    boardRight: 1540,
    openAreaLeft: 56,
    visibleFrets: data.visibleFrets,
    nutHalfWidth: 70,
    bodyHalfWidth: 96,
    edgePaddingNut: 10,
    edgePaddingBody: 14,
    stringCount: data.stringCount,
  });
}

function yOnString(
  geometry: Geometry,
  stringNumber: number,
  x: number,
): number {
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

  const fraction =
    geometry.stringCount === 1
      ? 0
      : (stringNumber - 1) / (geometry.stringCount - 1);

  const yAtNut = nutTop + fraction * (nutBottom - nutTop);
  const yAtBody = bodyTop + fraction * (bodyBottom - bodyTop);

  return yAtNut + clampedT * (yAtBody - yAtNut);
}

function midpointY(
  geometry: Geometry,
  a: number,
  b: number,
  x: number,
): number {
  return (yOnString(geometry, a, x) + yOnString(geometry, b, x)) / 2;
}

function stringGauge(geometry: Geometry, stringNumber: number): number {
  if (geometry.stringCount === 4) {
    return [3.6, 4.4, 5.3, 6.5][stringNumber - 1];
  }
  return [1.3, 1.6, 1.9, 2.3, 2.9, 3.6][stringNumber - 1];
}

function boardPath(geometry: Geometry): string {
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

function openCellPolygon(geometry: Geometry, stringNumber: number): string {
  const topY =
    stringNumber === 1
      ? yOnString(geometry, 1, geometry.boardLeft) - 12
      : midpointY(geometry, stringNumber - 1, stringNumber, geometry.boardLeft);

  const bottomY =
    stringNumber === geometry.stringCount
      ? yOnString(geometry, geometry.stringCount, geometry.boardLeft) + 12
      : midpointY(geometry, stringNumber, stringNumber + 1, geometry.boardLeft);

  return [
    `${geometry.openAreaLeft},${topY}`,
    `${geometry.boardLeft},${topY}`,
    `${geometry.boardLeft},${bottomY}`,
    `${geometry.openAreaLeft},${bottomY}`,
  ].join(" ");
}

function fretCellPolygon(
  geometry: Geometry,
  stringNumber: number,
  fret: number,
): string {
  const x1 = geometry.fretBoundaries[fret - 1];
  const x2 = geometry.fretBoundaries[fret];

  const topLeftY =
    stringNumber === 1
      ? yOnString(geometry, 1, x1) - 12
      : midpointY(geometry, stringNumber - 1, stringNumber, x1);

  const topRightY =
    stringNumber === 1
      ? yOnString(geometry, 1, x2) - 12
      : midpointY(geometry, stringNumber - 1, stringNumber, x2);

  const bottomLeftY =
    stringNumber === geometry.stringCount
      ? yOnString(geometry, geometry.stringCount, x1) + 12
      : midpointY(geometry, stringNumber, stringNumber + 1, x1);

  const bottomRightY =
    stringNumber === geometry.stringCount
      ? yOnString(geometry, geometry.stringCount, x2) + 12
      : midpointY(geometry, stringNumber, stringNumber + 1, x2);

  return [
    `${x1},${topLeftY}`,
    `${x2},${topRightY}`,
    `${x2},${bottomRightY}`,
    `${x1},${bottomLeftY}`,
  ].join(" ");
}

function markerPosition(
  geometry: Geometry,
  cell: Cell,
): { x: number; y: number } {
  if (cell.fret === 0) {
    const x = (geometry.openAreaLeft + geometry.boardLeft) / 2;
    return { x, y: yOnString(geometry, cell.stringNumber, geometry.boardLeft) };
  }

  const x1 = geometry.fretBoundaries[cell.fret - 1];
  const x2 = geometry.fretBoundaries[cell.fret];
  const x = (x1 + x2) / 2;

  return { x, y: yOnString(geometry, cell.stringNumber, x) };
}

function inlayMarkup(geometry: Geometry, theme: Theme): string {
  const single = [3, 5, 7, 9];
  const double = [12];
  const circles: string[] = [];

  for (const fret of single) {
    if (fret > geometry.visibleFrets) continue;
    const x =
      (geometry.fretBoundaries[fret - 1] + geometry.fretBoundaries[fret]) / 2;
    circles.push(
      `<circle cx="${x}" cy="${geometry.centerY}" r="7" class="inlay" style="fill:${theme.inlayColor}" />`,
    );
  }

  for (const fret of double) {
    if (fret > geometry.visibleFrets) continue;
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

function fretLabels(geometry: Geometry): string {
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

function stringLabels(geometry: Geometry): string {
  const labels: string[] = [];

  for (let n = 1; n <= geometry.stringCount; n += 1) {
    const y = yOnString(geometry, n, geometry.boardLeft);
    labels.push(`<text x="26" y="${y + 4}" class="string-label">${n}</text>`);
  }

  return labels.join("\n");
}

function renderCellOverlay(
  geometry: Geometry,
  cell: Cell,
  className: string,
): string {
  const points =
    cell.fret === 0
      ? openCellPolygon(geometry, cell.stringNumber)
      : fretCellPolygon(geometry, cell.stringNumber, cell.fret);

  return `<polygon points="${points}" class="${className}" />`;
}

const FretboardComponent: FrontendRenderer<FrontendState, ComponentData> = (
  args,
) => {
  const { parentElement, data, setStateValue } = args;

  ensureStyles(parentElement);
  let root = parentElement.querySelector<HTMLDivElement>(".component-root");
  if (!root) {
    root = document.createElement("div");
    root.className = "component-root";
    parentElement.appendChild(root);
  }

  const geometry = geometryForInstrument(data);

  const incomingSelected =
    data.selectedString != null && data.selectedFret != null
      ? {
          stringNumber: data.selectedString,
          fret: data.selectedFret,
        }
      : null;

  if (!instances.has(parentElement)) {
    instances.set(parentElement, {
      selected: incomingSelected,
      hovered: null,
    });
  }

  const instance = instances.get(parentElement)!;

  instance.selected = incomingSelected;

  const hoverMarkup = instance.hovered
    ? renderCellOverlay(geometry, instance.hovered, "hover-cell")
    : "";
  const selectedMarkup = instance.selected
    ? renderCellOverlay(geometry, instance.selected, "selected-cell")
    : "";
  const marker = instance.selected
    ? markerPosition(geometry, instance.selected)
    : null;
  const badgeMarkup = instance.selected
    ? `<div class="badge">String ${instance.selected.stringNumber} · Fret ${instance.selected.fret}</div>`
    : `<div class="badge">No target selected</div>`;
  const markerMarkup = marker
    ? `
        <circle cx="${marker.x}" cy="${marker.y}" r="11" class="selected-marker-halo" />
        <circle
          cx="${marker.x}"
          cy="${marker.y}"
          r="7.5"
          class="selected-marker"
          style="fill:${data.theme.markerColor}; stroke:${data.theme.markerStroke}"
        />
      `
    : "";

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
        style="stroke:${data.theme.fretColor}"
      />`;
    },
  ).join("\n");

  const stringLines = Array.from({ length: geometry.stringCount }, (_, idx) => {
    const n = idx + 1;
    return `
      <line
        x1="${geometry.openAreaLeft}"
        y1="${yOnString(geometry, n, geometry.boardLeft)}"
        x2="${geometry.boardRight}"
        y2="${yOnString(geometry, n, geometry.boardRight)}"
        class="string-line"
        style="stroke:${data.theme.stringColor}; stroke-width:${stringGauge(geometry, n)}"
      />
    `;
  }).join("\n");

  const hitRegions: string[] = [];
  for (let n = 1; n <= geometry.stringCount; n += 1) {
    hitRegions.push(
      `<polygon points="${openCellPolygon(geometry, n)}" class="hit-cell" data-string="${n}" data-fret="0" />`,
    );

    for (let fret = 1; fret <= geometry.visibleFrets; fret += 1) {
      hitRegions.push(
        `<polygon points="${fretCellPolygon(geometry, n, fret)}" class="hit-cell" data-string="${n}" data-fret="${fret}" />`,
      );
    }
  }

  root.innerHTML = `
    <div class="fretboard-shell">
      ${badgeMarkup}
      <svg
        viewBox="0 0 ${geometry.viewBoxWidth} ${geometry.viewBoxHeight}"
        class="fretboard"
        role="img"
        aria-label="Fretboard selector"
      >
        <defs>
          <linearGradient id="bg-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${data.theme.bgTop}" />
            <stop offset="100%" stop-color="${data.theme.bgBottom}" />
          </linearGradient>

          <linearGradient id="board-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${data.instrument === "acoustic_guitar" ? "#241f1b" : "#c89a64"}" />
            <stop offset="50%" stop-color="${data.theme.boardBase}" />
            <stop offset="100%" stop-color="${data.instrument === "acoustic_guitar" ? "#191512" : "#a67647"}" />
          </linearGradient>

          <filter id="soft-shadow" x="-20%" y="-50%" width="140%" height="200%">
            <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.35" />
          </filter>
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
          d="${boardPath(geometry)}"
          fill="url(#board-gradient)"
          stroke="${data.theme.boardEdge}"
          stroke-width="3"
          filter="url(#soft-shadow)"
        />

        ${hoverMarkup}
        ${selectedMarkup}
        ${fretLines}
        ${inlayMarkup(geometry, data.theme)}
        ${stringLines}

        <line
          x1="${geometry.boardLeft}"
          y1="${geometry.centerY - geometry.nutHalfWidth}"
          x2="${geometry.boardLeft}"
          y2="${geometry.centerY + geometry.nutHalfWidth}"
          stroke="${data.theme.nutColor}"
          stroke-width="8"
          stroke-linecap="round"
        />

        ${markerMarkup}

        ${stringLabels(geometry)}
        ${fretLabels(geometry)}
        ${hitRegions.join("\n")}
      </svg>
    </div>
  `;

  const cells = root.querySelectorAll<SVGPolygonElement>(".hit-cell");

  const enterHandlers: Array<() => void> = [];
  const leaveHandlers: Array<() => void> = [];
  const clickHandlers: Array<() => void> = [];

  cells.forEach((cell) => {
    const onEnter = () => {
      instance.hovered = {
        stringNumber: Number(cell.dataset.string),
        fret: Number(cell.dataset.fret),
      };
      root!.dispatchEvent(new CustomEvent("rerender"));
    };

    const onLeave = () => {
      instance.hovered = null;
      root!.dispatchEvent(new CustomEvent("rerender"));
    };

    const onClick = () => {
      const selected: Cell = {
        stringNumber: Number(cell.dataset.string),
        fret: Number(cell.dataset.fret),
      };
      instance.selected = selected;
      setStateValue("selectedPosition", selected);
      setStateValue("selectedString", selected.stringNumber);
      setStateValue("selectedFret", selected.fret);
      root!.dispatchEvent(new CustomEvent("rerender"));
    };

    cell.addEventListener("mouseenter", onEnter);
    cell.addEventListener("mouseleave", onLeave);
    cell.addEventListener("click", onClick);

    enterHandlers.push(() => cell.removeEventListener("mouseenter", onEnter));
    leaveHandlers.push(() => cell.removeEventListener("mouseleave", onLeave));
    clickHandlers.push(() => cell.removeEventListener("click", onClick));
  });

  const rerender = () => {
    FretboardComponent(args);
  };

  root.addEventListener("rerender", rerender, { once: true });

  return () => {
    enterHandlers.forEach((fn) => fn());
    leaveHandlers.forEach((fn) => fn());
    clickHandlers.forEach((fn) => fn());
    root?.removeEventListener("rerender", rerender);
  };
};

export default FretboardComponent;
