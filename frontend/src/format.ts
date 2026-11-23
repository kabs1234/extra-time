import type { Difficulty, Era } from '@/api/types';

const DIFFICULTY_LABELS: Readonly<Record<Difficulty, string>> = {
  easy: 'Easy',
  medium: 'Medium',
  hard: 'Hard',
};

const DATE_FORMAT = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

export function formatDifficulty(difficulty: Difficulty): string {
  return DIFFICULTY_LABELS[difficulty];
}

export function formatYears(era: Pick<Era, 'start_year' | 'end_year'>): string {
  return `${era.start_year}–${era.end_year}`;
}

export function formatDate(isoDate: string): string {
  return DATE_FORMAT.format(new Date(isoDate));
}

export function readPageNumber(query: unknown): number {
  const page = Number(query);
  return Number.isInteger(page) && page > 0 ? page : 1;
}
