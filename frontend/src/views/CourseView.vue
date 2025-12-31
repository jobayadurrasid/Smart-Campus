<template>
  <div class="app-container">
    <!-- Top-left corner menu -->
    <div class="corner-menu" ref="menuRef">
      <button class="menu-btn" @click="isMenuOpen = !isMenuOpen">
        ☰
      </button>
      <div v-if="isMenuOpen" class="menu-dropdown">
        <RouterLink to="/dashboard" class="menu-item">Dashboard</RouterLink>
      <RouterLink v-if="auth.userRole === 'admin'" to="/admin/register" class="menu-item">Register</RouterLink>
      <RouterLink v-if="auth.userRole === 'admin'" to="/enrollment" class="menu-item">Enrollment</RouterLink>
      <RouterLink to="/schedule" class="menu-item">Schedule</RouterLink>
      <RouterLink to="/chatbot" class="menu-item">Chat Assistant</RouterLink>
        <RouterLink to="/profile" class="menu-item">Profile</RouterLink>
        <button @click="auth.logout()" class="menu-item logout-item">
          Logout
        </button>
      </div>
    </div>

    <!-- Main content area -->
    <div class="course-management">
      <!-- Error message -->
      <div v-if="error" class="error-message">
        {{ error }}
        <button @click="error = null" class="error-close">×</button>
      </div>
      
      <!-- Header section -->
      <div class="header-section">
        <h2>{{ auth.userRole === 'admin' ? 'Course Management' : 'Courses' }}</h2>
        <div v-if="auth.userRole === 'admin'" class="admin-controls">
          <button @click="showCreateModal = true" class="btn-primary">
            Add New Course
          </button>
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="isLoading" class="loading-skeleton">
        <div v-for="i in 3" :key="i" class="course-skeleton"></div>
      </div>
      
      <!-- Course list -->
      <div class="course-list">
        <div v-for="course in courses" :key="course.id" class="course-card">
          <h3>{{ course.name }}</h3>
          <p>Code: {{ course.id }}</p>
          <p>Department: {{ getDepartmentName(course.department_code) }}</p>
          <p>Semester: {{ formatSemester(course.semester) }}</p>
          <p>Credits: {{ course.credits }}</p>
          <p v-if="course.teacher">Teacher: {{ course.teacher.name }} ({{ course.teacher.id }})</p>
          
          <!-- Admin-only actions -->
          <div v-if="auth.userRole === 'admin'" class="course-actions">
            <button @click="confirmDeleteCourse(course.id)" class="btn-delete">Delete</button>
          </div>
        </div>
      </div>

      <!-- Create Course Modal -->
      <div v-if="showCreateModal" class="modal-overlay">
        <div class="modal-content">
          <h3>Create New Course</h3>
          <form @submit.prevent="handleCreateCourse">
            <div class="form-group">
              <label>Course Name</label>
              <input v-model="newCourse.name" required class="form-input">
            </div>
            
            <div class="form-group">
              <label>Credits</label>
              <input 
                v-model.number="newCourse.credits" 
                type="number" 
                min="1" 
                max="10" 
                required 
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label>Department</label>
              <select 
                v-model="newCourse.department_code" 
                required 
                class="form-input"
                @change="onDepartmentChange"
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
              <label>Semester</label>
              <select v-model="newCourse.semester" required class="form-input">
                <option value="" selected disabled>Select Semester</option>
                <option value="fall">Fall</option>
                <option value="spring">Spring</option>
              </select>
            </div>
            
            <div class="form-group" v-if="newCourse.department_code">
              <label>Teacher</label>
              <div class="teacher-search-container">
                <input
                  v-model="teacherSearchQuery"
                  @input="searchTeachers"
                  @focus="showTeacherSuggestions = true"
                  placeholder="Search teacher by name or ID"
                  class="form-input"
                  :disabled="!newCourse.department_code"
                />
                <div v-if="showTeacherSuggestions && teacherSearchQuery" class="suggestions-dropdown">
                  <div 
                    v-for="teacher in filteredTeachers" 
                    :key="teacher.id"
                    @click="selectTeacher(teacher)"
                    class="suggestion-item"
                  >
                    {{ teacher.name }} (ID: {{ teacher.id }})
                    <span class="teacher-email">{{ teacher.email }}</span>
                  </div>
                  <div v-if="filteredTeachers.length === 0" class="suggestion-item no-results">
                    No teachers found in {{ getDepartmentName(newCourse.department_code) }}
                  </div>
                </div>
              </div>
              <div v-if="newCourse.teacher_id" class="selected-teacher">
                Selected: {{ selectedTeacherName }} (ID: {{ newCourse.teacher_id }})
              </div>
            </div>
            
            <div class="form-actions">
              <button 
                type="submit"
                :disabled="isSubmitting || !isFormValid"
                class="btn-submit"
              >
                {{ isSubmitting ? 'Creating...' : 'Create Course' }}
              </button>
              <button 
                type="button" 
                @click="closeModal"
                class="btn-cancel"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div v-if="showDeleteConfirm" class="modal-overlay">
        <div class="modal-content">
          <h3>Confirm Deletion</h3>
          <p>Are you sure you want to delete this course?</p>
          <div class="form-actions">
            <button @click="deleteCourse(selectedCourseId)" class="btn-delete">Delete</button>
            <button @click="showDeleteConfirm = false" class="btn-cancel">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { courseService, userService } from '@/services/api'
