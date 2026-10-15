import type { Metadata } from 'next';
import Link from 'next/link';
import { LegalPage } from '../../components/LegalPage';
import { BUSINESS } from '../../lib/business';
import { whatsappUrl } from '../../lib/whatsapp';

export const metadata: Metadata = {
  title: 'Términos de reserva y cancelación · SSENSUUM',
  description: 'Anticipo, cancelaciones, cambios de horario y reembolsos en SSENSUUM.',
};

export default function TermsPage() {
  const whatsapp = <a href={whatsappUrl('Hola SSENSUUM, quiero cambiar o cancelar mi reserva.')}>WhatsApp al {BUSINESS.whatsappDisplay}</a>;

  return (
    <LegalPage title="Términos de reserva y cancelación">
      <section>
        <h2>Anticipo</h2>
        <ul>
          <li>Para confirmar tu reserva pagas un anticipo de <strong>$300</strong>, o de <strong>$600</strong> en servicios con dos terapeutas (masaje a 4 manos y masaje de parejas).</li>
          <li>El anticipo aplica para todos los clientes, <strong>incluidos los miembros del Private Club</strong>.</li>
          <li>El anticipo <strong>se descuenta del total</strong> que pagas el día de tu servicio. Si eres miembro, se descuenta de tu precio de miembro.</li>
          <li>Los pagos en línea se procesan con Mercado Pago. Mientras pagas, tu horario queda apartado durante 15 minutos; si el pago no se completa en ese tiempo, el horario se libera.</li>
        </ul>
      </section>

      <section>
        <h2>Cancelaciones y cambios de horario</h2>
        <ul>
          <li>Las reservas se hacen con al menos <strong>3 horas de anticipación</strong>.</li>
          <li>Puedes <strong>cancelar o cambiar tu horario sin costo hasta 3 horas antes</strong> de tu cita. En ese caso eliges entre usar tu anticipo en el nuevo horario o recibir su reembolso.</li>
          <li>Si cancelas con menos de 3 horas de anticipación o no te presentas, <strong>el anticipo no es reembolsable</strong>.</li>
          <li>Para cancelar o cambiar tu horario, escríbenos por {whatsapp}. Contamos el tiempo a partir de la hora de tu mensaje.</li>
        </ul>
      </section>

      <section>
        <h2>Reembolsos</h2>
        <ul>
          <li>Los reembolsos se hacen al mismo medio de pago, a través de Mercado Pago. El tiempo en que se reflejan depende de tu banco o emisor de tarjeta.</li>
          <li>Si SSENSUUM necesita cancelar o mover tu cita, te ofrecemos otro horario o el reembolso total del anticipo, a tu elección.</li>
          <li>Si tu pago se acredita después de que tu horario fue ocupado, te contactamos para darte otro horario o reembolsarte el anticipo completo.</li>
        </ul>
      </section>

      <section>
        <h2>Durante tu visita</h2>
        <ul>
          <li>Si la presión o el ambiente no son lo que esperabas, dínoslo: lo ajustamos durante los primeros 10 minutos de tu sesión.</li>
          <li>Los tratamientos de medicina estética requieren una valoración previa y solo se realizan si el profesional de salud los considera adecuados para ti.</li>
        </ul>
      </section>

      <section>
        <h2>Tus datos</h2>
        <p>Usamos los datos de tu reserva conforme a nuestro <Link href="/aviso-de-privacidad">aviso de privacidad</Link>.</p>
      </section>
    </LegalPage>
  );
}
