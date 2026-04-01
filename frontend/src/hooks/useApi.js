import { useState, useCallback } from 'react'

export const useApi = (apiFunction) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const execute = useCallback(async (...args) => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiFunction(...args)
      setData(response.data)
      return response.data
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [apiFunction])

  return { data, loading, error, execute }
}
