// Pure header builders for the $api plugin, kept apart so they are unit
// testable (the test mock transport cannot assert real request headers).
export interface SsrForwarding {
  cookie?: string
  referer?: string
}

export function readXsrfCookie(cookieString: string): string | null {
  const match = cookieString.match(/(?:^|;\s*)XSRF-TOKEN=([^;]+)/)
  return match?.[1] ? decodeURIComponent(match[1]) : null
}

export function buildApiHeaders(
  base: HeadersInit | undefined,
  xsrf: string | null,
  ssr: SsrForwarding | undefined,
): Headers {
  const headers = new Headers(base)
  if (xsrf) headers.set('X-XSRF-TOKEN', xsrf)
  if (ssr?.cookie) headers.set('cookie', ssr.cookie)
  // Sanctum's stateful check needs a referer/origin from a stateful domain.
  if (ssr?.referer) headers.set('referer', ssr.referer)
  return headers
}
