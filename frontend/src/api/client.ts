import axios from "axios"

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1"

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const message = error.response.data?.message || error.response.data?.detail || "An error occurred"
      return Promise.reject(new Error(message))
    }
    return Promise.reject(error)
  }
)
