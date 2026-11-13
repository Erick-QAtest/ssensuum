// Datos del responsable que aparecen en el aviso de privacidad y los términos.
export const BUSINESS = {
  commercialName: 'SSENSUUM',
  // Nombre de la persona física o razón social dueña del negocio (como aparece ante el SAT).
  legalName: 'José Alberto Gómez Díaz',
  address: 'Mexicaltzingo 2122-B, Col. Americana, Guadalajara, Jalisco, México',
  privacyEmail: 'sensum.gdl@gmail.com',
  whatsappDisplay: '33 2943 4598',
  // Cambiar por el enlace directo de reseñas de Google Business (g.page/r/…/review) cuando esté.
  reviewUrl: 'https://maps.app.goo.gl/2CLVeFkfyoiGDQqv6',
  lastUpdated: '15 de octubre de 2026',
  // Enlace al video de la experiencia (Instagram, YouTube…). Vacío = no se muestra en el hero.
  experienceVideoUrl: '',
};

// Perfiles oficiales del club, en el orden en que se muestran en el footer.
export const SOCIAL_LINKS = [
  { network: 'Instagram', handle: '@sensum.gdl', url: 'https://www.instagram.com/sensum.gdl/' },
  { network: 'TikTok', handle: '@ssensuum', url: 'https://www.tiktok.com/@ssensuum' },
  { network: 'Facebook', handle: 'SSENSUUM', url: 'https://www.facebook.com/profile.php?id=61595486577087' },
  { network: 'X', handle: '@ssensuum', url: 'https://x.com/ssensuum' },
] as const;
