/** Where to go after logging in: the `?redirect=` path if it is a local one, otherwise home. */
export function readRedirect(query: unknown): string {
  const isLocalPath = typeof query === 'string' && query.startsWith('/') && !query.startsWith('//');
  return isLocalPath ? query : '/';
}
