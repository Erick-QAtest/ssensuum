import type { Metadata } from 'next';
import { CustomersPage } from '../../../features/customers/CustomersPage';

export const metadata: Metadata = { title: 'Clientes · SSENSUUM' };

export default function AdminCustomersPage() {
  return <CustomersPage />;
}
