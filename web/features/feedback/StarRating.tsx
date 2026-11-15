import { StarIcon } from '../../components/icons';

const LABELS = ['', 'Muy mal', 'Mal', 'Regular', 'Bien', 'Excelente'];

// Cinco radios con forma de estrella: se usan con mouse, dedo o flechas del teclado.
export function StarRating({ name, label, value, onChange }: { name: string; label: string; value: number; onChange: (value: number) => void }) {
  return (
    <fieldset className="stars">
      <legend>{label}</legend>
      <div className="starsRow">
        {[1, 2, 3, 4, 5].map((star) => (
          <label key={star} className={star <= value ? 'starOn' : ''}>
            <input type="radio" name={name} value={star} checked={value === star} onChange={() => onChange(star)} />
            <StarIcon />
            <span className="srOnly">{star} de 5 · {LABELS[star]}</span>
          </label>
        ))}
        <span className="starsCaption" aria-hidden="true">{LABELS[value]}</span>
      </div>
    </fieldset>
  );
}
