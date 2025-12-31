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
      <RouterLink to="/enrollment" class="menu-item">Enrollment</RouterLink>
      <RouterLink  to="/schedule" class="menu-item">Schedule</RouterLink>
      <RouterLink to="/chatbot" class="menu-item">Chat Assistant</RouterLink>
        <RouterLink to="/profile" class="menu-item">Profile</RouterLink>
        <button @click="auth.logout()" class="menu-item logout-item">
          Logout
        </button>
      </div>
    </div>

    <div class="registration-container">
      <div class="registration-card">
        <div class="header-section">
          <h2>
            <span class="icon">👤</span>
            Register New User

          </h2>
        </div>
          <div v-if="loading" class="loading-indicator">
          <div class="spinner"></div>
          Loading...
        </div>
        <!-- Error message -->
        <div v-if="error" class="error-message">
          {{ error }}
          <button @click="error = null" class="error-close">×</button>
        </div>

        <form ref="form" @submit.prevent="handleSubmit" class="registration-form">
          <div class="form-group">
            <label>Email</label>
            <input 
              v-model="form.email" 
              type="email" 
              class="form-input"
              required
              @input="validateForm"
            >
          </div>

          <div class="form-group">
            <label>Full Name</label>
            <input 
              v-model="form.full_name" 
              class="form-input"
              required
              minlength="3"
              @input="validateForm"
            >
          </div>

          <div class="form-group">
            <label>User Role</label>
            <select v-model="form.role" class="form-input" required @change="validateForm">
              <option value="" selected disabled>Select Role</option>
              <option 
                v-for="role in availableRoles" 
                :key="role" 
                :value="role"
              >
                {{ role }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Department</label>
            <select 
              v-model="form.department_code" 
              class="form-input" 
              required
              :disabled="loadingDepartments"
              @change="validateForm"
            >
              <option value="" selected disabled>Select Department</option>
              <option 
                v-for="dept in departments" 
                :key="dept.code" 
                :value="dept.code"
              >
                {{ dept.name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Enrollment Date</label>
            <input 
              v-model="form.date_of_enrollment" 
              type="date" 
              class="form-input"
              :max="maxDate"
              :min="minDate"
              required
              @change="validateForm"
            >
          </div>

          <!-- Profile Image Section -->
          <div class="image-upload-section">
            <h3 class="section-title">Profile Image</h3>
            
            <div class="upload-options">
              <button 
                type="button" 
                class="btn-secondary"
                @click="$refs.fileInput.click()"
              >
                <span class="icon">📁</span> Upload from Device
                <input 
                  ref="fileInput"
                  type="file" 
                  accept="image/*" 
                  hidden 
                  @change="handleFileUpload"
                />
              </button>

              <button 
                type="button" 
                class="btn-secondary"
                @click="toggleCamera"
                :disabled="cameraUnavailable"
              >
                <span class="icon">📷</span> 
                {{ isCameraActive ? 'Stop Camera' : 'Take Photo' }}
              </button>
            </div>

            <!-- Webcam Preview -->
            <div v-if="isCameraActive" class="webcam-section">
              <video 
                ref="video"
                autoplay
                playsinline
                class="webcam-preview"
              ></video>
              <canvas ref="canvas" style="display: none;"></canvas>
              <button 
                v-if="isCameraActive"
                type="button"
                class="btn-primary"
                @click="capturePhoto"
              >
                <span class="icon">⏺️</span> Capture Photo
              </button>
            </div>

            <!-- Image Preview -->
            <div v-if="imagePreview" class="image-preview-section">
              <img :src="imagePreview" alt="Preview" class="preview-image">
              <button 
                type="button"
                class="btn-delete"
                @click="removeImage"
              >
                <span class="icon">🗑️</span> Remove Image
              </button>
            </div>

            <div v-if="imageError" class="error-message">
              {{ imageError }}
            </div>
          </div>

          <button
            type="submit"
            class="btn-submit"
            :disabled="!isFormValid || loading"
          >
            {{ loading ? 'Registering...' : 'Register User' }}
          </button>
        </form>

        <!-- Success Dialog -->
        <div v-if="RegDone" class="modal-overlay">
          <div class="modal-content">
            <h3>{{ succMsg }}</h3>
            <div class="form-actions">
              <button 
                type="button"
                @click="RegDone = false" 
                class="btn-primary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted, onBeforeUnmount, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { userService } from '@/services/api'
import { RouterLink } from 'vue-router'
import * as faceapi from 'face-api.js'

const auth = useAuthStore()
const form = ref({
  email: '',
  full_name: '',
  role: '',
  department_code: '',
  date_of_enrollment: new Date().toISOString().split('T')[0],
  image: null
})
let formData = new FormData()
const isFormValid = ref(false)
const loading = ref(false)
const error = ref(null)
const departments = ref([])
const loadingDepartments = ref(false)
const succMsg = ref(null)
const RegDone = ref(false)
const fileInput = ref(null)
const video = ref(null)
const canvas = ref(null)
const isCameraActive = ref(false)
const imagePreview = ref(null)
const imageError = ref(null)
const stream = ref(null)
const cameraUnavailable = ref(false)
const isMenuOpen = ref(false)

const currentYear = new Date().getFullYear()
const minDate = new Date(2000, 0, 1).toISOString().split('T')[0]
const maxDate = new Date(currentYear, 11, 31).toISOString().split('T')[0]

const availableRoles = computed(() => {
  const baseRoles = ['student', 'teacher']
  return auth.userRole === 'admin' ? [...baseRoles, 'admin'] : baseRoles
})

const validateForm = () => {
  isFormValid.value = (
    form.value.email && 
    form.value.full_name && 
    form.value.role && 
    form.value.department_code && 
    form.value.date_of_enrollment && 
    form.value.image
  )
}

const loadModels = async () => {
  try {
    await faceapi.nets.tinyFaceDetector.loadFromUri('/models')
    console.log("Model loaded successfully")
  } catch (err) {
    console.error("Error loading model:", err)
  }
}

onMounted(async () => {
  try {
    loadingDepartments.value = true
    departments.value = await userService.getDepartments()
    await loadModels()
    try {
      const devices = await navigator.mediaDevices.enumerateDevices()
      cameraUnavailable.value = !devices.some(device => device.kind === 'videoinput')
    } catch (err) {
      cameraUnavailable.value = true
    }
  } catch (err) {
    error.value = 'Failed to load departments'
  } finally {
    loadingDepartments.value = false
  }
  document.addEventListener('click', handleClickOutside)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const menuRef = ref(null)

const handleClickOutside = (e) => {
  if (isMenuOpen.value && menuRef.value && !menuRef.value.contains(e.target)) {
    isMenuOpen.value = false
  }
}
const toggleCamera = async () => {
  if (isCameraActive.value) {
    stopCamera()
  } else {
    removeImage()
    startCamera()
  }
}

const startCamera = async () => {
  try {
    isCameraActive.value = true;
    await nextTick();
    await nextTick();
    await new Promise(resolve => setTimeout(resolve, 50));

    let videoEl = video.value;
    if (!videoEl) {
      videoEl = document.querySelector('.webcam-preview');
      if (!videoEl) {
        videoEl = document.createElement('video');
        videoEl.className = 'webcam-preview';
        videoEl.autoplay = true;
        videoEl.playsinline = true;
        document.querySelector('.webcam-section').appendChild(videoEl);
        video.value = videoEl;
      }
    }

    if (!videoEl.isConnected) {
      throw new Error('Video element exists but not in DOM');
    }

    if (stream.value) {
      stopCamera();
    }

    stream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'user',
        width: { ideal: 1280 },
        height: { ideal: 720 }
      }
    });

    videoEl.srcObject = stream.value;
    await new Promise((resolve, reject) => {
      videoEl.onloadedmetadata = resolve;
      videoEl.onerror = () => reject(new Error('Video stream error'));
      setTimeout(() => reject(new Error('Video loading timeout')), 3000);
    });

    await videoEl.play();

  } catch (err) {
    stopCamera();
    imageError.value = `Camera error: ${err.message}`;
    cameraUnavailable.value = true;
    if (video.value) {
      video.value.style.border = '2px solid red';
    }
  }
};

const stopCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
  }
  isCameraActive.value = false
}

