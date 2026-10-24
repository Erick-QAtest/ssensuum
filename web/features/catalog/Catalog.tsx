'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowDownIcon, ArrowIcon, CarIcon, ClockIcon, CloseIcon, MenuIcon, PauseIcon, PeopleIcon, PinIcon, PlayIcon, WhatsAppIcon } from '../../components/icons';
import { BUSINESS } from '../../lib/business';
import { getServices, getTherapists, track } from '../../lib/api';
import { money } from '../../lib/format';
import type { Service, Therapist } from '../../lib/types';
import { whatsappUrl, WHATSAPP_MESSAGES } from '../../lib/whatsapp';
import { AESTHETICS, BARBER, MASSAGE } from './categories';
import { CartaSection } from './CartaSection';
import { CLUB_RULES, FAQ, SPECIAL_ID, TESTIMONIALS } from './content';
import { ServiceRow } from './ServiceRow';
import { TeamSection } from './TeamSection';

const NAV = [
  { href: '#equipo', label: 'Terapeutas' },
  { href: '#masajes', label: 'Carta' },
  { href: '#membresia', label: 'Membresía' },
  { href: '#ubicacion', label: 'Cómo llegar' },
];
const BOOK_HREF = `/reservar?service=${SPECIAL_ID}`;
const MAPS_URL = 'https://maps.app.goo.gl/2CLVeFkfyoiGDQqv6';

function WhatsAppLink({ message, label, className, children }: { message: string; label: string; className: string; children: React.ReactNode }) {
  return (
    <a className={className} href={whatsappUrl(message)} target="_blank" rel="noreferrer" onClick={() => track('whatsapp_click', label)}>
      {children}
    </a>
  );
}

