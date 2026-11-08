import { ImageResponse } from 'next/og';

// Ícono para "Agregar a pantalla de inicio" (iOS no usa el favicon SVG).
// Misma S de DM Serif Display que app/icon.svg, a sangre completa: iOS redondea las esquinas.
export const size = { width: 180, height: 180 };
export const contentType = 'image/png';

const S_PATH = 'M237 -18Q182 -18 125.0 -4.5Q68 9 30 31L35 167H45L76 102Q90 74 106.0 52.5Q122 31 150 19Q170 9 188.5 5.5Q207 2 230 2Q291 2 326.5 35.0Q362 68 362 120Q362 169 338.0 196.5Q314 224 261 250L220 268Q134 306 85.5 355.5Q37 405 37 487Q37 546 67.5 589.0Q98 632 152.5 655.0Q207 678 280 678Q333 678 380.5 664.0Q428 650 463 626L457 506H447L406 581Q389 616 372.0 630.5Q355 645 333 651Q320 655 309.0 656.5Q298 658 281 658Q230 658 195.0 628.5Q160 599 160 549Q160 498 187.0 467.5Q214 437 266 413L312 393Q408 351 450.0 303.5Q492 256 492 181Q492 93 425.5 37.5Q359 -18 237 -18Z';

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundImage: 'linear-gradient(135deg, #7a432a, #3e2419)',
        }}
      >
        <svg width="110" height="146" viewBox="30 -18 462 696">
          <path transform="translate(0 660) scale(1 -1)" fill="#f1e4d6" d={S_PATH} />
        </svg>
      </div>
    ),
    size,
  );
}
