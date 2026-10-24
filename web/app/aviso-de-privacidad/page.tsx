import type { Metadata } from 'next';
import Link from 'next/link';
import { LegalPage } from '../../components/LegalPage';
import { BUSINESS } from '../../lib/business';
import { whatsappUrl } from '../../lib/whatsapp';

export const metadata: Metadata = {
  title: 'Aviso de privacidad · SSENSUUM',
  description: 'Cómo SSENSUUM recaba, usa y protege tus datos personales.',
  alternates: { canonical: '/aviso-de-privacidad' },
};

const responsible = BUSINESS.legalName ? `${BUSINESS.legalName}, con nombre comercial ${BUSINESS.commercialName}` : BUSINESS.commercialName;
const contact = BUSINESS.privacyEmail
  ? <>al correo <a href={`mailto:${BUSINESS.privacyEmail}`}>{BUSINESS.privacyEmail}</a> o por WhatsApp al <a href={whatsappUrl('Hola SSENSUUM, quiero hacer una solicitud sobre mis datos personales.')}>{BUSINESS.whatsappDisplay}</a></>
  : <>por WhatsApp al <a href={whatsappUrl('Hola SSENSUUM, quiero hacer una solicitud sobre mis datos personales.')}>{BUSINESS.whatsappDisplay}</a></>;

