'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { Service, Therapist } from './types';

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
const MASSAGE = 'Masajes';
const BARBER = 'Barbería';
const AESTHETICS = 'Medicina estética';

function money(value: number) {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    maximumFractionDigits: 0,
  }).format(value);
}

function serviceButtonLabel(category: string) {
  return category === AESTHETICS ? 'Agendar valoración' : 'Reservar';
}

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function PinIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 21s6-5.3 6-11a6 6 0 1 0-12 0c0 5.7 6 11 6 11Z" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="10" r="2.2" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="M12 7.5V12l3 2" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function CarIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m5 15 1.5-5h11L19 15M4 15h16v4H4z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <circle cx="7" cy="19" r="1" fill="currentColor" />
      <circle cx="17" cy="19" r="1" fill="currentColor" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3 19 6v5c0 4.7-2.8 8-7 10-4.2-2-7-5.3-7-10V6l7-3Z" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="m8.8 12 2 2 4.4-4.4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ServiceRow({ service, onReserve, compact = false }: { service: Service; onReserve: () => void; compact?: boolean }) {
  return (
    <article className={`fusionServiceRow ${compact ? 'fusionServiceRowCompact' : ''}`} data-testid="service-card">
      <div className="fusionServiceText">
        <div className="fusionServiceTitleLine">
          <h3>{service.name}</h3>
          {service.id === 'massage-special' ? <span className="fusionTag">El más elegido</span> : null}
          {service.therapistsRequired === 2 ? <span className="fusionTag fusionTagSoft">{service.name.toLowerCase().includes('pareja') ? 'Para dos personas' : 'Dos terapeutas'}</span> : null}
        </div>
        {!compact ? <p>{service.description}</p> : null}
        <small>{service.durationMinutes >= 60 ? `${Math.round(service.durationMinutes / 60 * 10) / 10} h` : `${service.durationMinutes} min`}</small>
      </div>
      <div className="fusionServicePurchase">
        <strong>{money(service.publicPrice)}</strong>
        <span>público general</span>
        <small>{money(service.memberPrice)} miembros</small>
        <button type="button" className="fusionButton fusionButtonSmall" onClick={onReserve}>{serviceButtonLabel(service.category)}</button>
      </div>
    </article>
  );
}

