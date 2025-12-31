<template>
    <div class="login-container">
      <div class="login-card">
        <h2>Smart Campus Login</h2>
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <input 
              v-model="email" 
              type="email" 
              placeholder="Email" 
              required
              class="form-input"
            >
          </div>
          <div class="form-group">
            <input 
              v-model="password" 
              type="password" 
              placeholder="Password" 
              required
              class="form-input"
            >
          </div>
          <button type="submit" class="btn-submit">Login</button>
          <p v-if="error" class="error-message">{{ error }}</p>
        </form>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref,nextTick } from 'vue'
  import { useRouter } from 'vue-router'
  import { useAuthStore } from '@/stores/auth'
  
  const email = ref('admin@campus.edu')
  const password = ref('secret')
  const error = ref(null)
  const router = useRouter()
  const auth = useAuthStore()
  
  const handleLogin = async () => {
    const success = await auth.login(email.value, password.value)
    if (success) {
      await router.push('/dashboard')
    await nextTick() // waits for DOM to update
    window.dispatchEvent(new Event('resize'))
    } else {
      error.value = "Invalid credentials"
    }
  }
  </script>
  
  <style>
  /* Root level reset */
  html, body, #app {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
  </style>
  
  <style scoped>
  .login-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #f8fafc;
    background-image: linear-gradient(to bottom right, #f0f4ff, #ffffff);
    padding: 1rem;
  }
  
  .login-card {
    background: white;
    padding: 2.5rem;
    border-radius: 1rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
    border: 1px solid #e2e8f0;
  }
  
  h2 {
    color: #1e293b;
    text-align: center;
    margin-bottom: 2rem;
    font-size: 1.5rem;
  }
  
  .form-group {
    margin-bottom: 1.5rem;
  }
  
  .form-input {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    font-size: 1rem;
    transition: all 0.3s ease;
  }
  
  .form-input:focus {
    outline: none;
    border-color: #4f46e5;
    box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
  }
  
  .btn-submit {
    width: 100%;
    background: #4f46e5;
    color: white;
    padding: 0.75rem;
    border: none;
    border-radius: 0.5rem;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .btn-submit:hover {
    background: #4338ca;
    transform: translateY(-1px);
  }
  
  .error-message {
    color: #ef4444;
    text-align: center;
    margin-top: 1rem;
    font-size: 0.9rem;
  }
  
  @media (max-width: 480px) {
    .login-card {
      padding: 1.5rem;
    }
    
    h2 {
      font-size: 1.3rem;
      margin-bottom: 1.5rem;
    }
    
    .form-input {
      padding: 0.65rem 0.9rem;
    }
    
    .btn-submit {
      padding: 0.65rem;
    }
  }
  </style>