const capturePhoto = async () => {
  const ctx = canvas.value.getContext('2d')
  canvas.value.width = video.value.videoWidth
  canvas.value.height = video.value.videoHeight
  ctx.drawImage(video.value, 0, 0, canvas.value.width, canvas.value.height)

  const detection = await faceapi.detectSingleFace(canvas.value, new faceapi.TinyFaceDetectorOptions())

  if (!detection) {
    imageError.value = 'Image does not contain a face'
    
    setTimeout(() => {
      imageError.value = ''
    }, 2000)
    return
  }
  imageError.value =''
  canvas.value.toBlob(blob => {
    const file = new File([blob], 'profile-photo.jpg', { type: 'image/jpeg' })
    form.value.image = file
    imagePreview.value = URL.createObjectURL(blob)
    validateForm() // Update form validation after capturing photo
    stopCamera()
  }, 'image/jpeg', 0.95)
}

const handleFileUpload = (e) => {
  const file = e.target.files[0]
  if (!file) return

  if (file.size > 2000000) {
    imageError.value = 'Image size should be less than 2MB'
    return
  }

  if (!file.type.match('image.*')) {
    imageError.value = 'Please select an image file'
    return
  }

  const imgURL = URL.createObjectURL(file)
  const img = new Image()
  img.src = imgURL
  img.onload = async () => {
    const detection = await faceapi.detectSingleFace(img, new faceapi.TinyFaceDetectorOptions())
    if (!detection) {
      imageError.value = 'Image does not contain a face'
      setTimeout(() => {
      imageError.value = ''
    }, 2000)
      return
    }

    form.value.image = file
    imagePreview.value = imgURL
    imageError.value = ''
    validateForm() // Update form validation after file upload
  }
}

