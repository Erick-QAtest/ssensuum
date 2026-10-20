'use client';

import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { deleteHrDocument, getHrDocuments, hrDocumentsExportUrl, hrDownloadUrl, uploadHrDocument } from '../../lib/api';
import type { HrDocument, HrDocumentCategory, StaffMember } from '../../lib/types';
import { ACCEPTED_FILES, DOCUMENT_CATEGORIES, MAX_DOCUMENT_BYTES, formatDate, formatSize } from './hr';

type Props = {
  staff: StaffMember[];
  // '' = todos, 'general' = documentos del equipo, o el id de un terapeuta.
  filter: string;
  onFilterChange: (filter: string) => void;
  onChanged: () => void;
};

export function DocumentsPanel({ staff, filter, onFilterChange, onChanged }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [documents, setDocuments] = useState<HrDocument[] | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [owner, setOwner] = useState('');
  const [category, setCategory] = useState<HrDocumentCategory>('contrato');
  const [title, setTitle] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const names = Object.fromEntries(staff.map((member) => [member.id, member.name]));

  const load = useCallback(() => {
    return getHrDocuments(filter)
      .then((rows) => { setDocuments(rows); setError(''); })
      .catch((e: Error) => setError(e.message));
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  // Al filtrar por un terapeuta, lo que se suba queda a su nombre.
  useEffect(() => { setOwner(filter === 'general' ? '' : filter); }, [filter]);

  function chooseFile(next: File | null) {
    setNotice('');
    if (next && next.size > MAX_DOCUMENT_BYTES) {
      setError('El archivo pesa más de 8 MB');
      setFile(null);
      if (input.current) input.current.value = '';
      return;
    }
    setError('');
    setFile(next);
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setError('');
    uploadHrDocument(file, category, owner, title)
      .then((document) => {
        setNotice(`Se subió ${document.fileName}.`);
        setFile(null);
        setTitle('');
        if (input.current) input.current.value = '';
        load();
        onChanged();
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setBusy(false));
  }

  function remove(document: HrDocument) {
    if (!window.confirm(`¿Borrar “${document.title}”? El archivo se elimina del repositorio.`)) return;
    setNotice('');
    deleteHrDocument(document.id)
      .then(() => { load(); onChanged(); })
      .catch((e: Error) => setError(e.message));
  }

  return (
    <section className="adminCard" id="documentos" data-testid="hr-documents">
      <div className="adminRow adminRowSpread">
        <h2>Repositorio de documentos</h2>
        <a className="secondaryButton hrButtonLink" href={hrDocumentsExportUrl} data-testid="hr-export-documents">Descargar todo (ZIP)</a>
      </div>
      <p className="muted">Contratos, identificaciones, certificados y demás archivos del equipo. PDF, imágenes, Word, Excel, CSV o texto, hasta 8 MB.</p>

      <form className="recordForm hrUpload" onSubmit={submit}>
        <div className="recordGrid">
          <label>Archivo
            <input ref={input} type="file" accept={ACCEPTED_FILES} data-testid="hr-file" onChange={(event) => chooseFile(event.target.files?.[0] ?? null)} />
          </label>
          <label>Título (opcional)<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Se usa el nombre del archivo" /></label>
          <label>Pertenece a
            <select value={owner} onChange={(event) => setOwner(event.target.value)}>
              <option value="">Todo el equipo (general)</option>
              {staff.map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}
            </select>
          </label>
          <label>Categoría
            <select value={category} onChange={(event) => setCategory(event.target.value as HrDocumentCategory)}>
              {DOCUMENT_CATEGORIES.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
        </div>
        <div className="adminRow">
          <button type="submit" className="primaryButton" disabled={!file || busy} data-testid="hr-upload">{busy ? 'Subiendo…' : 'Subir documento'}</button>
        </div>
      </form>

      {error ? <div className="errorBox" role="alert">{error}</div> : null}
      {notice ? <div className="successBox" role="status">{notice}</div> : null}

      <div className="adminRow">
        <label className="hrFilter">Mostrar
          <select value={filter} onChange={(event) => onFilterChange(event.target.value)} aria-label="Filtrar documentos">
            <option value="">Todos los documentos</option>
            <option value="general">Solo generales</option>
            {staff.map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}
          </select>
        </label>
      </div>

      {documents === null && !error ? <p className="muted">Cargando documentos…</p> : null}
      {documents?.length === 0 ? <p className="muted">No hay documentos con este filtro.</p> : null}
      {documents && documents.length > 0 ? (
        <div className="adminTableWrap">
          <table className="adminTable">
            <thead><tr><th>Documento</th><th>Pertenece a</th><th>Categoría</th><th>Subido</th><th>Tamaño</th><th></th></tr></thead>
            <tbody>
              {documents.map((document) => (
                <tr key={document.id} data-testid="hr-document-row">
                  <td>{document.title}<span className="adminSub">{document.fileName}</span></td>
                  <td>{document.therapistId ? names[document.therapistId] ?? document.therapistId : 'General'}</td>
                  <td><span className="adminBadge adminBadge-warning">{document.categoryLabel}</span></td>
                  <td>{formatDate(document.uploadedAt)}</td>
                  <td>{formatSize(document.sizeBytes)}</td>
                  <td className="recordActions">
                    <a className="adminAction" href={hrDownloadUrl(document.id)}>Descargar</a>
                    <button type="button" className="linkButton" onClick={() => remove(document)}>Borrar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
