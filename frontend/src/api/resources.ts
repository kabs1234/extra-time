import { buildQuery, requestEmpty, requestJson } from '@/api/client';
import type {
  Attempt,
  AttemptInput,
  Era,
  LeaderboardRow,
  Page,
  Question,
  QuizFilters,
  Topic,
} from '@/api/types';

export async function listEras(): Promise<ReadonlyArray<Era>> {
  const page = await requestJson<Page<Era>>('/eras/');
  return page.results;
}

export async function listTopics(): Promise<ReadonlyArray<Topic>> {
  const page = await requestJson<Page<Topic>>('/topics/');
  return page.results;
}

export function listQuestions(page = 1): Promise<Page<Question>> {
  return requestJson<Page<Question>>(`/questions/${buildQuery({ page })}`);
}

export function getQuestion(id: number): Promise<Question> {
  return requestJson<Question>(`/questions/${id}/`);
}

export function getLeaderboard(): Promise<ReadonlyArray<LeaderboardRow>> {
  return requestJson<ReadonlyArray<LeaderboardRow>>('/leaderboard/');
}

export function startQuiz(filters: QuizFilters): Promise<ReadonlyArray<Question>> {
  return requestJson<ReadonlyArray<Question>>(`/quiz/${buildQuery(filters)}`);
}

export function submitAttempt(input: AttemptInput): Promise<Attempt> {
  return requestJson<Attempt>('/attempts/', { method: 'POST', body: JSON.stringify(input) });
}

export function listAttempts(page = 1): Promise<Page<Attempt>> {
  return requestJson<Page<Attempt>>(`/attempts/${buildQuery({ page })}`);
}

export function getAttempt(id: number): Promise<Attempt> {
  return requestJson<Attempt>(`/attempts/${id}/`);
}

export function deleteAttempt(id: number): Promise<void> {
  return requestEmpty(`/attempts/${id}/`, { method: 'DELETE' });
}
