import axios from 'axios'

const apiClient = axios.create({
  baseURL: '',
})

/**
 * GET /api/info/version
 * Returns version and build information
 */
export async function getVersionInfo() {
  try {
    const response = await apiClient.get('/api/info/version')
    return response.data
  } catch (error) {
    console.error('Failed to fetch version info:', error)
    return null
  }
}

/**
 * GET /api/info/version/simple
 * Returns just the version number
 */
export async function getVersionString() {
  try {
    const response = await apiClient.get('/api/info/version/simple')
    return response.data
  } catch (error) {
    console.error('Failed to fetch version string:', error)
    return 'unknown'
  }
}

/**
 * GET /api/info/health
 * Health check endpoint
 */
export async function healthCheck() {
  try {
    const response = await apiClient.get('/api/info/health')
    return response.data
  } catch (error) {
    console.error('Health check failed:', error)
    return null
  }
}

/**
 * GET /api/info
 * Get complete application information
 */
export async function getAppInfo() {
  try {
    const response = await apiClient.get('/api/info')
    return response.data
  } catch (error) {
    console.error('Failed to fetch app info:', error)
    return null
  }
}

/**
 * GET /api/info/status/detailed
 * Get detailed status information
 */
export async function getDetailedStatus() {
  try {
    const response = await apiClient.get('/api/info/status/detailed')
    return response.data
  } catch (error) {
    console.error('Failed to fetch detailed status:', error)
    return null
  }
}

export default apiClient
