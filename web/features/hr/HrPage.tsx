'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { getStaff, hrStaffExportUrl, staffRehire } from '../../lib/api';
import { scheduleSummary } from '../../lib/schedule';
import type { HrDocumentCategory, StaffMember } from '../../lib/types';
import { AdminNav } from '../../components/AdminNav';
import { TherapistAvatar } from '../../components/TherapistAvatar';
import { DocumentsPanel } from './DocumentsPanel';
import { HireWizard } from './HireWizard';
import { LeaveFlow } from './LeaveFlow';
import { PayrollPanel } from './PayrollPanel';
import { ScheduleForm } from './ScheduleForm';
import { StaffForm } from './StaffForm';
import { TemplatesPanel } from './TemplatesPanel';
import { UploadPreset, formatDate, formatPhone } from './hr';

// Lo que se abre arriba de la tabla: el alta, la edición de un expediente o la baja.
type Panel = { kind: 'hire' } | { kind: 'edit' | 'leave' | 'schedule'; member: StaffMember } | null;

export function HrPage() {
  const [staff, setStaff] = useState<StaffMember[] | null>(null);
  const [panel, setPanel] = useState<Panel>(null);
  const [filter, setFilter] = useState('');
  const [preset, setPreset] = useState<UploadPreset | null>(null);
  const [version, setVersion] = useState(0);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    return getStaff()
      .then((rows) => { setStaff(rows); setError(''); })
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => { load(); }, [load]);

  function showDocuments(member: StaffMember) {
    setFilter(member.id);
    document.getElementById('documentos')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function open(next: Panel) {
    setPanel(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function rehire(member: StaffMember) {
    if (!window.confirm(`¿Reactivar a ${member.name}? Vuelve a aparecer en el sitio y en las reservas.`)) return;
    staffRehire(member.id).then(() => load()).catch((e: Error) => setError(e.message));
  }

  function capture(member: StaffMember, category: HrDocumentCategory) {
    setFilter(member.id);
    setPreset({ therapistId: member.id, category, key: Date.now() });
    document.getElementById('documentos')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  const complete = staff?.filter((member) => member.active && member.documentationComplete).length ?? 0;
  const active = staff?.filter((member) => member.active).length ?? 0;

  return (
    <main className="bookingShell" data-testid="hr-page">
      <Link href="/" className="backLink">← Volver al sitio</Link>
      <div className="bookingPanel">
        <div className="bookingTitle">
          <span className="kicker">Administración</span>
          <h1>Recursos humanos</h1>
        </div>
        <AdminNav current="equipo" />

        {panel?.kind === 'hire' ? (
          <HireWizard onHired={() => load()} onCapture={capture} onClose={() => setPanel(null)} />
        ) : null}
        {panel?.kind === 'edit' ? (
          <StaffForm
            member={panel.member}
            onSaved={() => { setPanel(null); load(); }}
            onCancel={() => setPanel(null)}
          />
        ) : null}
        {panel?.kind === 'schedule' ? (
          <ScheduleForm member={panel.member} onSaved={() => { setPanel(null); load(); }} onCancel={() => setPanel(null)} />
        ) : null}
        {panel?.kind === 'leave' ? (
          <LeaveFlow member={panel.member} onDone={() => { setPanel(null); load(); }} onCancel={() => setPanel(null)} />
        ) : null}

        <TemplatesPanel version={version} />

        <section className="adminCard">
          <div className="adminRow adminRowSpread">
            <h2>Masajistas</h2>
            <div className="adminRow hrHeadActions">
              <button type="button" className="primaryButton" onClick={() => open({ kind: 'hire' })} data-testid="hr-hire">Dar de alta</button>
              <a className="secondaryButton hrButtonLink" href={hrStaffExportUrl} data-testid="hr-export-staff">Exportar a Excel</a>
            </div>
          </div>

          {error ? <div className="errorBox" role="alert">{error}</div> : null}
          {staff === null && !error ? <p className="muted">Cargando equipo…</p> : null}
          {staff?.length === 0 ? <p className="muted">Aún no hay masajistas registrados.</p> : null}
          {staff && active > 0 ? <p className="muted" data-testid="hr-complete-count">Documentación completa: {complete} de {active} masajistas activos.</p> : null}

          {staff && staff.length > 0 ? (
            <div className="adminTableWrap">
              <table className="adminTable">
                <thead><tr><th>Masajista</th><th>Estado</th><th>Horario</th><th>Documentación</th><th>Teléfono</th><th>Correo</th><th>Ingreso</th><th>Emergencia</th><th>Archivos</th><th></th></tr></thead>
                <tbody>
                  {staff.map((member) => (
                    <tr key={member.id} data-testid="staff-row">
                      <td>
                        <div className="hrPerson">
                          <TherapistAvatar therapist={member} className="hrAvatar" />
                          <div>{member.name}{member.fullName ? <span className="adminSub">{member.fullName}</span> : null}</div>
                        </div>
                      </td>
                      <td>
                        <span className={`statusBadge ${member.active ? 'ok' : 'wait'}`}>{member.active ? 'Activo' : 'Baja'}</span>
                        {!member.active && member.leftOn ? <span className="adminSub">Desde {formatDate(member.leftOn)}{member.leaveReason ? ` · ${member.leaveReason}` : ''}</span> : null}
                      </td>
                      <td className="hrScheduleCell" data-testid="staff-schedule">
                        {!member.active ? '—' : member.schedule === null ? <span className="statusBadge wait">Sin capturar</span> : scheduleSummary(member.schedule) ?? 'Siempre disponible'}
                        <button type="button" className="hrLink" onClick={() => open({ kind: 'schedule', member })}>Editar</button>
                      </td>
                      <td data-testid="staff-documentation">
                        {member.documentationComplete ? <span className="statusBadge ok">Completa</span> : (
                          <>
                            <span className="statusBadge wait">Incompleta</span>
                            {member.missingDocuments.map((missing) => (
                              <span key={missing.category} className="adminSub hrMissing">
                                Falta {missing.label.toLowerCase()} · <button type="button" className="hrLink" onClick={() => capture(member, missing.category)}>Capturar</button>
                              </span>
                            ))}
                          </>
                        )}
                      </td>
                      <td>{member.phone ? formatPhone(member.phone) : '—'}</td>
                      <td>{member.email ?? '—'}</td>
                      <td>{member.hiredOn ? formatDate(member.hiredOn) : '—'}</td>
                      <td>{member.emergencyContact ?? '—'}</td>
                      <td>
                        <button type="button" className="hrLink" onClick={() => showDocuments(member)}>
                          {member.documents === 1 ? '1 archivo' : `${member.documents} archivos`}
                        </button>
                      </td>
                      <td className="recordActions">
                        <button type="button" className="hrLink" onClick={() => open({ kind: 'edit', member })}>Editar expediente</button>
                        {member.active ? (
                          <button type="button" className="hrLink hrLinkDanger" onClick={() => open({ kind: 'leave', member })} data-testid="hr-leave">Dar de baja</button>
                        ) : (
                          <button type="button" className="hrLink" onClick={() => rehire(member)} data-testid="hr-rehire">Reactivar</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>

        <PayrollPanel />

        {staff ? (
          <DocumentsPanel
            staff={staff}
            filter={filter}
            onFilterChange={setFilter}
            preset={preset}
            onChanged={() => { setVersion((value) => value + 1); load(); }}
          />
        ) : null}
      </div>
    </main>
  );
}
