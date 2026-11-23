import { reactive, readonly } from 'vue';

import { isUnauthorized, requestEmpty, requestJson } from '@/api/client';
import type { AccessToken, LoginResponse, Me, SignupInput } from '@/api/types';

type SessionState = {
  user: Me | undefined;
  isReady: boolean;
};

const state = reactive<SessionState>({ user: undefined, isReady: false });

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

/** Concurrent callers share one refresh: with rotation, a second refresh would reuse a revoked token. */
export function refreshAccessToken(): Promise<boolean> {
  refreshInFlight ??= requestNewAccessToken().finally(() => {
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
}

async function restoreSession(): Promise<void> {
  try {
    if (await refreshAccessToken()) {
      state.user = await requestJson<Me>('/me/');
    }
  } catch (error: unknown) {
    clearSession();
    if (!isUnauthorized(error)) {
      reportSessionError(error);
    }
  } finally {
    state.isReady = true;
  }
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

function reportSessionError(error: unknown): void {
  queueMicrotask(() => {
    throw error;
  });
}