import { debounce } from 'lodash-es'

const auth = useAuthStore()
const courses = ref([])
const departments = ref([])
const isLoading = ref(false)
const loadingDepartments = ref(false)
const error = ref(null)
const showCreateModal = ref(false)
const isSubmitting = ref(false)
const showDeleteConfirm = ref(false)
const selectedCourseId = ref(null)
const isMenuOpen = ref(false)
// Course form data
const newCourse = ref({
  name: '',
  credits: 3,
  department_code: '',
  semester: '',
  teacher_id: ''
})

// Teacher search
const teacherSearchQuery = ref('')
const teacherSuggestions = ref([])
const showTeacherSuggestions = ref(false)
const selectedTeacherName = ref('')

// Computed properties
const filteredTeachers = computed(() => {
  return teacherSuggestions.value.filter(teacher => 
    teacher.department_code === newCourse.value.department_code
  )
})

const isFormValid = computed(() => {
  return (
    newCourse.value.name &&
    newCourse.value.credits > 0 &&
    newCourse.value.department_code &&
    newCourse.value.semester &&
    newCourse.value.teacher_id
  )
})

const menuRef = ref(null)

const handleClickOutside = (e) => {
  if (isMenuOpen.value && menuRef.value && !menuRef.value.contains(e.target)) {
    isMenuOpen.value = false
  }
}

// Methods
const fetchDepartments = async () => {
  try {
    loadingDepartments.value = true
    departments.value = await userService.getDepartments()
  } catch (err) {
    error.value = 'Failed to load departments'
    console.error(err)
  } finally {
    loadingDepartments.value = false
  }
}