export default function PrivacyNoticePage() {
  return (
    <LegalPage title="Aviso de privacidad integral">
      <section>
        <h2>1. Quién es responsable de tus datos</h2>
        <p>
          {responsible}, con domicilio en {BUSINESS.address} (en adelante, “SSENSUUM”), es responsable del tratamiento de tus datos
          personales, conforme a la Ley Federal de Protección de Datos Personales en Posesión de los Particulares y demás normativa aplicable.
        </p>
      </section>

      <section>
        <h2>2. Qué datos recabamos</h2>
        <ul>
          <li><strong>Identificación y contacto:</strong> nombre, apellidos, teléfono (WhatsApp), correo electrónico y fecha de nacimiento.</li>
          <li><strong>Reservas y servicios:</strong> servicios elegidos, fechas y horarios, terapeuta, historial de visitas y tus preferencias para el servicio (por ejemplo, técnica, presión o zonas).</li>
          <li><strong>Pago:</strong> el monto, estado e identificador de tus pagos. Los pagos en línea los procesa Mercado Pago; SSENSUUM no recibe ni guarda los datos de tu tarjeta.</li>
          <li><strong>Membresía:</strong> fecha de inicio y vigencia de tu membresía.</li>
        </ul>
        <p>
          <strong>Datos sensibles.</strong> Para cuidar tu salud podemos preguntarte en el club sobre lesiones, alergias, embarazo,
          padecimientos o tratamientos; en el caso de medicina estética, también tu historial clínico como parte de la valoración.
          Estos datos se consideran sensibles: solo los recabamos en persona, con tu consentimiento expreso y por escrito, y los
          usamos únicamente para prestarte el servicio de forma segura. Por este sitio web no te pedimos datos de salud.
        </p>
      </section>

      <section>
        <h2>3. Para qué usamos tus datos</h2>
        <p>Finalidades necesarias para darte el servicio:</p>
        <ul>
          <li>Agendar, confirmar, reprogramar o cancelar tus reservas y enviarte confirmaciones y recordatorios.</li>
          <li>Cobrar el anticipo y, cuando corresponda, gestionar reembolsos.</li>
          <li>Prestarte el servicio de acuerdo con tus preferencias y cuidar tu seguridad durante la sesión.</li>
          <li>Administrar tu membresía y sus beneficios, incluido el beneficio de cumpleaños.</li>
          <li>Atender tus dudas, quejas y solicitudes, y emitir tus comprobantes fiscales cuando los pidas.</li>
          <li>Cumplir obligaciones legales, fiscales y requerimientos de autoridades.</li>
        </ul>
        <p>Finalidades adicionales, que no son necesarias para el servicio:</p>
        <ul>
          <li>Enviarte promociones, novedades y beneficios del club.</li>
          <li>Pedirte tu opinión sobre la experiencia mediante encuestas de satisfacción.</li>
        </ul>
        <p>
          Si no quieres que usemos tus datos para estas finalidades adicionales, escríbenos {contact} con el mensaje
          “No deseo recibir promociones”. Tu negativa no afecta tus reservas ni los servicios que contratas.
        </p>
      </section>

      <section>
        <h2>4. Con quién compartimos tus datos</h2>
        <p>SSENSUUM no vende ni renta tus datos personales. Solo los compartimos en estos casos:</p>
        <ul>
          <li><strong>Mercado Pago</strong>, para procesar el pago de tu anticipo y, en su caso, su reembolso.</li>
          <li><strong>Proveedores que nos dan servicio</strong>, como el alojamiento del sitio web y del sistema de reservas, que tratan tus datos solo por cuenta de SSENSUUM y bajo nuestras instrucciones.</li>
          <li><strong>WhatsApp</strong>, cuando tú eliges comunicarte con nosotros por ese medio.</li>
          <li><strong>Autoridades competentes</strong>, cuando una ley o un mandato de autoridad lo exija.</li>
        </ul>
        <p>Estas transferencias no requieren tu consentimiento conforme a la ley, por ser necesarias para darte el servicio o para cumplir obligaciones legales.</p>
      </section>

      <section>
        <h2>5. Tus derechos ARCO y cómo revocar tu consentimiento</h2>
        <p>
          Tienes derecho a <strong>acceder</strong> a tus datos, <strong>rectificarlos</strong> si son inexactos, <strong>cancelarlos</strong> cuando
          ya no sean necesarios y <strong>oponerte</strong> a su uso para fines específicos. También puedes revocar el consentimiento que nos
          diste y pedirnos limitar el uso o la divulgación de tus datos.
        </p>
        <p>Para ejercer cualquiera de estos derechos, envía tu solicitud {contact}, con:</p>
        <ul>
          <li>Tu nombre y un medio para responderte.</li>
          <li>Una identificación oficial (o la de tu representante legal y el documento que lo acredite).</li>
          <li>La descripción clara de los datos y del derecho que quieres ejercer.</li>
        </ul>
        <p>
          Te responderemos en un plazo máximo de 20 días hábiles desde que recibamos tu solicitud completa y, si procede, la haremos
          efectiva dentro de los 15 días hábiles siguientes.
        </p>
      </section>

      <section>
        <h2>6. Uso de tecnologías en este sitio</h2>
        <p>
          Este sitio no usa cookies de publicidad ni de rastreo. Para mejorar el sitio contamos de forma anónima las visitas y
          los clics en botones como “Reservar” o “WhatsApp”, sin guardar tu dirección IP ni ningún dato que te identifique. Para mostrar las tipografías usamos Google Fonts, y el botón “Ver mapa”
          abre Google Maps. Al usarlos, Google puede recibir datos técnicos como tu dirección IP, conforme a su política de privacidad.
        </p>
      </section>

      <section>
        <h2>7. Cuánto tiempo conservamos tus datos</h2>
        <p>
          Conservamos tus datos mientras tengas una relación con SSENSUUM y, después, solo durante los plazos que exigen las leyes
          fiscales y demás disposiciones aplicables. Al concluir, los eliminamos de forma segura.
        </p>
      </section>

      <section>
        <h2>8. Cambios a este aviso</h2>
        <p>
          Cualquier cambio a este aviso de privacidad se publicará en esta misma página, <Link href="/aviso-de-privacidad">ssensuum.mx/aviso-de-privacidad</Link>,
          indicando la fecha de última actualización.
        </p>
      </section>

      <section>
        <h2>9. Autoridad</h2>
        <p>
          Si consideras que tu derecho a la protección de datos personales ha sido vulnerado, puedes acudir ante la autoridad
          competente en materia de protección de datos personales.
        </p>
      </section>
    </LegalPage>
  );
}
