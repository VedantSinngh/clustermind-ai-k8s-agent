const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const getAuthToken = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("clustermind_token");
  }
  return null;
};

export const setAuthToken = (token: string) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("clustermind_token", token);
  }
};

export const removeAuthToken = () => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("clustermind_token");
  }
};

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    credentials: "include",
    headers,
  });

  if (response.status === 401) {
    removeAuthToken();
    if (typeof window !== "undefined" && window.location.pathname !== "/") {
      window.location.href = "/";
    }
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "An unknown error occurred" }));
    throw new Error(errorData.detail || `HTTP Error ${response.status}`);
  }

  return response.json();
}