export function Catalog() {
  const router = useRouter();
  const [services, setServices] = useState<Service[]>([]);
  const [therapists, setTherapists] = useState<Therapist[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      fetch(`${API}/services`).then((r) => {
        if (!r.ok) throw new Error('No se pudo cargar el catálogo');
        return r.json();
      }),
      fetch(`${API}/therapists`).then((r) => {
        if (!r.ok) throw new Error('No se pudo cargar el equipo');
        return r.json();
      }),
    ])
      .then(([serviceRows, therapistRows]) => {
        setServices(serviceRows);
        setTherapists(therapistRows);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const massageServices = useMemo(() => services.filter((service) => service.category === MASSAGE), [services]);
  const barberServices = useMemo(() => services.filter((service) => service.category === BARBER), [services]);
  const aestheticServices = useMemo(() => services.filter((service) => service.category === AESTHETICS), [services]);
  const featuredMassage = massageServices.find((service) => service.id === 'massage-special') ?? massageServices[0];

  const reserve = (service: Service) => router.push(`/reservar?service=${service.id}`);

  return (
    <main className="fusionPage">
      <nav className="fusionNav" aria-label="Navegación principal">
        <a href="#inicio" className="fusionNavLogo" aria-label="SSENSUUM inicio">
          <img src="/ssensuum/brand-logo.jpg" alt="SSENSUUM Private Massage Club" />
        </a>
        <div className="fusionNavLinks">
          <a href="#masajes">Masajes</a>
          <a href="#barberia">Barbería</a>
          <a href="#estetica">Medicina estética</a>
          <a href="#membresia">Membresía</a>
          <a href="#ubicacion">Nosotros</a>
        </div>
        <button type="button" className="fusionButton fusionNavCta" onClick={() => featuredMassage && reserve(featuredMassage)}>Reservar</button>
      </nav>

      <header className="fusionHero" id="inicio">
        <div className="fusionHeroCopy">
          <img className="fusionHeroLogo" src="/ssensuum/brand-logo.jpg" alt="SSENSUUM Private Massage Club" />
          <p className="fusionEyebrow">PRIVATE MASSAGE CLUB · GUADALAJARA</p>
          <h1>Tu masaje,<br /><em>diseñado por ti.</em></h1>
          <p className="fusionHeroLead">Elige técnica, presión, zonas y terapeuta. Una experiencia privada diseñada alrededor de cómo quieres sentirte al salir.</p>
          <div className="fusionHeroActions">
            <button type="button" className="fusionButton" disabled={!featuredMassage} onClick={() => featuredMassage && reserve(featuredMassage)}>
              Reservar primera visita <ArrowIcon />
            </button>
            <a className="fusionButton fusionButtonOutline" href="#membresia">Soy miembro</a>
          </div>
          <div className="fusionReassurance"><ShieldIcon /><span><strong>$300 para confirmar</strong> · Si la presión o el ambiente no son lo que esperabas, lo ajustamos durante los primeros 10 minutos.</span></div>
          <div className="fusionHeroTrust">
            <span>Terapeuta por nombre</span>
            <span>Espacio privado</span>
            <span>Experiencia personalizada</span>
          </div>
        </div>

        <div className="fusionHeroVisual" aria-label="Masaje especial SSENSUUM">
          <div className="fusionHeroPosterWrap">
            <img src="/ssensuum/massage-special.jpg" alt="Carta de Masaje Especial SSENSUUM" />
          </div>
          <div className="fusionFirstVisitCard">
            <span>PRIMERA VISITA</span>
            <p>Masaje especial</p>
            <strong>{featuredMassage ? money(featuredMassage.publicPrice) : '$1,500'}</strong>
            <small>{featuredMassage ? `${money(featuredMassage.deposit)} de anticipo` : '$300 de anticipo'}</small>
          </div>
        </div>
      </header>

      <div className="fusionIdentityStrip">
        <strong>MASAJES · BARBERÍA · MEDICINA ESTÉTICA</strong>
        <span>Mexicaltzingo 2122-B, Col. Americana, Guadalajara · Todos los días de 9:00 a.m. a 8:30 p.m.</span>
      </div>

      <section className="fusionSection fusionClub" aria-labelledby="club-title">
        <div className="fusionSectionHeading">
          <h2 id="club-title">Así se siente el club</h2>
          <p>La identidad que ya existe: masaje, barbería, estética y una experiencia privada en un mismo lugar.</p>
        </div>
        <div className="fusionExperienceGrid">
          <article className="fusionExperienceCard fusionExperienceBrand">
            <img src="/ssensuum/brand-logo.jpg" alt="SSENSUUM Private Massage Club" />
            <div><span>01</span><strong>Bienvenido a SSENSUUM</strong></div>
          </article>
          <article className="fusionExperienceCard">
            <img src="/ssensuum/massage-special.jpg" alt="Masaje especial SSENSUUM" />
            <div><span>02</span><strong>Masaje hecho a tu medida</strong></div>
          </article>
          <article className="fusionExperienceCard">
            <img src="/ssensuum/barberia-menu.jpg" alt="Barbería SSENSUUM" />
            <div><span>03</span><strong>Barbería dentro del club</strong></div>
          </article>
          <article className="fusionExperienceCard">
            <img src="/ssensuum/estetica-menu.jpg" alt="Medicina estética SSENSUUM" />
            <div><span>04</span><strong>Medicina estética</strong></div>
          </article>
        </div>
      </section>

      <section className="fusionSection fusionCatalogSection" id="masajes" data-testid="catalog">
        <div className="fusionSectionHeading fusionSectionHeadingActions">
          <div>
            <span className="fusionKicker">Carta SSENSUUM</span>
            <h2>Carta de masajes</h2>
          </div>
          <div className="fusionHeadingSide">
            <p>Todas las sesiones duran una hora. Reserva con tres horas de anticipación y confirma con $300, o $600 cuando el servicio ocupa a dos terapeutas.</p>
            <a href="#equipo" className="fusionPillLink">No sé cuál elegir</a>
          </div>
        </div>

        {error ? <div className="errorBox">{error}. Verifica que la API esté corriendo en localhost:8000.</div> : null}

        <div className="fusionMenuLayout">
          <aside className="fusionFeatureCard">
            <img src="/ssensuum/massage-special.jpg" alt="Masaje especial SSENSUUM" />
            {featuredMassage ? (
              <button type="button" className="fusionButton fusionFeatureButton" onClick={() => reserve(featuredMassage)}>Reservar este masaje <ArrowIcon /></button>
            ) : null}
          </aside>
          <div className="fusionServiceList">
            {massageServices.map((service) => <ServiceRow key={service.id} service={service} onReserve={() => reserve(service)} />)}
          </div>
        </div>
      </section>

      <section className="fusionSection fusionSecondaryServices">
        <div className="fusionSplitService" id="barberia">
          <div className="fusionSplitHeader">
            <div><span className="fusionKicker">Dentro del club</span><h2>Barbería</h2><p>Corte, barba y cuidado personal en el mismo lugar donde te das tu masaje.</p></div>
          </div>
          <div className="fusionSplitBody">
            <img src="/ssensuum/barberia-menu.jpg" alt="Menú de barbería SSENSUUM" />
            <div>{barberServices.map((service) => <ServiceRow key={service.id} service={service} compact onReserve={() => reserve(service)} />)}</div>
          </div>
        </div>

        <div className="fusionSplitService" id="estetica">
          <div className="fusionSplitHeader">
            <div><span className="fusionKicker">Valoración profesional</span><h2>Medicina estética</h2><p>Tratamientos faciales y corporales con valoración previa.</p></div>
          </div>
          <div className="fusionSplitBody">
            <img src="/ssensuum/estetica-menu.jpg" alt="Menú de medicina estética SSENSUUM" />
            <div>{aestheticServices.map((service) => <ServiceRow key={service.id} service={service} compact onReserve={() => reserve(service)} />)}</div>
          </div>
        </div>
      </section>

      <section className="fusionSection fusionTeamSection" id="equipo">
        <div className="fusionSectionHeading">
          <div><span className="fusionKicker">Tu terapeuta</span><h2>Sabes quién te va a atender.</h2></div>
          <p>Elige por nombre y fortalezas, o deja la asignación a disponibilidad.</p>
        </div>
        <div className="fusionTherapistGrid">
          {therapists.map((therapist, index) => (
            <article className="fusionTherapistCard" key={therapist.id}>
              <span className="fusionTherapistIndex">0{index + 1}</span>
              <div className="fusionTherapistAvatar">{therapist.name.slice(0, 1)}</div>
              <div><h3>{therapist.name}</h3><p>{therapist.strengths}</p></div>
            </article>
          ))}
        </div>
      </section>

      <section className="fusionMembership" id="membresia">
        <div className="fusionMembershipCopy">
          <span className="fusionKicker fusionKickerLight">PRIVATE CLUB</span>
          <h2>Membresía Private Club</h2>
          <div className="fusionMembershipPrice">$3,000</div>
          <p>al año, para una persona</p>
          <ul>
            <li>Masajes a $1,200 en lugar de $1,500.</li>
            <li>Precio preferente en barbería y medicina estética.</li>
            <li>Un masaje de regalo en la semana de tu cumpleaños.</li>
            <li>Doce meses desde tu fecha de inicio.</li>
          </ul>
          <a className="fusionButton fusionButtonLight" href="tel:+523329434598">Quiero ser miembro <ArrowIcon /></a>
        </div>
        <div className="fusionMembershipVisual"><img src="/ssensuum/membership.jpg" alt="Credencial Membresía Private Club SSENSUUM" /></div>
      </section>

      <section className="fusionSection fusionLocation" id="ubicacion">
        <div className="fusionSectionHeading">
          <div><span className="fusionKicker">Colonia Americana</span><h2>Dónde estamos</h2></div>
          <p>Tenemos tres cajones para clientes frente a la finca, señalados en azul.</p>
        </div>
        <div className="fusionLocationGrid">
          <div className="fusionLocationImage"><img src="/ssensuum/location.jpg" alt="Fachada de SSENSUUM y cajones de estacionamiento" /></div>
          <div className="fusionLocationInfo">
            <h3>Mexicaltzingo 2122-B, Col. Americana</h3>
            <p>Guadalajara, Jalisco. Abrimos todos los días de 9:00 a.m. a 8:30 p.m.</p>
            <div className="fusionLocationFacts">
              <div><PinIcon /><span>Mexicaltzingo 2122-B<br />Col. Americana, Guadalajara.</span></div>
              <div><ClockIcon /><span>Todos los días<br />9:00 a.m. a 8:30 p.m.</span></div>
              <div><CarIcon /><span>Estacionamiento para clientes<br />cajones 1, 2 y 3.</span></div>
            </div>
            <a className="fusionButton" href="https://maps.app.goo.gl/2CLVeFkfyoiGDQqv6" target="_blank" rel="noreferrer">Ver mapa y reseñas <ArrowIcon /></a>
          </div>
        </div>
      </section>

      <footer className="fusionFooter">
        <img src="/ssensuum/brand-logo.jpg" alt="SSENSUUM Private Massage Club" />
        <div className="fusionFooterLinks"><a href="#masajes">Masajes</a><a href="#barberia">Barbería</a><a href="#estetica">Medicina estética</a><a href="#membresia">Membresía</a><a href="#ubicacion">Nosotros</a></div>
        <button type="button" className="fusionButton" disabled={!featuredMassage} onClick={() => featuredMassage && reserve(featuredMassage)}>Reservar</button>
      </footer>
    </main>
  );
}
