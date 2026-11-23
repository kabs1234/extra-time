import { buildQuery, requestJson } from '@/api/client';
import type { Era, LeaderboardRow, Page, Question, Topic } from '@/api/types';

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
