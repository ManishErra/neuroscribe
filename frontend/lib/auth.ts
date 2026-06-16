export interface UserPayload {
  sub: string;
  email: string;
  name?: string;
  exp: number;
}

export function parseJwt(token: string): UserPayload | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    
    let jsonPayload: string;
    if (typeof window !== "undefined") {
      jsonPayload = decodeURIComponent(
        window
          .atob(base64)
          .split('')
          .map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
          })
          .join('')
      );
    } else {
      jsonPayload = Buffer.from(base64, 'base64').toString('utf8');
    }
    
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = parseJwt(token);
  if (!payload) return true;
  const currentTime = Math.floor(Date.now() / 1000);
  return payload.exp < currentTime;
}
