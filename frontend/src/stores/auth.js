import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const userRole = ref(localStorage.getItem('userRole') || null)
  const userId = ref(localStorage.getItem('userId') || null)
  const router = useRouter()
  
  const decodeToken = (token) => {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      return JSON.parse(atob(base64))
    } catch (e) {
      console.error("Token decoding failed:", e)
      return null
    }
  }

  const login = async (email, password) => {
    try {
      const response = await axios.post('http://127.0.0.1:8000/token', 
        `username=${email}&password=${password}`,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      )
      
      token.value = response.data.access_token
      const decoded = decodeToken(token.value)
      
      if (decoded) {
        userRole.value = decoded.role
        userId.value = decoded.id
        localStorage.setItem('token', token.value)
        localStorage.setItem('userRole', userRole.value)
        localStorage.setItem('userId',userId.value)
        return true
      }
      
      return false
    } catch (error) {
      console.error("Login failed:", error)
      return false
    }
  }

  const logout = () => {
    token.value = null
    userRole.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    localStorage.removeItem('userId')
    router.push('/login')
  }

  return { 
    token, 
    userRole,
    userId, 
    login, 
    logout,
    decodeToken
  }
})