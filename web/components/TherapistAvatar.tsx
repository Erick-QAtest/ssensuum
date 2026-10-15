import type { Therapist } from '../lib/types';

// Foto del terapeuta, o su inicial mientras no haya foto.
export function TherapistAvatar({ therapist, className }: { therapist: Therapist; className: string }) {
  if (therapist.photoUrl) {
    return <img className={`${className} hasPhoto`} src={therapist.photoUrl} alt={`${therapist.name}, terapeuta de SSENSUUM`} loading="lazy" />;
  }
  return <span className={className} aria-hidden="true">{therapist.name.slice(0, 1)}</span>;
}
