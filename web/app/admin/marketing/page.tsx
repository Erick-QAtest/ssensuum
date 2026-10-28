import type { Metadata } from 'next';
import { MarketingPage } from '../../../features/marketing/MarketingPage';

export const metadata: Metadata = { title: 'Marketing · SSENSUUM' };

export default function AdminMarketingPage() {
  return <MarketingPage />;
}
