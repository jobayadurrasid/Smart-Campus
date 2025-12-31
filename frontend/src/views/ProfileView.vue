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
      <RouterLink v-if="auth.userRole === 'admin'" to="/schedule" class="menu-item">Schedule</RouterLink>
      <RouterLink to="/chatbot" class="menu-item">Chat Assistant</RouterLink>
        <button @click="auth.logout()" class="menu-item logout-item">
          Logout
        </button>
      </div>
    </div>

    <div class="profile-container">
      <div class="profile-card">
        <!-- Demo Notice -->
        

        <div class="profile-header">
          <h2>
            <span class="icon">👤</span>
            My Profile
          </h2>
          <button 
            @click="editMode = !editMode" 
            class="btn-edit"
            v-if="!editMode"
          >
            Edit Profile
          </button>
        </div>

        <!-- View Mode -->
        <div v-if="!editMode" class="profile-view">
          <div class="profile-image-section">
            <img 
              :src="profileImageUrl || '/default-profile.png'" 
              alt="Profile" 
              class="profile-image"
              @error="handleImageError"
            >
          </div>
          <div v-if="loading" class="loading-indicator">
          <div class="spinner"></div>
          Loading...
        </div>
          <div class="profile-details">
            <div class="detail-row">
              <span class="detail-label">Full Name:</span>
              <span class="detail-value">{{ user.full_name || 'Not available' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Email:</span>
              <span class="detail-value">{{ user.email || 'Not available' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Role:</span>
              <span class="detail-value capitalize">{{ user.role || 'Not available' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Department:</span>
              <span class="detail-value">{{ departmentName || 'Not available' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label capitalize">{{auth.userRole}} Since:</span>
              <span class="detail-value">{{ formatDate(user.date_of_enrollment) || 'Not available' }}</span>
            </div>
          </div>
        </div>

        <!-- Edit Mode - Demo Version -->
        <div v-else class="demo-edit-mode">
            <div class="demo-notice">
          <span class="demo-icon">🚧</span>
          This is a demo profile page - functionality is limited
          <span class="demo-icon">🚧</span>
        </div>
          <h3>Edit Profile (Demo)</h3>
          <p>The edit functionality is currently in development.</p>
          <p>This is a demonstration view only.</p>
          
          <div class="demo-edit-form">
            <div class="form-group">
              <label>Profile Image</label>
              <div class="image-preview">
                <img 
                  :src="profileImageUrl || '/default-profile.png'" 
                  class="profile-image"
                >
              </div>
              <button class="btn-secondary" disabled>
                Upload New Image (Disabled in Demo)
              </button>
            </div>

            <div class="form-group">
              <label>Full Name</label>
              <input 
                type="text" 
                class="form-input"
                :value="user.full_name"
                disabled
              >
            </div>

            <div class="form-group">
              <label>Email</label>
              <input 
                type="email" 
                class="form-input"
                :value="user.email"
                disabled
              >
            </div>

            <div class="form-group">
              <label>Department</label>
              <select class="form-input" disabled>
                <option>{{ departmentName || 'Select department' }}</option>
              </select>
            </div>

            <div class="form-actions">
              <button 
                type="button" 
                @click="editMode = false" 
                class="btn-cancel"
              >
                Cancel
              </button>
              <button 
                type="button" 
                class="btn-submit"
                disabled
              >
                Save Changes (Disabled)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { userService, fetchUserProfile } from '@/services/api'
import { RouterLink } from 'vue-router'

// Properly declare all reactive properties
const auth = useAuthStore()
const user = ref({
  full_name: '',
  email: '',
  role: '',
  department_code: '',
  date_of_enrollment: ''
})
const profileImageUrl = ref('')
const editMode = ref(false) // This fixes the error
const loading = ref(false)
const error = ref(null)
const successMessage = ref('')
const departments = ref([])
const loadingDepartments = ref(false)
const isMenuOpen = ref(false)
const menuRef = ref(null)

// Computed properties
const departmentName = computed(() => {
  const dept = departments.value.find(d => d.code === user.value.department_code)
  return dept ? dept.name : 'Not assigned'
})

// Methods
const formatDate = (dateString) => {
  if (!dateString) return ''
  const options = { year: 'numeric', month: 'long', day: 'numeric' }
  return new Date(dateString).toLocaleDateString(undefined, options)
}

const handleImageError = () => {
  profileImageUrl.value = '/default-profile.png'
}

const fetchProfile = async () => {
  try {
    loading.value = true
    const profileData = await fetchUserProfile.getProfile()
    user.value = profileData
    
    try {
      const imageUrl = await fetchUserProfile.getImage()
      profileImageUrl.value = imageUrl
    } catch (imageError) {
      console.warn('Could not load profile image:', imageError)
      profileImageUrl.value = '/default-profile.png'
    }
  } catch (err) {
    console.error('Profile fetch error:', err)
  } finally {
    loading.value = false
  }
}

const fetchDepartments = async () => {
  try {
    loadingDepartments.value = true
    departments.value = await userService.getDepartments()
    console.log(departments.value)
  } catch (err) {
    console.error('Departments fetch error:', err)
  } finally {
    loadingDepartments.value = false
  }
}

const handleClickOutside = (e) => {
  if (isMenuOpen.value && menuRef.value && !menuRef.value.contains(e.target)) {
    isMenuOpen.value = false
  }
}

// Lifecycle hooks
onMounted(async () => {
  await Promise.all([fetchProfile(), fetchDepartments()])
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (profileImageUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(profileImageUrl.value)
  }
})
</script>
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
/* Your existing styles */
.app-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #f8fafc;
  background-image: linear-gradient(to bottom right, #f0f4ff, #ffffff);
  overflow: auto;
  padding: 1rem;
}

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

/* Add demo-specific styles */
.demo-notice {
  background-color: #fffbeb;
  color: #b45309;
  padding: 0.75rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  text-align: center;
  font-weight: 500;
  border: 1px solid #fcd34d;
}

.demo-icon {
  font-size: 1.2rem;
}

.demo-edit-mode {
  padding: 1.5rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
  border: 1px dashed #cbd5e1;
}

.demo-edit-mode h3 {
  color: #4f46e5;
  margin-bottom: 1rem;
}

.demo-edit-mode p {
  color: #64748b;
  margin-bottom: 1.5rem;
}


/* Corner menu (same as before) */
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

/* Profile container */
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding-top: 3rem;
}

.profile-card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  padding: 2rem;
  margin-bottom: 2rem;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.profile-header h2 {
  color: #1e293b;
  font-size: 1.8rem;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.profile-header .icon {
  font-size: 1.5rem;
}

/* Error and success messages */
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

.success-message {
  background: #dcfce7;
  color: #166534;
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
  color: inherit;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 0.5rem;
}

/* Profile view mode */
.profile-view {
  display: flex;
  gap: 2rem;
}

.profile-image-section {
  flex: 0 0 200px;
}

.profile-image {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #e2e8f0;
}

.profile-details {
  flex: 1;
}

.detail-row {
  display: flex;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f1f5f9;
}

.detail-label {
  font-weight: 600;
  color: #334155;
  width: 150px;
}

.detail-value {
  color: #64748b;
  flex: 1;
}

.capitalize {
  text-transform: capitalize;
}

/* Edit mode */
.profile-edit-form {
  display: grid;
  gap: 1.5rem;
}

.image-upload-section {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.current-image {
  flex: 0 0 150px;
}

.upload-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Form elements (same as before) */
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

/* Buttons (same as before with additions) */
.btn-edit {
  background: #4f46e5;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-edit:hover {
  background: #4338ca;
  transform: translateY(-1px);
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
}

.btn-secondary:hover {
  background: #c7d2fe;
  transform: translateY(-1px);
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
}

.btn-delete:hover {
  background: #fecaca;
  transform: translateY(-1px);
}

.btn-submit {
  background: #10b981;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
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

.btn-cancel {
  background: #64748b;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #475569;
  transform: translateY(-1px);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
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
  .profile-view {
    flex-direction: column;
  }
  
  .profile-image-section {
    display: flex;
    justify-content: center;
    flex: 0 0 auto;
    margin-bottom: 1.5rem;
  }
  
  .image-upload-section {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .detail-row {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .detail-label {
    width: 100%;
  }
}
</style>