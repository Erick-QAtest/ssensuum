'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { getStaff, hrStaffExportUrl } from '../../lib/api';
import type { StaffMember } from '../../lib/types';
import { AdminNav } from '../../components/AdminNav';
import { TherapistAvatar } from '../../components/TherapistAvatar';
import { DocumentsPanel } from './DocumentsPanel';
import { PayrollPanel } from './PayrollPanel';
import { StaffForm } from './StaffForm';
import { formatDate, formatPhone } from './hr';

export function HrPage() {
  const [staff, setStaff] = useState<StaffMember[] | null>(null);
  const [editing, setEditing] = useState<StaffMember | null>(null);
  const [filter, setFilter] = useState('');
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

  return (
    <main className="bookingShell" data-testid="hr-page">
      <Link href="/" className="backLink">← Volver al sitio</Link>
      <div className="bookingPanel">
        <div className="bookingTitle">
          <span className="kicker">Administración</span>
          <h1>Recursos humanos</h1>
        </div>
        <AdminNav current="equipo" />

        {editing ? (
          <StaffForm
            member={editing}
            onSaved={() => { setEditing(null); load(); }}
            onCancel={() => setEditing(null)}
          />
        ) : null}

        <section className="adminCard">
          <div className="adminRow adminRowSpread">
            <h2>Masajistas</h2>
            <a className="secondaryButton hrButtonLink" href={hrStaffExportUrl} data-testid="hr-export-staff">Exportar a Excel</a>
          </div>

          {error ? <div className="errorBox" role="alert">{error}</div> : null}
          {staff === null && !error ? <p className="muted">Cargando equipo…</p> : null}
          {staff?.length === 0 ? <p className="muted">Aún no hay masajistas registrados.</p> : null}

          {staff && staff.length > 0 ? (
            <div className="adminTableWrap">
              <table className="adminTable">
                <thead><tr><th>Masajista</th><th>Estado</th><th>Teléfono</th><th>Correo</th><th>Ingreso</th><th>Emergencia</th><th>Documentos</th><th></th></tr></thead>
                <tbody>
                  {staff.map((member) => (
                    <tr key={member.id} data-testid="staff-row">
                      <td>
                        <div className="hrPerson">
                          <TherapistAvatar therapist={member} className="hrAvatar" />
                          <div>{member.name}{member.fullName ? <span className="adminSub">{member.fullName}</span> : null}</div>
                        </div>
                      </td>
                      <td><span className={`statusBadge ${member.active ? 'ok' : 'wait'}`}>{member.active ? 'Activo' : 'Baja'}</span></td>
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
                        <button type="button" className="hrLink" onClick={() => { setEditing(member); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>Editar expediente</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>

        <PayrollPanel />

        {staff ? <DocumentsPanel staff={staff} filter={filter} onFilterChange={setFilter} onChanged={load} /> : null}
      </div>
    </main>
  );
}
