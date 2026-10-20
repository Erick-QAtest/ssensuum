'use client';

import { useEffect, useState } from 'react';
import { getHrDocuments, hrDownloadUrl } from '../../lib/api';
import type { HrDocument } from '../../lib/types';
import { formatSize } from './hr';

// version cambia cada vez que se sube o borra un documento, para volver a cargar la lista.
export function TemplatesPanel({ version }: { version: number }) {
  const [templates, setTemplates] = useState<HrDocument[] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getHrDocuments('', 'plantilla')
      .then((rows) => { setTemplates(rows); setError(''); })
      .catch((e: Error) => setError(e.message));
  }, [version]);

  return (
    <section className="adminCard" data-testid="hr-templates">
      <h2>Formatos para firmar</h2>
      <p className="muted">
        Descarga, imprime y firma con cada masajista. Después captura el escaneo o foto del documento firmado en su expediente con el botón “Capturar” de la tabla.
      </p>
      {error ? <div className="errorBox" role="alert">{error}</div> : null}
      {templates?.length === 0 ? <p className="muted">Aún no hay formatos. Súbelos en el repositorio con la categoría “Formato para firmar”.</p> : null}
      {templates && templates.length > 0 ? (
        <ul className="hrTemplates">
          {templates.map((template) => (
            <li key={template.id}>
              <div>
                <strong>{template.title}</strong>
                <span className="adminSub">{template.fileName} · {formatSize(template.sizeBytes)}</span>
              </div>
              <a className="secondaryButton hrButtonLink" href={hrDownloadUrl(template.id)} data-testid="hr-template-download">Descargar</a>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
