import { reactive, readonly } from 'vue';

import { getErrorMessage, isUnauthorized, requestEmpty, requestJson } from '@/api/client';
import type { AccessToken, LoginResponse, Me, SignupInput } from '@/api/types';

type SessionState = {
  user: Me | undefined;
  isReady: boolean;
  /**
   * Why the session couldn't be restored when the cause wasn't a missing or revoked cookie
   * (a server error, the network). The user may well still be logged in, so the app offers a
   * retry instead of treating them as a guest.
   */
  restoreError: string | undefined;
};

const REFRESH_LOCK = 'extra-time-refresh';

const state = reactive<SessionState>({ user: undefined, isReady: false, restoreError: undefined });

/**
 * The access token lives only in this module's memory: never in localStorage, never in a
 * cookie JavaScript can read. A page reload loses it, and initSession gets a new one from
 * the HttpOnly refresh cookie.
 */
let accessToken: string | undefined;
let refreshInFlight: Promise<boolean> | undefined;
let initInFlight: Promise<void> | undefined;

export const session = readonly(state);

export function isLoggedIn(): boolean {
  return state.user !== undefined;
}

export function getAccessToken(): string | undefined {
  return accessToken;
}

export function setAccessToken(token: string): void {
  accessToken = token;
}

export function setCurrentUser(user: Me): void {
  state.user = user;
}

export function initSession(): Promise<void> {
  initInFlight ??= restoreSession();
  return initInFlight;
}

export function retrySessionRestore(): Promise<void> {
  initInFlight = restoreSession();
  return initInFlight;
}

/**
 * Concurrent callers share one refresh: with rotation, a second refresh would reuse a revoked token.
 * Other tabs share the cookie too, so a Web Lock makes tabs take turns; a tab that waited sends the
 * cookie the previous tab just received.
 */
export function refreshAccessToken(): Promise<boolean> {
  refreshInFlight ??= runOneTabAtATime(requestNewAccessToken).finally(() => {
    refreshInFlight = undefined;
  });
  return refreshInFlight;
}

export async function login(username: string, password: string): Promise<void> {
  const response = await requestJson<LoginResponse>('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  accessToken = response.access;
  state.user = response.user;
  state.restoreError = undefined;
}

export async function signup(input: SignupInput): Promise<void> {
  await requestJson('/auth/signup/', { method: 'POST', body: JSON.stringify(input) });
  await login(input.username, input.password);
}

export async function logout(): Promise<void> {
  try {
    await requestEmpty('/auth/logout/', { method: 'POST' });
  } finally {
    clearSession();
  }
}

export function clearSession(): void {
  accessToken = undefined;
  state.user = undefined;
  state.restoreError = undefined;
}

async function restoreSession(): Promise<void> {
  try {
    if (await refreshAccessToken()) {
      state.user = await requestJson<Me>('/me/');
    }
    state.restoreError = undefined;
  } catch (error: unknown) {
    clearSession();
    if (!isUnauthorized(error)) {
      state.restoreError = getErrorMessage(error);
    }
  } finally {
    state.isReady = true;
  }
}

function runOneTabAtATime(task: () => Promise<boolean>): Promise<boolean> {
  return 'locks' in navigator ? navigator.locks.request(REFRESH_LOCK, task) : task();
}

async function requestNewAccessToken(): Promise<boolean> {
  try {
    const response = await requestJson<AccessToken>('/auth/refresh/', { method: 'POST' });
    accessToken = response.access;
    return true;
  } catch (error: unknown) {
    if (isUnauthorized(error)) {
      clearSession();
      return false;
    }
    throw error;
  }
}
