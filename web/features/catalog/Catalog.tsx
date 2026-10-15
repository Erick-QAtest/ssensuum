'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowIcon, CarIcon, ClockIcon, PinIcon, ShieldIcon } from '../../components/icons';
import { getServices, getTherapists, track } from '../../lib/api';
import { money } from '../../lib/format';
import type { Service, Therapist } from '../../lib/types';
import { whatsappUrl } from '../../lib/whatsapp';
import { AESTHETICS, BARBER, MASSAGE } from './categories';
import { ServiceRow } from './ServiceRow';

export function Catalog() {
  const router = useRouter();
  const [services, setServices] = useState<Service[]>([]);
  const [therapists, setTherapists] = useState<Therapist[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([getServices(), getTherapists()])
      .then(([serviceRows, therapistRows]) => {
        setServices(serviceRows);
        setTherapists(therapistRows);
      })
      .catch((e: Error) => setError(e.message));
    track('page_view', 'home');
  }, []);

  const massageServices = useMemo(() => services.filter((service) => service.category === MASSAGE), [services]);
  const barberServices = useMemo(() => services.filter((service) => service.category === BARBER), [services]);
  const aestheticServices = useMemo(() => services.filter((service) => service.category === AESTHETICS), [services]);
  const featuredMassage = massageServices.find((service) => service.id === 'massage-special') ?? massageServices[0];

  // Barbería y medicina estética aún no tienen agenda propia: se coordinan por WhatsApp
  // en lugar de pasar por el selector de terapeutas de masaje.
  const reserve = (service: Service) => {
    if (service.category === MASSAGE) {
      track('reserve_click', service.id);
      router.push(`/reservar?service=${service.id}`);
      return;
    }
    track('whatsapp_click', service.id);
    const intent = service.category === AESTHETICS ? 'agendar una valoración para' : 'reservar';
    window.open(whatsappUrl(`Hola SSENSUUM, quiero ${intent}: ${service.name}.`), '_blank', 'noopener');
  };

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
          <a href="#ubicacion">Cómo llegar</a>
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
            <a className="fusionButton fusionButtonOutline" href={whatsappUrl('Hola SSENSUUM, soy miembro del Private Club y quiero reservar.')} target="_blank" rel="noreferrer" onClick={() => track('whatsapp_click', 'soy-miembro')}>Soy miembro</a>
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
        <strong>PRIVATE MASSAGE CLUB · COL. AMERICANA</strong>
        <span>Todos los días de 9:00 a.m. a 8:30 p.m.</span>
      </div>

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

        {error ? <div className="errorBox">No pudimos cargar la carta. Intenta de nuevo en un momento.</div> : null}

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
        <div className="fusionSectionHeading">
          <div><span className="fusionKicker">También dentro del club</span><h2>Barbería y medicina estética</h2></div>
          <p>Complementa tu visita sin cambiar de lugar. Agenda por WhatsApp y te confirmamos horario.</p>
        </div>
        <div className="fusionSplitService" id="barberia">
          <div className="fusionSplitHeader">
            <div><h2>Barbería</h2><p>Corte, barba y cuidado personal en el mismo lugar donde te das tu masaje.</p></div>
          </div>
          <div className="fusionSplitBody">
            <img src="/ssensuum/barberia-menu.jpg" alt="Menú de barbería SSENSUUM" />
            <div>{barberServices.map((service) => <ServiceRow key={service.id} service={service} compact onReserve={() => reserve(service)} />)}</div>
          </div>
        </div>

        <div className="fusionSplitService" id="estetica">
          <div className="fusionSplitHeader">
            <div><h2>Medicina estética</h2><p>Tratamientos faciales y corporales con valoración previa.</p></div>
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
          <p className="fusionMembershipMath"><strong>Se paga sola:</strong> 5 masajes a precio de miembro ($1,500 de ahorro) más tu masaje de cumpleaños ($1,500) suman los $3,000. Cada visita extra es ahorro.</p>
          <a className="fusionButton fusionButtonLight" href={whatsappUrl('Hola SSENSUUM, quiero información de la membresía Private Club.')} target="_blank" rel="noreferrer" onClick={() => track('whatsapp_click', 'membresia')}>Quiero ser miembro <ArrowIcon /></a>
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
            <div className="fusionLocationFacts">
              <div><PinIcon /><span>Mexicaltzingo 2122-B<br />Col. Americana, Guadalajara.</span></div>
              <div><ClockIcon /><span>Todos los días<br />9:00 a.m. a 8:30 p.m.</span></div>
              <div><CarIcon /><span>Estacionamiento para clientes<br />cajones 1, 2 y 3.</span></div>
            </div>
            <a className="fusionButton" href="https://maps.app.goo.gl/2CLVeFkfyoiGDQqv6" target="_blank" rel="noreferrer">Abrir en Google Maps <ArrowIcon /></a>
          </div>
        </div>
        <iframe
          className="fusionLocationMap"
          title="Mapa de SSENSUUM en Google Maps"
          src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3893.4319101526876!2d-103.3757063182753!3d20.66842565080885!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x8428af00626c2c97%3A0xdda69d37a00f1a1f!2sSSENSUUM!5e1!3m2!1ses-419!2smx!4v1792079897295!5m2!1ses-419!2smx"
          loading="lazy"
          referrerPolicy="strict-origin-when-cross-origin"
          allowFullScreen
        />
      </section>

      <footer className="fusionFooter">
        <img src="/ssensuum/brand-logo.jpg" alt="SSENSUUM Private Massage Club" />
        <div className="fusionFooterLinks"><a href="#masajes">Masajes</a><a href="#barberia">Barbería</a><a href="#estetica">Medicina estética</a><a href="#membresia">Membresía</a><a href="#ubicacion">Cómo llegar</a><a href="/terminos">Términos de reserva</a><a href="/aviso-de-privacidad">Aviso de privacidad</a></div>
        <button type="button" className="fusionButton" disabled={!featuredMassage} onClick={() => featuredMassage && reserve(featuredMassage)}>Reservar</button>
      </footer>
    </main>
  );
}
