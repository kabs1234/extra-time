import { buildQuery, requestEmpty, requestJson } from '@/api/client';
import type {
  AccessToken,
  Attempt,
  AttemptInput,
  Era,
  LeaderboardRow,
  Me,
  MeInput,
  Page,
  Question,
  QuestionInput,
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

export function listMyQuestions(page = 1): Promise<Page<Question>> {
  return requestJson<Page<Question>>(`/questions/${buildQuery({ mine: 'true', page })}`);
}

export function createQuestion(input: QuestionInput): Promise<Question> {
  return requestJson<Question>('/questions/', { method: 'POST', body: JSON.stringify(input) });
}

export function updateQuestion(id: number, input: QuestionInput): Promise<Question> {
  return requestJson<Question>(`/questions/${id}/`, { method: 'PUT', body: JSON.stringify(input) });
}

export function deleteQuestion(id: number): Promise<void> {
  return requestEmpty(`/questions/${id}/`, { method: 'DELETE' });
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

export function getMe(): Promise<Me> {
  return requestJson<Me>('/me/');
}

export function updateMe(input: MeInput): Promise<Me> {
  return requestJson<Me>('/me/', { method: 'PATCH', body: JSON.stringify(input) });
}

export function changePassword(oldPassword: string, newPassword: string): Promise<AccessToken> {
  return requestJson<AccessToken>('/me/password/', {
    method: 'POST',
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  });
}

export function deleteMe(password: string): Promise<void> {
  return requestEmpty('/me/', { method: 'DELETE', body: JSON.stringify({ password }) });
}
