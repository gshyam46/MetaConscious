/**
 * API Configuration for MetaConscious Frontend
 * Configures the base URL for API calls to FastAPI backend
 */

// Get API base URL from environment variable or default to FastAPI backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

/**
 * Get the full API URL for a given endpoint
 * @param {string} endpoint - The API endpoint (e.g., '/api/goals')
 * @returns {string} - The full URL
 */
export function getApiUrl(endpoint) {
  // Ensure endpoint starts with /
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${API_BASE_URL}${normalizedEndpoint}`;
}

/**
 * Make an API request with proper error handling
 * @param {string} endpoint - The API endpoint
 * @param {RequestInit} options - Fetch options
 * @returns {Promise<Response>} - The fetch response
 */
export async function apiRequest(endpoint, options = {}) {
  const url = getApiUrl(endpoint);
  
  // Set default headers
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };
  
  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };
  
  try {
    const response = await fetch(url, config);
    return response;
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
}

export { API_BASE_URL };