const fetchCourses = async () => {
  try {
    isLoading.value = true
    if(auth.userRole=="admin"){
    courses.value = await courseService.getAll()
    }
    else{
      const endpoint = auth.userRole === 'teacher' 
      ? 'getforTeacher' 
      : 'getforStudent'
    courses.value = await courseService[endpoint](auth.userId)
    }
  } catch (err) {
    error.value = 'Failed to load courses'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

const getDepartmentName = (code) => {
  const dept = departments.value.find(d => d.code === code)
  return dept ? dept.name : code
}

const formatSemester = (semester) => {
  return semester === 'fall' ? 'Fall' : 'Spring'
}

const onDepartmentChange = () => {
  // Reset teacher selection when department changes
  newCourse.value.teacher_id = ''
  selectedTeacherName.value = ''
  teacherSearchQuery.value = ''
  teacherSuggestions.value = []
}

const searchTeachers = debounce(async () => {
  // Don't search if query is too short
  if (!teacherSearchQuery.value || teacherSearchQuery.value.trim().length < 1) {
    teacherSuggestions.value = [];
    return;
  }

  if (!newCourse.value.department_code) {
    error.value = "Please select a department first";
    return;
  }

  try {
    const teachers = await userService.searchTeachers(
      newCourse.value.department_code,
      teacherSearchQuery.value.trim()
    );
    teacherSuggestions.value = teachers;
  } catch (err) {
    if (err.response?.status === 422) {
      error.value = "Please enter at least 2 characters to search";
    } else {
      error.value = "Failed to search teachers";
    }
    teacherSuggestions.value = [];
  }
}, 300);

const selectTeacher = (teacher) => {
  newCourse.value.teacher_id = teacher.id
  selectedTeacherName.value = teacher.name
  teacherSearchQuery.value = teacher.name
  showTeacherSuggestions.value = false
}

const handleCreateCourse = async () => {
  try {
    isSubmitting.value = true
    const createdCourse = await courseService.create(newCourse.value)
    courses.value.push(createdCourse)
    closeModal()
  } catch (err) {
    error.value = 'Failed to create course: ' + (err.response?.data?.message || err.message)
    console.error(err)
  } finally {
    isSubmitting.value = false
  }
}

const confirmDeleteCourse = (courseId) => {
  selectedCourseId.value = courseId
  showDeleteConfirm.value = true
}

const deleteCourse = async (courseId) => {
  try {
    await courseService.delete(courseId)
    courses.value = courses.value.filter(c => c.id !== courseId)
    showDeleteConfirm.value = false
  } catch (err) {
    error.value = 'Failed to delete course'
    console.error(err)
  }
}

const closeModal = () => {
  showCreateModal.value = false
  resetForm()
}

const resetForm = () => {
  newCourse.value = {
    name: '',
    credits: 3,
    department_code: '',
    semester: '',
    teacher_id: ''
  }
  teacherSearchQuery.value = ''
  selectedTeacherName.value = ''
  teacherSuggestions.value = []
  error.value = null
}

// Lifecycle hooks
onMounted(() => {
  fetchDepartments()
  fetchCourses()
  document.addEventListener('click', handleClickOutside)
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

/* Centered course management */
.course-management {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 3rem 1rem 1rem;
  flex: 1;
  box-sizing: border-box;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

h2 {
  color: #1e293b;
  font-size: 1.8rem;
  margin: 0;
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

/* Loading skeleton */
.loading-skeleton {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  padding-bottom: 1rem;
}

.course-skeleton {
  background: #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
  height: 150px;
  animation: pulse 1.5s infinite ease-in-out;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 0.3; }
}

/* Course list */
.course-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  padding-bottom: 1rem;
}

.course-card {
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
  background: white;
  transition: transform 0.2s, box-shadow 0.2s;
}

.course-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.course-card h3 {
  color: #1e293b;
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.course-card p {
  color: #64748b;
  margin: 0.3rem 0;
}

/* Course actions */
.course-actions {
  margin-top: 1.5rem;
  display: flex;
  justify-content: flex-end;
}

/* Buttons */
.btn-primary {
  background: #4f46e5;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: #4338ca;
  transform: translateY(-1px);
}

.btn-delete {
  background: #ef4444;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-delete:hover {
  background: #dc2626;
  transform: translateY(-1px);
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
  border-radius: 0.5rem;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}

.modal-content h3 {
  margin-top: 0;
  color: #1e293b;
}

/* Form styles */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #334155;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.25rem;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
}

select.form-input option[disabled] {
  color: #94a3b8;
}

select.form-input:invalid {
  color: #94a3b8;
}

select.form-input option:not([disabled]) {
  color: #1e293b;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 2rem;
}

.btn-submit {
  background: #10b981;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
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
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel:hover {
  background: #475569;
  transform: translateY(-1px);
}

/* Teacher search styles */
.teacher-search-container {
  position: relative;
}

.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-top: none;
  border-radius: 0 0 0.25rem 0.25rem;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.suggestion-item {
  padding: 0.75rem;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f1f5f9;
}

.suggestion-item:hover {
  background: #f8fafc;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.no-results {
  color: #64748b;
  font-style: italic;
  cursor: default;
}

.teacher-email {
  display: block;
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.selected-teacher {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: #f0fdf4;
  border-radius: 0.25rem;
  color: #166534;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .course-list {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    padding: 1.5rem;
    margin: 0 1rem;
  }
  
  .course-management {
    padding-top: 5rem;
  }
}
</style>