export function Catalog() {
  const router = useRouter();
  const [services, setServices] = useState<Service[]>([]);
  const [therapists, setTherapists] = useState<Therapist[]>([]);
  const [error, setError] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const [heroCtaVisible, setHeroCtaVisible] = useState(true);
  const heroCtaRef = useRef<HTMLAnchorElement>(null);
  const heroVideoRef = useRef<HTMLVideoElement>(null);
  // null: el video no corre (movimiento reducido o ahorro de datos) y queda el poster.
  const [heroPaused, setHeroPaused] = useState<boolean | null>(null);

  useEffect(() => {
    Promise.all([getServices(), getTherapists()])
      .then(([serviceRows, therapistRows]) => {
        setServices(serviceRows);
        setTherapists(therapistRows);
      })
      .catch(() => setError('No pudimos cargar la carta. Intenta de nuevo en un momento.'));
    track('page_view', 'home');
  }, []);

  // Mientras el botón del hero está en pantalla, la barra fija sobra y taparía contenido.
  useEffect(() => {
    const cta = heroCtaRef.current;
    if (!cta || !('IntersectionObserver' in window)) {
      setHeroCtaVisible(false);
      return;
    }
    const observer = new IntersectionObserver(([entry]) => setHeroCtaVisible(entry.isIntersecting));
    observer.observe(cta);
    return () => observer.disconnect();
  }, []);

  // El video del hero arranca solo si no se pidió movimiento reducido ni ahorro de datos.
  useEffect(() => {
    const video = heroVideoRef.current;
    const saveData = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection?.saveData;
    if (!video || window.matchMedia('(prefers-reduced-motion: reduce)').matches || saveData) return;
    video.play().then(() => setHeroPaused(false), () => setHeroPaused(true));
  }, []);

  const toggleHeroVideo = () => {
    const video = heroVideoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play().then(() => setHeroPaused(false), () => setHeroPaused(true));
    } else {
      video.pause();
      setHeroPaused(true);
    }
  };

  useEffect(() => {
    if (!menuOpen) return;
    const close = (event: KeyboardEvent) => { if (event.key === 'Escape') setMenuOpen(false); };
    window.addEventListener('keydown', close);
    return () => window.removeEventListener('keydown', close);
  }, [menuOpen]);

  const special = services.find((service) => service.id === SPECIAL_ID);
  const massages = useMemo(() => services.filter((service) => service.category === MASSAGE && service.id !== SPECIAL_ID), [services]);
  const barber = useMemo(() => services.filter((service) => service.category === BARBER), [services]);
  const aesthetics = useMemo(() => services.filter((service) => service.category === AESTHETICS), [services]);

  // Barbería y medicina estética se coordinan por WhatsApp.
  const reserveByWhatsapp = (service: Service) => {
    track('whatsapp_click', service.id);
    const intent = service.category === AESTHETICS ? 'agendar una valoración para' : 'reservar';
    window.open(whatsappUrl(`Hola SSENSUUM, quiero ${intent}: ${service.name}.`), '_blank', 'noopener');
  };

  return (
    <main className="club">
      {/* 1. Header */}
      <header className="clubHeader">
        <div className="wrap">
          <div className="clubHeaderRow">
            <a href="#inicio" className="clubLogo" aria-label="SSENSUUM, inicio">
              <img src="/ssensuum/brand-logo.webp" width={450} height={150} alt="SSENSUUM Private Massage Club" />
            </a>
            <nav className="clubNav" aria-label="Secciones">
              {NAV.map((item) => <a key={item.href} href={item.href}>{item.label}</a>)}
            </nav>
            <div className="clubHeaderActions">
              <a className="btn" href={BOOK_HREF} onClick={() => track('reserve_click', 'header')}>Reservar</a>
              <button
                type="button"
                className="clubMenuButton"
                aria-expanded={menuOpen}
                aria-controls="menu-movil"
                aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
                onClick={() => setMenuOpen((open) => !open)}
              >
                {menuOpen ? <CloseIcon /> : <MenuIcon />}
              </button>
            </div>
          </div>
        </div>
        {menuOpen ? (
          <nav className="clubMenu" id="menu-movil" aria-label="Secciones">
            {NAV.map((item) => <a key={item.href} href={item.href} onClick={() => setMenuOpen(false)}>{item.label}</a>)}
          </nav>
        ) : null}
      </header>

      {/* 2. Hero */}
      <section className="hero" id="inicio">
        <div className="wrap heroGrid">
          <div className="heroCopy">
            <p className="heroLabel">Private Massage Club · Guadalajara</p>
            <h1>Tú eliges <em>quién te&nbsp;atiende.</em></h1>
            <p className="heroLead">Masajes privados para hombres. Elige a tu terapeuta y reserva una experiencia a tu medida.</p>
          </div>
          <figure className="heroMedia">
            <video
              ref={heroVideoRef}
              width={960}
              height={1280}
              poster="/ssensuum/hero-cortina-poster.jpg"
              muted
              loop
              playsInline
              preload="none"
              aria-label="Cabina privada de SSENSUUM a media luz, vista tras una cortina"
            >
              <source src="/ssensuum/hero-cortina.webm" type="video/webm" />
              <source src="/ssensuum/hero-cortina.mp4" type="video/mp4" />
            </video>
            {heroPaused !== null ? (
              <button className="heroMediaToggle" type="button" onClick={toggleHeroVideo} aria-label={heroPaused ? 'Reproducir video' : 'Pausar video'}>
                {heroPaused ? <PlayIcon /> : <PauseIcon />}
              </button>
            ) : null}
          </figure>
          <div className="heroActions">
            {BUSINESS.experienceVideoUrl ? (
              <a className="heroVideo" href={BUSINESS.experienceVideoUrl} target="_blank" rel="noreferrer">
                <PlayIcon />
                <span>Conoce la experiencia SSENSUUM</span>
                <small>Video</small>
              </a>
            ) : null}
            <a className="heroCta" ref={heroCtaRef} href="#equipo" onClick={() => track('reserve_click', 'hero')}>
              Elegir terapeuta <ArrowIcon />
            </a>
            <a className="heroScroll" href="#equipo" aria-label="Ver a los terapeutas"><ArrowDownIcon /></a>
            <p className="heroMeta">
              <PeopleIcon />
              {therapists.length ? `${therapists.length} terapeutas · ` : ''}Atención personalizada
            </p>
          </div>
        </div>
      </section>

      {error ? <div className="wrap"><div className="errorBox" role="alert">{error}</div></div> : null}

      {/* 3. Terapeutas */}
      <TeamSection therapists={therapists} />

      {/* 4. Cómo funciona */}
      <section className="section" aria-labelledby="como-title">
        <div className="wrap">
          <div className="sectionHead">
            <p className="label">Cómo funciona</p>
            <h2 id="como-title">Tres pasos y es tu hora.</h2>
          </div>
          <ol className="steps">
            <li><div><strong>Eliges terapeuta y técnica.</strong></div></li>
            <li>
              <div>
                <strong>Apartas con {money(special?.deposit ?? 300)}, que se descuentan de tu total.</strong>
                Reserva con 3 horas de anticipación.
              </div>
            </li>
            <li><div><strong>Llegas, te estacionas en los cajones 1, 2 o 3 frente al club y empieza tu hora.</strong></div></li>
          </ol>
          <p className="stepsNote">Si la presión o el ambiente no son lo que esperabas, lo ajustamos en los primeros 10 minutos.</p>
        </div>
      </section>

      {/* 5. Reglas del club */}
      <section className="section" aria-labelledby="reglas-title">
        <div className="wrap">
          <div className="sectionHead">
            <p className="label">Reglas del club</p>
            <h2 id="reglas-title">Lo que cuida tu experiencia.</h2>
          </div>
          <ul className="rules">
            {CLUB_RULES.map((rule) => (
              <li key={rule.lead}><strong>{rule.lead}</strong>{rule.text ? ` ${rule.text}` : ''}</li>
            ))}
          </ul>
        </div>
      </section>

      {/* 6. Tu primera visita */}
      {special ? (
        <section className="section" aria-labelledby="primera-title">
          <div className="wrap">
            <div className="sectionHead">
              <p className="label">Tu primera visita</p>
              <h2 id="primera-title">Empieza por el favorito.</h2>
            </div>
            <article className="firstVisit" data-testid="service-card">
              <span><span className="tag">El más elegido</span></span>
              <h3>{special.name}</h3>
              <p>Recomendado para tu primera visita. {special.description}</p>
              <p className="priceLine">
                <span className="price">{money(special.publicPrice)}</span>
                <span>1 h · anticipo {money(special.deposit)}</span>
              </p>
              <button type="button" className="btn" onClick={() => { track('reserve_click', SPECIAL_ID); router.push(BOOK_HREF); }}>Reservar</button>
            </article>
          </div>
        </section>
      ) : null}

      {/* 7. Carta completa */}
      <CartaSection services={massages} />

      {/* 8. Testimonios (solo con contenido real) */}
      {TESTIMONIALS.length ? (
        <section className="section" aria-labelledby="testimonios-title">
          <div className="wrap">
            <div className="sectionHead">
              <p className="label">Testimonios</p>
              <h2 id="testimonios-title">Lo que dicen del club.</h2>
            </div>
            <ul className="quotes">
              {TESTIMONIALS.map((item) => (
                <li key={item.author}>
                  <figure><blockquote>{item.quote}</blockquote><figcaption>{item.author}</figcaption></figure>
                </li>
              ))}
            </ul>
          </div>
        </section>
      ) : null}

      {/* 9. Membresía */}
      <section className="section membership" id="membresia" aria-labelledby="membresia-title">
        <div className="wrap">
          <p className="label">Private Club</p>
          <h2 id="membresia-title">Membresía Private Club</h2>
          <p className="membershipPrice">$3,000</p>
          <p>al año, para una persona</p>
          {special ? (
            <p className="membershipHighlight">
              Masajes a {money(special.memberPrice)} en lugar de {money(special.publicPrice)}. Con el masaje de tu cumpleaños, se paga sola en unas 6 visitas.
            </p>
          ) : null}
          <ul>
            <li>Precio preferente en barbería y medicina estética.</li>
            <li>Un masaje de regalo en la semana de tu cumpleaños, sin costo y sin anticipo.</li>
            <li>Doce meses desde tu fecha de inicio.</li>
          </ul>
          <WhatsAppLink className="btn btnLight" message={WHATSAPP_MESSAGES.membership} label="membresia">Quiero ser miembro</WhatsAppLink>
        </div>
      </section>

      {/* 10. Complementa tu visita */}
      <section className="section" aria-labelledby="complementa-title">
        <div className="wrap">
          <div className="sectionHead">
            <p className="label">También en el club</p>
            <h2 id="complementa-title">Complementa tu visita</h2>
          </div>
          <div className="complements">
            <div className="complementGroup" id="barberia">
              <h3>Barbería</h3>
              <ul className="compactList">
                {barber.map((service) => <ServiceRow key={service.id} service={service} onReserve={() => reserveByWhatsapp(service)} />)}
              </ul>
            </div>
            <div className="complementGroup" id="estetica">
              <h3>Medicina estética</h3>
              <p>Con valoración previa.</p>
              <ul className="compactList">
                {aesthetics.map((service) => <ServiceRow key={service.id} service={service} onReserve={() => reserveByWhatsapp(service)} />)}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 11. Cómo llegar */}
      <section className="section" id="ubicacion" aria-labelledby="llegar-title">
        <div className="wrap location">
          <div>
            <div className="sectionHead">
              <p className="label">Col. Americana</p>
              <h2 id="llegar-title">Cómo llegar</h2>
            </div>
            <ul className="facts">
              <li><PinIcon /><span><strong>Mexicaltzingo 2122-B</strong>Col. Americana, Guadalajara</span></li>
              <li><ClockIcon /><span><strong>Todos los días</strong>9:00 a.m. a 8:30 p.m.</span></li>
              <li><CarIcon /><span><strong>Cajones 1, 2 y 3, frente al club</strong>Están señalados en azul. Si los tres están ocupados, avísanos al llegar.</span></li>
            </ul>
            <a className="btn" href={MAPS_URL} target="_blank" rel="noreferrer">Ver mapa</a>
          </div>
          <img src="/ssensuum/location.jpg" alt="Fachada de SSENSUUM y cajones de estacionamiento" loading="lazy" />
        </div>
      </section>

      {/* 12. Preguntas frecuentes (solo con respuestas confirmadas) */}
      {FAQ.length ? (
        <section className="section" aria-labelledby="faq-title">
          <div className="wrap">
            <div className="sectionHead">
              <p className="label">Preguntas frecuentes</p>
              <h2 id="faq-title">Antes de tu visita</h2>
            </div>
            <div className="faq">
              {FAQ.map((item) => (
                <details key={item.question}>
                  <summary>{item.question}</summary>
                  <p>{item.answer}</p>
                </details>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {/* 13. Footer */}
      <footer className="clubFooter">
        <div className="wrap">
          <img src="/ssensuum/brand-logo.webp" width={450} height={150} alt="SSENSUUM Private Massage Club" />
          <ul className="footerLinks">
            {NAV.map((item) => <li key={item.href}><a href={item.href}>{item.label}</a></li>)}
            <li><a href="/terminos">Términos de reserva</a></li>
            <li><a href="/aviso-de-privacidad">Aviso de privacidad</a></li>
          </ul>
          <small>© {new Date().getFullYear()} SSENSUUM · Guadalajara</small>
        </div>
      </footer>

      {/* Barra fija en móvil */}
      <div className={`bottomBar ${heroCtaVisible ? 'bottomBarHidden' : ''}`}>
        <a className="btn" href={BOOK_HREF} onClick={() => track('reserve_click', 'barra')}>Reservar</a>
        <WhatsAppLink className="btn bottomBarWhatsapp" message={WHATSAPP_MESSAGES.question} label="barra">
          <WhatsAppIcon />
          <span className="srOnly">Escríbenos por WhatsApp</span>
        </WhatsAppLink>
      </div>
    </main>
  );
}
