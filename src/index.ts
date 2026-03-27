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

type Cell = {
  stringNumber: StringNumber;
  fret: number;
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
    nutHalfWidth: 72,
    bodyHalfWidth: 102,
    edgePaddingNut: 10,
    edgePaddingBody: 16,
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
  const halfWidth =
    geometry.nutHalfWidth +
    t * (geometry.bodyHalfWidth - geometry.nutHalfWidth);

  if (geometry.stringCount === 1) {
    return geometry.centerY;
  }

  const ratio = (stringNumber - 1) / (geometry.stringCount - 1);
  return geometry.centerY - halfWidth + ratio * (halfWidth * 2);
}

function stringGauge(geometry: Geometry, stringNumber: number): number {
  const maxGauge = geometry.stringCount === 4 ? 4.6 : 3.8;
  const minGauge = geometry.stringCount === 4 ? 2.2 : 1.6;

  if (geometry.stringCount === 1) {
    return maxGauge;
  }

  const ratio = (stringNumber - 1) / (geometry.stringCount - 1);
  return minGauge + ratio * (maxGauge - minGauge);
}

function boardPath(geometry: Geometry): string {
  const left = geometry.boardLeft;
  const right = geometry.boardRight;
  const cy = geometry.centerY;

  const topLeft = cy - geometry.nutHalfWidth - geometry.edgePaddingNut;
  const botLeft = cy + geometry.nutHalfWidth + geometry.edgePaddingNut;
  const topRight = cy - geometry.bodyHalfWidth - geometry.edgePaddingBody;
  const botRight = cy + geometry.bodyHalfWidth + geometry.edgePaddingBody;

  return [
    `M ${left} ${topLeft}`,
    `L ${right} ${topRight}`,
    `L ${right} ${botRight}`,
    `L ${left} ${botLeft}`,
    "Z",
  ].join(" ");
}

function openCellPolygon(geometry: Geometry, stringNumber: number): string {
  const x1 = geometry.openAreaLeft;
  const x2 = geometry.boardLeft;
  const pad = 10;

  const y1a = yOnString(geometry, stringNumber, x1);
  const y1b = yOnString(geometry, stringNumber, x2);

  const prev =
    stringNumber > 1 ? yOnString(geometry, stringNumber - 1, x2) : y1b - 22;
  const next =
    stringNumber < geometry.stringCount
      ? yOnString(geometry, stringNumber + 1, x2)
      : y1b + 22;

  const topRight = (prev + y1b) / 2;
  const bottomRight = (y1b + next) / 2;

  return [
    `${x1},${y1a - pad}`,
    `${x2},${topRight}`,
    `${x2},${bottomRight}`,
    `${x1},${y1a + pad}`,
  ].join(" ");
}

function fretCellPolygon(
  geometry: Geometry,
  stringNumber: number,
  fret: number,
): string {
  const x1 = geometry.fretBoundaries[fret - 1];
  const x2 = geometry.fretBoundaries[fret];

  const y1l = yOnString(geometry, stringNumber, x1);
  const y1r = yOnString(geometry, stringNumber, x2);

  const prevL =
    stringNumber > 1 ? yOnString(geometry, stringNumber - 1, x1) : y1l - 22;
  const nextL =
    stringNumber < geometry.stringCount
      ? yOnString(geometry, stringNumber + 1, x1)
      : y1l + 22;
  const prevR =
    stringNumber > 1 ? yOnString(geometry, stringNumber - 1, x2) : y1r - 22;
  const nextR =
    stringNumber < geometry.stringCount
      ? yOnString(geometry, stringNumber + 1, x2)
      : y1r + 22;

  const topLeft = (prevL + y1l) / 2;
  const bottomLeft = (y1l + nextL) / 2;
  const topRight = (prevR + y1r) / 2;
  const bottomRight = (y1r + nextR) / 2;

  return [
    `${x1},${topLeft}`,
    `${x2},${topRight}`,
    `${x2},${bottomRight}`,
    `${x1},${bottomLeft}`,
  ].join(" ");
}

function markerPosition(
  geometry: Geometry,
  cell: Cell,
): { x: number; y: number } {
  const x =
    cell.fret === 0
      ? (geometry.openAreaLeft + geometry.boardLeft) / 2
      : (geometry.fretBoundaries[cell.fret - 1] +
          geometry.fretBoundaries[cell.fret]) /
        2;

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

  const incomingSelected: Cell | null =
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

  const selectedMarkup =
    instance.selected != null
      ? renderCellOverlay(geometry, instance.selected, "selected-cell")
      : "";

  const markerMarkup =
    instance.selected != null
      ? (() => {
          const { x: markerX, y: markerY } = markerPosition(
            geometry,
            instance.selected!,
          );
          return `
            <circle cx="${markerX}" cy="${markerY}" r="11" class="selected-marker-halo" />
            <circle
              cx="${markerX}"
              cy="${markerY}"
              r="7.5"
              class="selected-marker"
              style="fill:${data.theme.markerColor}; stroke:${data.theme.markerStroke}"
            />
          `;
        })()
      : "";

  const badgeMarkup =
    instance.selected != null
      ? `<div class="badge">String ${instance.selected.stringNumber} · Fret ${instance.selected.fret}</div>`
      : `<div class="badge">No target selected</div>`;

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
      console.log("CLICK", cell.dataset.string, cell.dataset.fret);
      const selected = {
        stringNumber: Number(cell.dataset.string),
        fret: Number(cell.dataset.fret),
      };
      setStateValue("selectedPosition", selected);
      console.log("SENDING", {
        string: cell.dataset.string,
        fret: cell.dataset.fret,
      });
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
