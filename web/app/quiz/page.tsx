import type { Metadata } from 'next';
import { TherapistQuiz } from '../../features/quiz/TherapistQuiz';

export const metadata: Metadata = {
  title: '¿Qué terapeuta va contigo? · SSENSUUM',
  description: 'Cinco preguntas para encontrar a tu terapeuta, tu masaje y tu horario en SSENSUUM, Col. Americana.',
  alternates: { canonical: '/quiz' },
};

export default function QuizPage() {
  return <TherapistQuiz />;
}
