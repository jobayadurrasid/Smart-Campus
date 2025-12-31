<template>
  <div class="app-container">
    <!-- Top-left corner menu -->
    <div class="corner-menu" ref="menuRef">
      <button class="menu-btn" @click="isMenuOpen = !isMenuOpen">
        ☰
      </button>
      <div v-if="isMenuOpen" class="menu-dropdown">
        <RouterLink to="/dashboard" class="menu-item">Dashboard</RouterLink>
        <RouterLink to="/courses" class="menu-item">
        {{ auth.userRole === 'admin' ? 'Course Management' : 'Courses' }}
      </RouterLink>
      <RouterLink v-if="auth.userRole === 'admin'" to="/admin/register" class="menu-item">Register</RouterLink>
      <RouterLink v-if="auth.userRole === 'admin'" to="/enrollment" class="menu-item">Enrollment</RouterLink>
      <RouterLink to="/schedule" class="menu-item">Schedule</RouterLink>
        <RouterLink to="/profile" class="menu-item">Profile</RouterLink>
        <button @click="auth.logout()" class="menu-item logout-item">
          Logout
        </button>
      </div>
    </div>

    <div class="chatbot-container">
      <div class="chatbot-card">
        <!-- Chatbot Header -->
        <div class="chat-header">
          <h2>
            <span class="icon">💬</span>
            Smart Campus Assistant
          </h2>
          <span class="role-badge capitalize">{{ role }}</span>
        </div>

        <!-- Messages Area -->
        <div class="messages-container">
          <div class="chat-messages" ref="messagesContainer">
            <div v-for="(msg, index) in messages" :key="index" 
                 :class="['message', msg.sender]">
              <div class="message-content">
                {{ msg.text }}
              </div>
              <div class="message-time">
                {{ formatTime(msg.timestamp) }}
              </div>
            </div>
            <div v-if="isLoading" class="message bot">
              <div class="message-content">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area - Always stays focused -->
        <div class="chat-input-area">
          <form @submit.prevent="sendMessage" class="chat-input-form">
            <input
              v-model="userInput"
              placeholder="Ask about schedules, assignments, or campus info..."
              ref="messageInput"
              :disabled="isLoading"
              autocomplete="off"
              class="chat-input-field"
            />
            <button 
              type="submit"
              :disabled="!userInput || isLoading"
              class="btn-submit"
            >
              <span v-if="!isLoading">Send</span>
              <span v-else class="loading-dots">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
              </span>
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted,nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { RouterLink } from 'vue-router'

