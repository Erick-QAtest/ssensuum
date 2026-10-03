'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { Service, Therapist } from './types';

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

function money(value: number) {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    maximumFractionDigits: 0
  }).format(value);
}

const specialServices = new Set(['massage-special', 'four-hands', 'couples-massage']);

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
      })
    ])
      .then(([serviceRows, therapistRows]) => {
        setServices(serviceRows);
        setTherapists(therapistRows);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const categories = useMemo(
    () => Array.from(new Set(services.map((service) => service.category))),
    [services]
  );

  const featured = services.find((service) => service.id === 'massage-special');

  return (
    <main className="siteShell">
      <div className="announcementBar" aria-label="Información del club">
        <span>Col. Americana · Guadalajara</span>
        <span className="announcementDot" aria-hidden="true" />
        <span>Todos los días · 9:00 a 20:30</span>
        <span className="announcementDot announcementDesktop" aria-hidden="true" />
        <span className="announcementDesktop">3 cajones de estacionamiento</span>
      </div>

      <header className="siteHeader">
        <a className="brand" href="#inicio" aria-label="SSENSUUM inicio">
          <span className="brandMark">S</span>
          <span className="brandText">
            <strong>SSENSUUM</strong>
            <small>PRIVATE MASSAGE CLUB</small>
          </span>
        </a>

        <nav className="desktopNav" aria-label="Navegación principal">
          <a href="#experiencias">Experiencias</a>
          <a href="#metodo">Cómo funciona</a>
          <a href="#equipo">Equipo</a>
          <a href="#ubicacion">Ubicación</a>
        </nav>

        <a className="headerCta" href="#experiencias">Reservar</a>
      </header>

      <section id="inicio" className="hero heroRedesign">
        <div className="heroContent">
          <div className="eyebrow">PRIVATE MASSAGE CLUB · GUADALAJARA</div>
          <h1>Tu masaje.<br /><em>Tus reglas.</em></h1>
          <p className="heroCopy">
            Elige técnicas, presión, zonas y terapeuta. Una experiencia privada diseñada alrededor de cómo quieres sentirte al salir.
          </p>

          <div className="heroActions">
            <a className="primaryCta" href="#experiencias">Elegir mi masaje</a>
            <a className="textCta" href="#metodo">Ver cómo funciona <span aria-hidden="true">↘</span></a>
          </div>

          <div className="heroProof" aria-label="Beneficios de reserva">
            <div><strong>01</strong><span>Elige a tu terapeuta</span></div>
            <div><strong>02</strong><span>Confirma con anticipo</span></div>
            <div><strong>03</strong><span>Ajustamos presión y ambiente</span></div>
          </div>
        </div>

        <div className="heroVisual" aria-label="Experiencia SSENSUUM">
          <div className="heroGlow" />
          <div className="experienceCard experienceCardMain">
            <span className="experienceLabel">PRIMERA VISITA</span>
            <div>
              <p>Masaje especial</p>
              <strong>{featured ? money(featured.publicPrice) : '$1,500'}</strong>
              <small>1 hora · anticipo {featured ? money(featured.deposit) : '$300'}</small>
            </div>
            <span className="experienceArrow">↗</span>
          </div>
          <div className="experienceCard experienceCardFloating">
            <span className="pulseDot" />
            <div><small>Diseñado por ti</small><strong>Técnica · presión · zonas</strong></div>
          </div>
          <div className="heroMonogram" aria-hidden="true">S</div>
        </div>
      </section>

      <section className="trustStrip" aria-label="Razones para elegir SSENSUUM">
        <div><span className="trustIndex">01</span><strong>No es un spa genérico</strong><p>Tu sesión se configura contigo, no desde un menú rígido.</p></div>
        <div><span className="trustIndex">02</span><strong>Sabes quién te atiende</strong><p>Elige terapeuta por nombre y especialidad antes de llegar.</p></div>
        <div><span className="trustIndex">03</span><strong>Reserva con claridad</strong><p>Precio, duración y anticipo visibles antes de confirmar.</p></div>
      </section>

      <section id="experiencias" className="section experiencesSection" data-testid="catalog">
        <div className="sectionHeader sectionHeaderEditorial">
          <div>
            <span className="kicker">LA CARTA</span>
            <h2>Elige la experiencia.<br />Nosotros cuidamos el resto.</h2>
          </div>
          <p>
            Precios transparentes para público y miembros. Cada sesión muestra duración, anticipo y número de terapeutas.
          </p>
        </div>

        {error ? (
          <div className="errorBox">{error}. Verifica que la API esté corriendo en localhost:8000.</div>
        ) : null}

        {categories.map((category) => (
          <div className="category categoryRedesign" key={category}>
            <div className="categoryHeading">
              <h3>{category}</h3>
              <span>{services.filter((service) => service.category === category).length.toString().padStart(2, '0')} experiencias</span>
            </div>

            <div className="grid serviceGrid">
              {services
                .filter((service) => service.category === category)
                .map((service) => (
                  <article
                    className={`card serviceCard ${specialServices.has(service.id) ? 'serviceCardFeatured' : ''}`}
                    key={service.id}
                    data-testid="service-card"
                  >
                    <div className="cardTop">
                      <span className="serviceDuration">{service.durationMinutes} min</span>
                      <div className="serviceBadges">
                        {specialServices.has(service.id) ? <span className="badge badgeSolid">Recomendado</span> : null}
                        {service.therapistsRequired === 2 ? <span className="badge">2 terapeutas</span> : null}
                      </div>
                    </div>

                    <div className="serviceBody">
                      <span className="serviceNumber">{service.id === 'massage-special' ? '01' : '·'}</span>
                      <h4>{service.name}</h4>
                      <p>{service.description}</p>
                    </div>

                    <div className="serviceFooter">
                      <div className="prices pricesRedesign">
                        <div><small>Público</small><strong>{money(service.publicPrice)}</strong></div>
                        <div><small>Miembro</small><strong>{money(service.memberPrice)}</strong></div>
                      </div>
                      <button onClick={() => router.push(`/reservar?service=${service.id}`)}>
                        Reservar <span aria-hidden="true">↗</span>
                      </button>
                    </div>
                  </article>
                ))}
            </div>
          </div>
        ))}
      </section>

      <section id="metodo" className="section methodSection">
        <div className="methodIntro">
          <span className="kicker">SIN FRICCIÓN</span>
          <h2>Tres decisiones.<br />Tu sesión queda lista.</h2>
          <p>No necesitas crear una cuenta para empezar. Primero eliges lo importante; después confirmas tu horario.</p>
        </div>

        <div className="methodSteps">
          <article>
            <span>01</span>
            <div><h3>Elige tu experiencia</h3><p>Masaje, barbería o estética con precio y duración visibles.</p></div>
          </article>
          <article>
            <span>02</span>
            <div><h3>Elige a tu terapeuta</h3><p>Selecciona por nombre y fortalezas, o déjanos elegir por disponibilidad.</p></div>
          </article>
          <article>
            <span>03</span>
            <div><h3>Elige día y hora</h3><p>Solo mostramos horarios realmente disponibles. Confirmas con anticipo.</p></div>
          </article>
        </div>
      </section>

      <section className="guaranteeSection">
        <div className="guaranteeMark" aria-hidden="true">10'</div>
        <div className="guaranteeContent">
          <span className="kicker kickerLight">GARANTÍA DE PRIMERA VISITA</span>
          <h2>Si la presión o el ambiente no se sienten bien, lo ajustamos.</h2>
          <p>
            Durante los primeros diez minutos nos dices qué cambiar. La experiencia debe adaptarse a ti, no al revés.
          </p>
        </div>
        <a className="outlineCta" href="#experiencias">Elegir experiencia</a>
      </section>

      <section id="equipo" className="section teamSection teamRedesign">
        <div className="sectionHeader sectionHeaderEditorial">
          <div>
            <span className="kicker">EL EQUIPO</span>
            <h2>El terapeuta también<br />forma parte de la elección.</h2>
          </div>
          <p>Conoce sus fortalezas antes de reservar. Si no tienes preferencia, el sistema puede asignarte disponibilidad.</p>
        </div>

        <div className="therapistGrid therapistGridRedesign">
          {therapists.map((therapist, index) => (
            <article className="therapistPreview therapistPreviewRedesign" key={therapist.id}>
              <div className="therapistPortrait" aria-hidden="true">
                <span>{therapist.name.slice(0, 1)}</span>
                <small>{String(index + 1).padStart(2, '0')}</small>
              </div>
              <div className="therapistInfo">
                <span className="therapistRole">TERAPEUTA</span>
                <strong>{therapist.name}</strong>
                <p>{therapist.strengths}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section id="ubicacion" className="locationSection">
        <div className="locationPanel">
          <span className="kicker">GUADALAJARA</span>
          <h2>Tu espacio privado<br />en la Americana.</h2>
          <p className="locationAddress">Mexicaltzingo 2122-B · Col. Americana</p>
          <div className="locationMeta">
            <div><small>HORARIO</small><strong>9:00 — 20:30</strong><span>Todos los días</span></div>
            <div><small>ESTACIONAMIENTO</small><strong>3 cajones</strong><span>Señalizados para clientes</span></div>
          </div>
          <a className="primaryCta locationCta" href="#experiencias">Reservar mi sesión</a>
        </div>
        <div className="locationVisual" aria-hidden="true">
          <div className="mapGrid" />
          <div className="mapPin"><span>S</span></div>
          <p>COL. AMERICANA<br />GUADALAJARA</p>
        </div>
      </section>

      <section className="closingSection">
        <span className="kicker">TU PRIMERA VISITA</span>
        <h2>Menos elegir “un masaje”.<br /><em>Más elegir cómo quieres sentirte.</em></h2>
        <a className="closingCta" href="#experiencias">Ver la carta <span aria-hidden="true">↗</span></a>
      </section>

      <footer className="siteFooter">
        <div className="footerBrand">
          <span className="brandMark">S</span>
          <div><strong>SSENSUUM</strong><small>PRIVATE MASSAGE CLUB</small></div>
        </div>
        <p>Mexicaltzingo 2122-B · Col. Americana · Guadalajara, Jal.</p>
        <p>© {new Date().getFullYear()} SSENSUUM</p>
      </footer>
    </main>
  );
}
