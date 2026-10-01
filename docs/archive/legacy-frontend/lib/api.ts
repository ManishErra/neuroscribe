const BASE_URL = "http://localhost:8000";

interface ApiOptions extends RequestInit {
  params?: Record<string, string>;
}

export async function apiRequest(path: string, options: ApiOptions = {}) {
  const token = typeof window !== "undefined" ? localStorage.getItem("ns_access_token") : null;

  const headers = new Headers(options.headers || {});
  
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let url = `${BASE_URL}${path}`;
  if (options.params) {
    const searchParams = new URLSearchParams(options.params);
    url += `?${searchParams.toString()}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = "API Request failed";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch (_) {}
    
    // Auto-logout on 401 Unauthorized (except when attempting to login)
    if (response.status === 401 && typeof window !== "undefined" && path !== "/auth/login") {
      localStorage.removeItem("ns_access_token");
      window.location.href = "/login";
    }
    
    throw new Error(errorDetail);
  }

  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}