const removeImage = () => {
  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value)
  }
  form.value.image = null
  imagePreview.value = null
  imageError.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  validateForm() // Update form validation after removing image
}

const handleSubmit = async () => {
  if (!isFormValid.value) {
    error.value = 'Please fill all required fields and upload a profile image'
    return
  }

  loading.value = true
  error.value = null

  try {
    formData.append('email', form.value.email);
    formData.append('full_name', form.value.full_name);
    formData.append('role', form.value.role);
    formData.append('department_code', form.value.department_code);
    formData.append('date_of_enrollment', form.value.date_of_enrollment);
    formData.append('image', form.value.image);
   
    const response = await userService.register(formData)
    if (response.data.status === "success") {
      RegDone.value = true
      succMsg.value = response.data.message
      form.value = {
        email: '',
        full_name: '',
        role: '',
        department_code: '',
        date_of_enrollment: new Date().toISOString().split('T')[0],
        image: null
      }
      removeImage()
      isFormValid.value = false
    } else {
      RegDone.value = true
      succMsg.value = response.data.message
      removeImage()
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Registration failed'
  } finally {
    loading.value = false
    formData = new FormData() // Reset form data
  }
}

onBeforeUnmount(() => {
  stopCamera()
  removeImage()
})
</script>

<!-- Keep the same styles as before -->
<style>
/* Root level reset */
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow: auto;
}
</style>

<style scoped>
/* Base container */
.app-container {
  position: relative;
  height: 100vh;
  width: 100vw;
  background-color: #f8fafc;
  background-image: linear-gradient(to bottom right, #f0f4ff, #ffffff);
  display: flex;
  flex-direction: column;
  overflow: auto;
}


/* Corner menu */
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

/* Registration container */
.registration-container {
  max-width: 800px;
  margin: 0 auto;
  padding-top: 3rem;
}

.registration-card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  padding: 2rem;
  margin-bottom: 2rem;
}

.header-section {
  margin-bottom: 1.5rem;
  text-align: center;
}

.header-section h2 {
  color: #1e293b;
  font-size: 1.8rem;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.header-section .icon {
  font-size: 1.5rem;
}


/* Error message */
.error-message {
  background: #fee2e2;
  color: #b91c1c;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-close {
  background: none;
  border: none;
  color: #b91c1c;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 0.5rem;
}

/* Form styles */
.registration-form {
  display: grid;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: #334155;
  font-weight: 500;
  font-size: 0.95rem;
}

.form-input {
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
}

/* Image upload section */
.image-upload-section {
  margin-top: 1rem;
  padding: 1.5rem;
  border: 1px dashed #cbd5e1;
  border-radius: 0.75rem;
}

.section-title {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #1e293b;
  font-size: 1.2rem;
}

.upload-options {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

/* Webcam styles */
.webcam-section {
  margin-bottom: 1.5rem;
}

.webcam-preview {
  width: 100%;
  max-height: 300px;
  border-radius: 0.5rem;
  background: #e2e8f0;
  margin-bottom: 1rem;
  display: block;
}

/* Image preview */
.image-preview-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Buttons */
.btn-primary {
  background: #4f46e5;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary:hover {
  background: #4338ca;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  background: #a5b4fc;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: #e0e7ff;
  color: #4f46e5;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-secondary:hover {
  background: #c7d2fe;
  transform: translateY(-1px);
}

.btn-secondary:disabled {
  background: #e2e8f0;
  color: #94a3b8;
  cursor: not-allowed;
  transform: none;
}

.btn-delete {
  background: #fee2e2;
  color: #ef4444;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-delete:hover {
  background: #fecaca;
  transform: translateY(-1px);
}

.btn-submit {
  background: #10b981;
  color: white;
  padding: 1rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: 500;
  transition: all 0.2s;
  width: 100%;
  margin-top: 1rem;
}

.btn-submit:hover {
  background: #0d9f6e;
  transform: translateY(-1px);
}

.btn-submit:disabled {
  background: #a7f3d0;
  cursor: not-allowed;
  transform: none;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 0.75rem;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
  text-align: center;
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #1e293b;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}
.loading-indicator {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 6px solid #ccc;
  border-top: 6px solid #3b82f6; /* Tailwind blue-500 */
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

.loading-text {
  font-size: 1.2rem;
  color: #333;
  font-weight: 500;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
/* Responsive adjustments */
@media (max-width: 768px) {
  .registration-container {
    padding: 1rem;
    padding-top: 5rem;
  }
  
  .registration-card {
    padding: 1.5rem;
  }
  
  .upload-options {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .header-section h2 {
    flex-direction: column;
    gap: 0.5rem;
  }
  
}
</style>