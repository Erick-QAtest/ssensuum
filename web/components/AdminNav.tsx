import Link from 'next/link';

export function AdminNav({ current }: { current: 'reservas' | 'registro' | 'clientes' | 'equipo' | 'finanzas' }) {
  return (
    <nav className="adminNav" aria-label="Administración">
      <Link href="/admin/reservas" className={current === 'reservas' ? 'active' : ''}>Reservas</Link>
      <Link href="/admin/registro" className={current === 'registro' ? 'active' : ''}>Registro</Link>
      <Link href="/admin/clientes" className={current === 'clientes' ? 'active' : ''}>Clientes</Link>
      <Link href="/admin/equipo" className={current === 'equipo' ? 'active' : ''}>Equipo</Link>
      <Link href="/admin/finanzas" className={current === 'finanzas' ? 'active' : ''}>Finanzas</Link>
    </nav>
  );
}
