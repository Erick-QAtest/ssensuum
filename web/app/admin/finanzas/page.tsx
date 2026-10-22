import type { Metadata } from 'next';
import { FinancePage } from '../../../features/finance/FinancePage';

export const metadata: Metadata = { title: 'Finanzas · SSENSUUM' };

export default function AdminFinancePage() {
  return <FinancePage />;
}
