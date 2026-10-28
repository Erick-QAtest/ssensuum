'use client';

import { PointerEvent, useEffect, useRef, useState } from 'react';
import { PHOTO_HEIGHT, PHOTO_WIDTH } from './hr';

type Props = {
  // Recibe la foto ya recortada a 4:5 (como el resto del equipo), o null si se quitó.
  onChange: (photo: Blob | null) => void;
  currentUrl?: string;
};

type Frame = { zoom: number; x: number; y: number };
const CENTERED: Frame = { zoom: 1, x: 0.5, y: 0.4 };

export function PhotoCapture({ onChange, currentUrl }: Props) {
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [frame, setFrame] = useState<Frame>(CENTERED);
  const [camera, setCamera] = useState<MediaStream | null>(null);
  const [error, setError] = useState('');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const captureRef = useRef<HTMLInputElement>(null);
  const drag = useRef<{ x: number; y: number; frame: Frame } | null>(null);

  useEffect(() => () => camera?.getTracks().forEach((track) => track.stop()), [camera]);

  useEffect(() => {
    if (camera && videoRef.current) videoRef.current.srcObject = camera;
  }, [camera]);

  // Dibuja el recorte y entrega la foto final cada vez que cambia el encuadre.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!image || !canvas) return;
    const context = canvas.getContext('2d');
    if (!context) return;
    const crop = cropBox(image, frame);
    context.drawImage(image, crop.sx, crop.sy, crop.width, crop.height, 0, 0, PHOTO_WIDTH, PHOTO_HEIGHT);
    canvas.toBlob((blob) => onChange(blob), 'image/jpeg', 0.86);
  }, [image, frame, onChange]);

  function load(file: File | undefined) {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError('Elige una imagen (JPG, PNG o HEIC desde el teléfono).');
      return;
    }
    const url = URL.createObjectURL(file);
    const next = new Image();
    next.onload = () => { setImage(next); setFrame(CENTERED); setError(''); };
    next.onerror = () => setError('No se pudo abrir esa imagen. Prueba con otra o tómala de nuevo.');
    next.src = url;
  }

  async function openCamera() {
    setError('');
    if (!navigator.mediaDevices?.getUserMedia) {
      captureRef.current?.click();
      return;
    }
    try {
      setCamera(await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 1600 }, height: { ideal: 2000 } }, audio: false }));
    } catch {
      // Sin permiso o sin cámara: en el teléfono, el selector de archivos abre la cámara nativa.
      captureRef.current?.click();
    }
  }

  function shoot() {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    const still = document.createElement('canvas');
    still.width = video.videoWidth;
    still.height = video.videoHeight;
    still.getContext('2d')?.drawImage(video, 0, 0);
    camera?.getTracks().forEach((track) => track.stop());
    setCamera(null);
    still.toBlob((blob) => blob && load(new File([blob], 'camara.jpg', { type: 'image/jpeg' })), 'image/jpeg', 0.92);
  }

  function clear() {
    setImage(null);
    onChange(null);
  }

  function startDrag(event: PointerEvent<HTMLCanvasElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    drag.current = { x: event.clientX, y: event.clientY, frame };
  }

  function moveDrag(event: PointerEvent<HTMLCanvasElement>) {
    if (!drag.current || !image) return;
    const box = event.currentTarget.getBoundingClientRect();
    const crop = cropBox(image, drag.current.frame);
    // Arrastrar la foto a la derecha mueve el recorte a la izquierda.
    const dx = ((event.clientX - drag.current.x) / box.width) * crop.width / Math.max(1, image.width - crop.width);
    const dy = ((event.clientY - drag.current.y) / box.height) * crop.height / Math.max(1, image.height - crop.height);
    setFrame({ ...drag.current.frame, x: clamp(drag.current.frame.x - dx), y: clamp(drag.current.frame.y - dy) });
  }

  return (
    <div className="hrPhoto">
      <div className="hrPhotoStage">
        {camera ? (
          <video ref={videoRef} className="hrPhotoMedia hrPhotoMirror" autoPlay playsInline muted data-testid="hr-photo-video" />
        ) : image ? (
          <canvas
            ref={canvasRef}
            className="hrPhotoMedia hrPhotoCanvas"
            width={PHOTO_WIDTH}
            height={PHOTO_HEIGHT}
            onPointerDown={startDrag}
            onPointerMove={moveDrag}
            onPointerUp={() => { drag.current = null; }}
            aria-label="Vista previa de la foto; arrastra para acomodarla"
            data-testid="hr-photo-preview"
          />
        ) : currentUrl ? (
          <img className="hrPhotoMedia" src={currentUrl} alt="Foto actual" />
        ) : (
          <span className="hrPhotoEmpty">Sin foto</span>
        )}
        {camera || image ? <span className="hrPhotoGuide" aria-hidden="true" /> : null}
      </div>

      <div className="hrPhotoSide">
        <ul className="hrPhotoTips">
          <li>Fondo liso y claro, como el resto del equipo.</li>
          <li>De frente, con la cara y los hombros dentro del óvalo.</li>
          <li>Luz pareja, sin sombras ni contraluz.</li>
          <li>Con la camisa del uniforme.</li>
        </ul>

        {camera ? (
          <div className="adminRow">
            <button type="button" className="primaryButton" onClick={shoot} data-testid="hr-photo-shoot">Tomar foto</button>
            <button type="button" className="secondaryButton" onClick={() => setCamera(null)}>Cancelar</button>
          </div>
        ) : (
          <div className="adminRow">
            <button type="button" className="primaryButton" onClick={openCamera}>{image ? 'Tomar otra' : 'Abrir cámara'}</button>
            <button type="button" className="secondaryButton" onClick={() => fileRef.current?.click()}>Subir archivo</button>
            {image ? <button type="button" className="hrLink" onClick={clear}>Quitar</button> : null}
          </div>
        )}

        {image && !camera ? (
          <label className="hrPhotoZoom">
            Acercar
            <input type="range" min={1} max={2.5} step={0.05} value={frame.zoom} onChange={(event) => setFrame({ ...frame, zoom: Number(event.target.value) })} />
          </label>
        ) : null}
        {image && !camera ? <p className="adminSub">Arrastra la foto para centrar la cara.</p> : null}
        {error ? <div className="errorBox" role="alert">{error}</div> : null}

        <input ref={fileRef} type="file" accept="image/*" hidden onChange={(event) => { load(event.target.files?.[0]); event.target.value = ''; }} data-testid="hr-photo-file" />
        <input ref={captureRef} type="file" accept="image/*" capture="user" hidden onChange={(event) => { load(event.target.files?.[0]); event.target.value = ''; }} />
      </div>
    </div>
  );
}

function clamp(value: number) {
  return Math.min(1, Math.max(0, value));
}

// Recorte 4:5 más grande que cabe en la imagen, reducido según el zoom y movido según x/y (0 a 1).
function cropBox(image: HTMLImageElement, frame: Frame) {
  const ratio = PHOTO_WIDTH / PHOTO_HEIGHT;
  let width = image.width;
  let height = width / ratio;
  if (height > image.height) {
    height = image.height;
    width = height * ratio;
  }
  width /= frame.zoom;
  height /= frame.zoom;
  return { sx: (image.width - width) * frame.x, sy: (image.height - height) * frame.y, width, height };
}
