/**
 * Auth Service - Backend-based JWT authentication
 * Uses JWT tokens from our own backend (PostgreSQL)
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Token storage key
const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

// --- TOKEN MANAGEMENT ---

export const getStoredToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

export const setStoredToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const clearStoredToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

export const getStoredUser = (): any | null => {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

export const setStoredUser = (user: any): void => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

// --- AUTH FUNCTIONS ---

/**
 * Register a new user
 */
export const registerWithEmail = async (
  email: string,
  password: string,
  username: string
): Promise<{ success: boolean; message?: string; email?: string }> => {
  try {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, username })
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      return { success: false, message: err.detail || 'Error al registrarse' };
    }

    const data = await response.json();
    setStoredToken(data.access_token);

    return {
      success: true,
      email: email,
      message: 'Registro exitoso. ¡Bienvenido!'
    };
  } catch (error: any) {
    return { success: false, message: 'Error de conexión' };
  }
};

/**
 * Login with email and password
 */
export const loginWithEmail = async (
  email: string,
  password: string
): Promise<{ success: boolean; user?: any; message?: string }> => {
  try {
    // OAuth2 form expects 'username' field for email
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      return { success: false, message: err.detail || 'Credenciales incorrectas' };
    }

    const data = await response.json();
    setStoredToken(data.access_token);

    // Fetch user profile
    const userResponse = await fetch(`${API_URL}/users/me`, {
      headers: { 'Authorization': `Bearer ${data.access_token}` }
    });

    if (userResponse.ok) {
      const user = await userResponse.json();
      setStoredUser(user);
      return { success: true, user };
    }

    return { success: true };
  } catch (error: any) {
    return { success: false, message: 'Error de conexión' };
  }
};

/**
 * Logout - clear local tokens
 */
export const logout = async (): Promise<void> => {
  clearStoredToken();
};

/**
 * Get current user from storage or fetch from API
 */
export const getCurrentUser = async (): Promise<any | null> => {
  const token = getStoredToken();
  if (!token) return null;

  try {
    const response = await fetch(`${API_URL}/users/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      clearStoredToken();
      return null;
    }

    const user = await response.json();
    setStoredUser(user);
    return user;
  } catch {
    return null;
  }
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  return !!getStoredToken();
};

/**
 * Get ID Token for API calls (compatibility wrapper)
 */
export const getIdToken = async (): Promise<string | null> => {
  return getStoredToken();
};

/**
 * Listen to auth state changes (simplified - checks on init)
 */
export const onAuthStateChange = (callback: (user: any | null) => void): (() => void) => {
  // Check auth state immediately
  const checkAuth = async () => {
    const user = await getCurrentUser();
    callback(user);
  };
  
  checkAuth();
  
  // Return unsubscribe function (no-op for localStorage-based auth)
  return () => {};
};

/**
 * Password reset - placeholder (would need backend implementation)
 */
export const sendPasswordResetEmail = async (email: string): Promise<{ success: boolean; message?: string }> => {
  // TODO: Implement password reset endpoint in backend
  return {
    success: false,
    message: 'Función de recuperación de contraseña no implementada aún. Contacta al administrador.'
  };
};
