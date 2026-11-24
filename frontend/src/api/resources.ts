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

export function listEras(): Promise<ReadonlyArray<Era>> {
  return listEveryPage<Era>('/eras/');
}

export function listTopics(): Promise<ReadonlyArray<Topic>> {
  return listEveryPage<Topic>('/topics/');
}

export function listQuestions(page = 1): Promise<Page<Question>> {
  return requestJson<Page<Question>>(`/questions/${buildQuery({ page })}`);
}

/** Lists are paginated (20 per page); follow `next` until the last page. */
async function listEveryPage<TItem>(path: string): Promise<ReadonlyArray<TItem>> {
  let pageNumber = 1;
  let page = await requestJson<Page<TItem>>(`${path}${buildQuery({ page: pageNumber })}`);
  let items: ReadonlyArray<TItem> = page.results;
  while (page.next) {
    pageNumber += 1;
    page = await requestJson<Page<TItem>>(`${path}${buildQuery({ page: pageNumber })}`);
    items = [...items, ...page.results];
  }
  return items;
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
