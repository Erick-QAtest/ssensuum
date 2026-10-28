import type { FunnelStage } from '../../lib/types';

export const STAGES: Record<FunnelStage, { label: string; hint: string; tone: 'ok' | 'wait' | 'alert' | 'plain' }> = {
  lead: { label: 'Interesado', hint: 'Dejó sus datos o un apartado sin pagar', tone: 'plain' },
  primera_reserva: { label: 'Primera reserva', hint: 'Tiene cita y aún no viene', tone: 'wait' },
  primera_visita: { label: 'Primera visita', hint: 'Vino una vez', tone: 'wait' },
  recurrente: { label: 'Recurrente', hint: 'Dos visitas o más', tone: 'ok' },
  miembro: { label: 'Miembro', hint: 'Private Club vigente', tone: 'ok' },
  en_riesgo: { label: 'En riesgo', hint: 'Se tardó más de lo normal', tone: 'alert' },
  inactivo: { label: 'Inactivo', hint: 'Mucho tiempo sin volver', tone: 'alert' },
};

export const STAGE_ORDER = Object.keys(STAGES) as FunnelStage[];

export function isStage(value: string | null): value is FunnelStage {
  return Boolean(value && value in STAGES);
}

export function StageBadge({ stage }: { stage: FunnelStage }) {
  const { label, tone } = STAGES[stage];
  return <span className={`statusBadge stage-${tone}`}>{label}</span>;
}
