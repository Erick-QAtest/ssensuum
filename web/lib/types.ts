export type Service = {
  id: string;
  name: string;
  category: string;
  description: string;
  durationMinutes: number;
  publicPrice: number;
  memberPrice: number;
  deposit: number;
  therapistsRequired: number;
};

export type Therapist = {
  id: string;
  name: string;
  strengths: string;
  photoUrl: string;
};
