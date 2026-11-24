const API_BASE = '/api';
const AUTH_PATH_PREFIX = '/auth/';
const HTTP_BAD_REQUEST = 400;
const HTTP_UNAUTHORIZED = 401;

export type FieldErrors = Readonly<Record<string, ReadonlyArray<string>>>;
export type QueryParams = Readonly<Record<string, string | number | undefined>>;

export type AuthHooks = {
  readonly getAccessToken: () => string | undefined;
  readonly refreshAccessToken: () => Promise<boolean>;
  readonly onAuthLost: () => void;
};

let authHooks: AuthHooks = {
  getAccessToken: () => undefined,
  refreshAccessToken: async () => false,
  onAuthLost: () => undefined,
};

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly body: unknown,
  ) {
    super(describeFailure(status, body));
  }
}

export function configureAuth(hooks: AuthHooks): void {
  authHooks = hooks;
}

export async function requestJson<TResult>(
  path: string,
  init: RequestInit = {},
): Promise<TResult> {
  const response = await send(path, init);
  return response.json();
}

export async function requestEmpty(
  path: string,
  init: RequestInit = {},
): Promise<void> {
  await send(path, init);
}

export function buildQuery(params: QueryParams = {}): string {
  const entries = Object.entries(params).flatMap(([key, value]) =>
    value === undefined || value === '' ? [] : [[key, String(value)]],
  );
  const query = new URLSearchParams(entries).toString();
  return query ? `?${query}` : '';
}

/**
 * Field errors from a 400 body, one flat list of messages per field. DRF nests errors for
 * nested data (`{"choices": {"2": {"text": [...]}}}`), so nested messages are collected too.
 */
export function getFieldErrors(error: unknown): FieldErrors {
  if (!(error instanceof ApiError) || error.status !== HTTP_BAD_REQUEST || !isRecord(error.body)) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(error.body).map(([field, value]) => [field, [...new Set(collectMessages(value))]]),
  );
}

/** The message to show above a form: `non_field_errors`/`detail`, or anything that isn't a field error. */
export function getFormMessage(error: unknown): string | undefined {
  const fieldErrors = getFieldErrors(error);
  if (fieldErrors.non_field_errors) {
    return fieldErrors.non_field_errors.join(' ');
  }
  return Object.keys(fieldErrors).length > 0 ? undefined : getErrorMessage(error);
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong.';
}

export function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === HTTP_UNAUTHORIZED;
}

/**
 * Sends a request with the in-memory access token. On a 401 from a non-auth endpoint
 * the token has probably expired: refresh once (the refresh cookie travels on its own)
 * and retry. If refreshing fails, the session is over; the request is retried without a
 * token, so public data still loads and only protected requests fail.
 */
async function send(path: string, init: RequestInit): Promise<Response> {
  const response = await fetchWithToken(path, init);
  if (response.status !== HTTP_UNAUTHORIZED || path.startsWith(AUTH_PATH_PREFIX)) {
    return ensureOk(response);
  }
  if (!(await authHooks.refreshAccessToken())) {
    authHooks.onAuthLost();
  }
  return ensureOk(await fetchWithToken(path, init));
}

function fetchWithToken(path: string, init: RequestInit): Promise<Response> {
  const accessToken = authHooks.getAccessToken();
  return fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...init.headers,
    },
  });
}

async function ensureOk(response: Response): Promise<Response> {
  if (!response.ok) {
    throw new ApiError(response.status, await readBody(response));
  }
  return response;
}

async function readBody(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

function collectMessages(value: unknown): ReadonlyArray<string> {
  if (typeof value === 'string') {
    return [value];
  }
  if (Array.isArray(value)) {
    return value.flatMap(collectMessages);
  }
  return isRecord(value) ? Object.values(value).flatMap(collectMessages) : [];
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function describeFailure(status: number, body: unknown): string {
  if (
    typeof body === 'object' &&
    body !== null &&
    'detail' in body &&
    typeof body.detail === 'string'
  ) {
    return body.detail;
  }
  return `The server answered ${status}.`;
}
