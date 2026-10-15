'use client';

import { track } from '../lib/api';
import { whatsappUrl } from '../lib/whatsapp';
import { WhatsAppIcon } from './icons';

export function WhatsAppFloat() {
  return (
    <a
      className="whatsappFloat"
      href={whatsappUrl('Hola SSENSUUM, tengo una pregunta.')}
      target="_blank"
      rel="noreferrer"
      aria-label="Escríbenos por WhatsApp"
      onClick={() => track('whatsapp_click', 'flotante')}
    >
      <WhatsAppIcon />
    </a>
  );
}
