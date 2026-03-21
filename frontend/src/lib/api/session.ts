export async function getAuthHeaders(options?: { headers?: HeadersInit }) {
  const headers = new Headers(options?.headers);
  return headers;
}