const auth = useAuthStore()
const role = ref(auth.userRole)
const messages = ref([
  { 
    text: `Hello ${auth.userRole}! I'm your Smart Campus Assistant. How can I help you today?`, 
    sender: 'bot', 
    timestamp: new Date() 
  }
])
const userInput = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const messageInput = ref(null)
const isMenuOpen = ref(false)
const menuRef = ref(null)

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  // Add user message
  const userMessage = {
    text: userInput.value,
    sender: 'user',
    timestamp: new Date()
  }
  messages.value.push(userMessage)
  const query = userInput.value
  userInput.value = ''
  isLoading.value = true

  scrollToBottom()

  try {
    // Simulate API call with realistic delay
    await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 700))
    
    // Add bot response
    messages.value.push({
      text: generateResponse(query),
      sender: 'bot',
      timestamp: new Date()
    })
  } catch (error) {
    messages.value.push({
      text: "Sorry, I'm having trouble responding right now. Please try again later.",
      sender: 'bot',
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
    // Ensure input stays focused
    nextTick(() => {
      messageInput.value?.focus()
    })
  }
}

const generateResponse = (query) => {
  // Simple response logic - replace with actual API call
  const responses = [
    `I understand you're asking about "${query}". In a real implementation, I would provide a proper response.`,
    `Regarding "${query}", the system would typically provide detailed information here.`,
    `Your question about "${query}" would be processed by our AI system in a real implementation.`,
    `Thanks for your question! A real implementation would analyze "${query}" and provide a helpful response.`
  ]
  return responses[Math.floor(Math.random() * responses.length)]
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatTime = (date) => {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const handleClickOutside = (e) => {
  if (isMenuOpen.value && menuRef.value && !menuRef.value.contains(e.target)) {
    isMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  // Auto-focus input on component mount
  messageInput.value?.focus()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
<style>
/* Root level reset */
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
}
</style>
<style scoped>
/* Base container */
.app-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #f8fafc;
  background-image: linear-gradient(to bottom right, #f0f4ff, #ffffff);
  overflow: hidden;
  padding: 1rem;
}

/* Corner menu styles */
.corner-menu {
  position: fixed;
  top: 1rem;
  left: 1rem;
  z-index: 100;
}

.menu-btn {
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  transition: all 0.2s ease;
}

.menu-btn:hover {
  background: #4338ca;
  transform: scale(1.05);
}

.menu-dropdown {
  position: absolute;
  top: 50px;
  left: 0;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
  min-width: 180px;
  overflow: hidden;
  z-index: 101;
}

.menu-item {
  display: block;
  padding: 0.75rem 1rem;
  color: #1e293b;
  text-decoration: none;
  transition: background 0.2s;
  font-size: 0.9rem;
}

.menu-item:hover {
  background: #f1f5f9;
}

.logout-item {
  color: #ef4444;
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.9rem;
  padding: 0.75rem 1rem;
}

/* Chat container */
.chatbot-container {
  max-width: 800px;
  height: calc(100vh - 2rem);
  margin: 0 auto;
  padding-top: 1rem;
  display: flex;
  flex-direction: column;
}

.chatbot-card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  padding: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Header */
.chat-header {
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.chat-header h2 {
  color: #1e293b;
  font-size: 1.5rem;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.chat-header .icon {
  font-size: 1.5rem;
}

.role-badge {
  background: #e0e7ff;
  color: #4f46e5;
  padding: 0.5rem 1rem;
  border-radius: 1rem;
  font-size: 0.85rem;
  font-weight: 500;
}

/* Messages area */
.messages-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  max-width: 80%;
  animation: fadeIn 0.3s ease;
}

.message-content {
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  line-height: 1.5;
  word-wrap: break-word;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.message-time {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.25rem;
  padding: 0 0.5rem;
}

.message.user {
  align-self: flex-end;
}

.message.user .message-content {
  background: #4f46e5;
  color: white;
  border-bottom-right-radius: 0.25rem;
}

.message.bot {
  align-self: flex-start;
}

.message.bot .message-content {
  background: #f1f5f9;
  color: #1e293b;
  border-bottom-left-radius: 0.25rem;
}

/* Input area - always stays at bottom */
.chat-input-area {
  padding: 1rem 2rem;
  border-top: 1px solid #f1f5f9;
  background: white;
  flex-shrink: 0;
}

.chat-input-form {
  display: flex;
  gap: 0.75rem;
}

.chat-input-field {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: all 0.2s;
}

.chat-input-field:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
}

.btn-submit {
  background: #4f46e5;
  color: white;
  padding: 0 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 80px;
}

.btn-submit:hover:not(:disabled) {
  background: #4338ca;
  transform: translateY(-1px);
}

.btn-submit:disabled {
  background: #c7d2fe;
  cursor: not-allowed;
}

.loading-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 100%;
}

/* Typing indicator */
.typing-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: white;
  animation: typingAnimation 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) {
  animation-delay: 0s;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingAnimation {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-3px); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .chatbot-container {
    padding: 0;
    height: 100vh;
  }
  
  .chatbot-card {
    height: 100%;
    border-radius: 0;
  }
  
  .message {
    max-width: 90%;
  }

  .chat-header,
  .chat-input-area {
    padding: 1rem;
  }

  .chat-messages {
    padding: 1rem;
  }
}

.capitalize {
  text-transform: capitalize;
}
</style>