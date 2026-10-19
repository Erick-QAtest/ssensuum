import Link from 'next/link';

export function AdminNav({ current }: { current: 'reservas' | 'registro' | 'clientes' }) {
  return (
    <nav className="adminNav" aria-label="Administración">
      <Link href="/admin/reservas" className={current === 'reservas' ? 'active' : ''}>Reservas</Link>
      <Link href="/admin/registro" className={current === 'registro' ? 'active' : ''}>Registro</Link>
      <Link href="/admin/clientes" className={current === 'clientes' ? 'active' : ''}>Clientes</Link>
    </nav>
  );
}
