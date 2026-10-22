'use client';

import { useEffect, useMemo, useRef } from 'react';
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  ChartConfiguration,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js';

Chart.register(BarController, BarElement, LineController, LineElement, PointElement, CategoryScale, LinearScale, Filler, Legend, Tooltip);

// Paleta validada para daltonismo sobre la superficie del sitio (#fffaf4): siena y verde, en ese orden fijo.
export const SERIES = ['#a0522d', '#2f8f6f'];
export const SERIES_WASH = 'rgba(160, 82, 45, 0.10)';
const INK = '#4f4741';
const MUTED = '#5f5852';
const GRID = 'rgba(99, 55, 37, 0.10)';
const SURFACE = '#fffaf4';

Chart.defaults.font.family = '"Karla", system-ui, -apple-system, "Segoe UI", sans-serif';
Chart.defaults.font.size = 13;
Chart.defaults.color = MUTED;
Chart.defaults.animation = false;

// Las barras de un mismo grupo van juntas (2px de separación) aunque el grosor esté topado en 24px:
// el ancho del grupo se calcula con el espacio real de cada categoría.
const BAR = 24;
const BAR_GAP = 2;
const tightGroups = {
  id: 'tightGroups',
  beforeUpdate(chart: Chart) {
    const count = chart.data.labels?.length ?? 0;
    const groups = chart.data.datasets.length;
    if ((chart.config as { type?: string }).type !== 'bar' || !count || groups < 2) return;
    const slot = (chart.chartArea?.width ?? chart.width) / count;
    // Cada barra ocupa un subespacio de ancho "sub"; la barra es BAR (o lo que quepa) y el resto es la separación.
    const categoryPercentage = Math.min(0.75, (groups * (BAR + BAR_GAP)) / slot);
    const sub = (slot * categoryPercentage) / groups;
    const barPercentage = Math.max(0.5, Math.min(BAR, sub - BAR_GAP) / sub);
    chart.data.datasets.forEach((dataset) => Object.assign(dataset, { categoryPercentage, barPercentage }));
  },
};
Chart.register(tightGroups);

const pesos = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 });

export function compactPesos(value: number) {
  const abs = Math.abs(value);
  const sign = value < 0 ? '−' : '';
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1).replace('.0', '')}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(1).replace('.0', '')}K`;
  return `${sign}$${abs}`;
}

function tooltip() {
  return {
    backgroundColor: '#1b1816',
    titleColor: '#f1e4d6',
    bodyColor: '#fffaf4',
    padding: 10,
    cornerRadius: 8,
    boxPadding: 4,
    usePointStyle: true,
    callbacks: {
      // Cada serie se identifica con una línea corta de su color, no con un cuadro.
      labelPointStyle: () => ({ pointStyle: 'line' as const, rotation: 0 }),
      labelColor: (context: { dataset: { borderColor?: unknown; backgroundColor?: unknown } }) => {
        const color = String(context.dataset.borderColor && typeof context.dataset.borderColor === 'string' ? context.dataset.borderColor : context.dataset.backgroundColor);
        return { borderColor: color, backgroundColor: color, borderWidth: 3 };
      },
      label: (context: { dataset: { label?: string }; parsed: { x: number | null; y: number | null }; chart: { options: { indexAxis?: string } } }) => {
        const value = context.chart.options.indexAxis === 'y' ? context.parsed.x : context.parsed.y;
        return ` ${pesos.format(value ?? 0)}  ${context.dataset.label ?? ''}`;
      },
    },
  };
}

function valueAxis() {
  return {
    beginAtZero: true,
    border: { display: false },
    grid: { color: GRID, lineWidth: 1, drawTicks: false },
    ticks: { padding: 8, maxTicksLimit: 5, callback: (value: string | number) => compactPesos(Number(value)) },
  };
}

function categoryAxis() {
  return { border: { color: 'rgba(99, 55, 37, 0.28)' }, grid: { display: false }, ticks: { color: MUTED, maxRotation: 0, autoSkipPadding: 12 } };
}

// Monta un Chart.js sobre un canvas y lo vuelve a dibujar cuando cambian los datos.
function ChartCanvas({ config, height, label }: { config: ChartConfiguration; height: number; label: string }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const chart = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvas.current) return;
    chart.current?.destroy();
    chart.current = new Chart(canvas.current, config);
    return () => { chart.current?.destroy(); chart.current = null; };
  }, [config]);

  return (
    <div className="financeChart" style={{ height }}>
      <canvas ref={canvas} role="img" aria-label={label} />
    </div>
  );
}

export function GroupedColumns({ labels, series, label }: { labels: string[]; series: { label: string; data: number[] }[]; label: string }) {
  const config = useMemo<ChartConfiguration>(() => ({
    type: 'bar',
    data: {
      labels,
      datasets: series.map((row, index) => ({
        label: row.label,
        data: row.data,
        backgroundColor: SERIES[index],
        hoverBackgroundColor: SERIES[index] + 'cc',
        borderRadius: { topLeft: 4, topRight: 4 },
        borderSkipped: 'start',
        maxBarThickness: BAR,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top', align: 'start', labels: { color: INK, usePointStyle: true, pointStyle: 'rect', boxWidth: 10, boxHeight: 10, padding: 16 } },
        tooltip: tooltip(),
      },
      scales: { x: categoryAxis(), y: valueAxis() },
    },
  }), [labels, series]);
  return <ChartCanvas config={config} height={280} label={label} />;
}

export function AreaLine({ labels, data, name, label }: { labels: string[]; data: number[]; name: string; label: string }) {
  const config = useMemo<ChartConfiguration>(() => ({
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: name,
        data,
        borderColor: SERIES[0],
        backgroundColor: SERIES_WASH,
        borderWidth: 2,
        borderJoinStyle: 'round',
        borderCapStyle: 'round',
        fill: 'origin',
        tension: 0,
        pointRadius: data.map((_, index) => (index === data.length - 1 ? 4 : 0)),
        pointBackgroundColor: SERIES[0],
        pointBorderColor: SURFACE,
        pointBorderWidth: 2,
        pointHoverRadius: 5,
        pointHitRadius: 14,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { display: false }, tooltip: tooltip() },
      scales: { x: categoryAxis(), y: valueAxis() },
    },
  }), [labels, data, name]);
  return <ChartCanvas config={config} height={240} label={label} />;
}

// Barras horizontales en HTML: el nombre va arriba de su barra, así nunca se recorta en tarjetas angostas.
export function HorizontalBars({ rows, label }: { rows: { label: string; amount: number; count?: number }[]; label: string }) {
  const max = Math.max(...rows.map((row) => row.amount), 1);
  return (
    <ul className="financeBars" aria-label={label}>
      {rows.map((row) => (
        <li key={row.label} title={`${row.label}: ${pesos.format(row.amount)}${row.count ? ` · ${row.count} ${row.count === 1 ? 'servicio' : 'servicios'}` : ''}`}>
          <span className="financeBarLabel">{row.label}</span>
          <span className="financeBarTrack">
            {/* El importe va pegado a la punta; se reserva su espacio para que la barra más larga no lo empuje fuera. */}
            <span className="financeBar" style={{ width: `calc((100% - 84px) * ${Math.max(row.amount / max, 0.01)})`, background: SERIES[0] }} />
            <span className="financeBarValue">{pesos.format(row.amount)}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}
