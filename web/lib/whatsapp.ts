export const WHATSAPP_NUMBER = '523310681307';

export function whatsappUrl(message: string) {
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;
}

export const WHATSAPP_MESSAGES = {
  question: 'Hola SSENSUUM, tengo una pregunta.',
  member: 'Hola, soy miembro y quiero reservar.',
  membership: 'Hola, quiero información de la membresía Private Club.',
  help: 'Hola, ¿me ayudan a elegir mi masaje?',
  barber: 'Hola SSENSUUM, quiero reservar en barbería.',
  aesthetics: 'Hola SSENSUUM, quiero agendar una valoración de medicina estética.',
  therapist: (name: string) => `Hola, quiero reservar con ${name}.`,
};
