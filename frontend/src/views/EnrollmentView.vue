<template>
  <div class="app-container">
    <!-- Dialog Box -->
    <div v-if="showDialog" class="dialog-overlay" @click.self="showDialog = false">
      <div class="dialog-box" :class="dialogClass">
        <h3>{{ dialogTitle }}</h3>
        <p>{{ dialogMessage }}</p>
        
        <!-- Show errors list if available -->
        <div v-if="dialogErrors.length > 0" class="dialog-errors">
          <div v-for="(error, index) in dialogErrors" :key="index" class="error-item">
            {{ error }}
          </div>
        </div>
        
        <button @click="showDialog = false" class="dialog-close">OK</button>
      </div>
    </div>

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
      <RouterLink v-if="auth.userRole === 'admin'" to="/schedule" class="menu-item">Schedule</RouterLink>
      <RouterLink to="/chatbot" class="menu-item">Chat Assistant</RouterLink>
              <RouterLink to="/profile" class="menu-item">Profile</RouterLink>
        <button @click="auth.logout()" class="menu-item logout-item">
          Logout
        </button>
      </div>
    </div>

    <div class="course-management">
      <!-- Error message -->
      <div v-if="error" class="error-message">
        {{ error }}
        <button @click="error = null" class="error-close">×</button>
      </div>
      
      <!-- Header section -->
      <div class="header-section">
        <h2>Course Enrollment Management</h2>
      </div>

      <!-- Course Selection -->
      <div class="form-group">
        <label>Select Course</label>
        <select v-model="selectedCourse" class="form-input" @change="clearSelections">
          <option disabled value="">Select a course</option>
          <option v-for="course in courses" :key="course.id" :value="course">
            {{ course.name }} ({{ course.id }})
          </option>
        </select>
      </div>
                <div v-if="loading" class="loading-indicator">
          <div class="spinner"></div>
          Loading...
        </div>
      <!-- Enrollment Method -->
      <div class="form-group">
        <label>Enrollment Method</label>
        <div class="method-options">
          <button 
            @click="enrollmentMethod = 'individual'" 
            :class="{ active: enrollmentMethod === 'individual' }"
            class="method-btn"
          >
            Individual Student
          </button>
          <button 
            @click="enrollmentMethod = 'group'" 
            :class="{ active: enrollmentMethod === 'group' }"
            class="method-btn"
          >
            Group Enrollment
          </button>
        </div>
      </div>

      <!-- Individual Enrollment -->
      <div v-if="enrollmentMethod === 'individual'" class="enrollment-section">
        <div class="form-row">
          <div class="form-group">
            <label>Department</label>
            <select 
              v-model="searchDepartment" 
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
        </div>

        <div class="form-group" v-if="searchDepartment">
          <label>Search Student</label>
          <div class="student-search-container">
            <input
              v-model="studentSearchQuery"
              @input="searchStudents"
              @focus="showStudentSuggestions = true"
              placeholder="Search student by name or ID"
              class="form-input"
              :disabled="!searchDepartment"
            />
            <div v-if="showStudentSuggestions && studentSearchQuery" class="suggestions-dropdown">
              <div 
                v-for="student in filteredStudents" 
                :key="student.id"
                @click="selectStudent(student)"
                class="suggestion-item"
              >
                {{ student.name }} (ID: {{ student.id }})
                <span class="student-info">Year: {{ getYearFromId(student.id) }}</span>
              </div>
              <div v-if="filteredStudents.length === 0" class="suggestion-item no-results">
                No students found in {{ getDepartmentName(searchDepartment) }}
              </div>
            </div>
          </div>
          <div v-if="selectedStudent" class="selected-student">
            Selected: {{ selectedStudent.name }} (ID: {{ selectedStudent.id }})
          </div>
        </div>

        <div v-if="selectedStudent" class="student-confirmation">
          <button @click="enrollStudent" class="btn-submit">
            Enroll 
          </button>
        </div>
      </div>

      <!-- Group Enrollment -->
      <div v-if="enrollmentMethod === 'group'" class="enrollment-section">
        <div class="form-row">
          <div class="form-group">
            <label>Department</label>
            <select v-model="groupCriteria.department" class="form-input" required>
              <option value="" disabled>Select Department</option>
              <option v-for="dept in departments" :key="dept.code" :value="dept.code">
                {{ dept.name }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Year</label>
            <select v-model="groupCriteria.year" class="form-input">
              <option value="-1">All Years</option>
              <option v-for="year in availableYears" :key="year" :value="year">
                {{ year }}
              </option>
            </select>
          </div>
        </div>

        <button 
          @click="fetchStudentsByCriteria" 
          :disabled="!groupCriteria.department"
          class="btn-fetch"
        >
          Find Students
        </button>

        <div v-if="groupFilteredStudents.length > 0" class="student-list-container">
          <div class="list-header">
            <h3>Matching Students ({{ groupFilteredStudents.length }})</h3>
            <label class="select-all">
              <input type="checkbox" v-model="selectAll" @change="toggleSelectAll">
              Select All
            </label>
          </div>
          
          <div class="student-list">
            <div v-for="student in groupFilteredStudents" :key="student.id" class="student-item">
              <input
                type="checkbox"
                :id="'student-' + student.id"
                :value="student.id"
                v-model="selectedStudents"
              >
              <label :for="'student-' + student.id">
                {{ student.name }} ({{ student.id }}) - Year {{ getYearFromId(student.id) }}
              </label>
            </div>
          </div>

          <button 
            @click="enrollSelectedStudents" 
            :disabled="!selectedStudents.length"
            class="btn-submit"
          >
            Enroll Selected ({{ selectedStudents.length }})
          </button>
        </div>
        <div v-else-if="studentsSearched" class="no-results">
          No students found matching the criteria
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { courseService, userService, enrollmentService } from '@/services/api'
import { debounce } from 'lodash-es'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

// Data
const courses = ref([])
const selectedCourse = ref(null)
const enrollmentMethod = ref('individual')
const departments = ref([])
const error = ref(null)

// Individual enrollment
const searchDepartment = ref('')
const studentSearchQuery = ref('')
const studentSuggestions = ref([])
const selectedStudent = ref(null)
const showStudentSuggestions = ref(false)

// Group enrollment
const groupFilteredStudents = ref([])
const groupCriteria = ref({
  department: '',
  year: ''
})
const selectedStudents = ref([])
const selectAll = ref(false)
const studentsSearched = ref(false)

// Menu
const isMenuOpen = ref(false)
const menuRef = ref(null)

// Dialog state
const showDialog = ref(false)
const dialogTitle = ref('')
const dialogMessage = ref('')
const dialogErrors = ref([])
const dialogType = ref('info') // 'info', 'success', 'error', 'warning'

const dialogClass = computed(() => {
  return {
    'dialog-success': dialogType.value === 'success',
    'dialog-error': dialogType.value === 'error',
    'dialog-warning': dialogType.value === 'warning'
  }
})

// Computed properties
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({length: 4}, (_, i) => currentYear - i)
})

const filteredStudents = computed(() => {
  return studentSuggestions.value.filter(student => 
    student.department_code === searchDepartment.value
  )
})

const isFormValid = computed(() => {
  return selectedCourse.value && (
    (enrollmentMethod.value === 'individual' && selectedStudent.value) ||
    (enrollmentMethod.value === 'group' && selectedStudents.value.length > 0)
  )
})

// Methods
const fetchCourses = async () => {
  try {
    courses.value = await courseService.getAll()
  } catch (err) {
    showDialogMessage({
      title: 'Error',
      message: 'Failed to fetch courses',
      type: 'error'
    })
    console.error("Failed to fetch courses:", err)
  }
}

const fetchDepartments = async () => {
  try {
    departments.value = await userService.getDepartments()
  } catch (err) {
    showDialogMessage({
      title: 'Error',
      message: 'Failed to fetch departments',
      type: 'error'
    })
    console.error("Failed to fetch departments:", err)
  }
}

const getDepartmentName = (code) => {
  const dept = departments.value.find(d => d.code === code)
  return dept ? dept.name : code
}

const getYearFromId = (id) => {
  return id.toString().substring(0, 4)
}

const onDepartmentChange = () => {
  studentSearchQuery.value = ''
  selectedStudent.value = null
  studentSuggestions.value = []
}

const searchStudents = debounce(async () => {
  if (!studentSearchQuery.value || studentSearchQuery.value.trim().length < 1) {
    studentSuggestions.value = []
    return
  }

  if (!searchDepartment.value) {
    error.value = "Please select a department first"
    return
  }

  try {
    const students = await userService.searchStudents({
      department: searchDepartment.value,
      query: studentSearchQuery.value.trim()
    })
    studentSuggestions.value = students
    error.value = null
  } catch (err) {
    showDialogMessage({
      title: 'Error',
      message: 'Failed to search students',
      type: 'error'
    })
    console.error(err)
    studentSuggestions.value = []
  }
}, 300)

const selectStudent = (student) => {
  selectedStudent.value = student
  studentSearchQuery.value = student.name
  showStudentSuggestions.value = false
}

const enrollStudent = async () => {
  if (!selectedCourse.value || !selectedStudent.value) return
  
  const response = await enrollmentService.enrollStudent(
    selectedCourse.value.id,
    selectedStudent.value.id
  )
  
  showDialogMessage({
    title: response.title,
    message: response.message,
    type: response.success ? 'success' : 'error',
    errors: response.errors || []
  })
  
  if (response.success) {
    clearSelections()
  }
}

const fetchStudentsByCriteria = async () => {
  try {
    studentsSearched.value = true
    const params = {
      department: groupCriteria.value.department
    }
    
    if (groupCriteria.value.year) {
      params.year = groupCriteria.value.year
    }
    
    const response = await userService.getStudents(params)
    groupFilteredStudents.value = response
    selectedStudents.value = []
    selectAll.value = false
    error.value = null
  } catch (err) {
    showDialogMessage({
      title: 'Error',
      message: 'Failed to fetch students',
      type: 'error'
    })
    console.error("Failed to fetch students:", err)
    groupFilteredStudents.value = []
  }
}

const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedStudents.value = groupFilteredStudents.value.map(s => s.id)
  } else {
    selectedStudents.value = []
  }
}

const enrollSelectedStudents = async () => {
  if (!selectedCourse.value || selectedStudents.value.length === 0) return
  
  const response = await enrollmentService.bulkEnroll(
    selectedCourse.value.id,
    selectedStudents.value
  )
  
  showDialogMessage({
    title: response.title,
    message: response.message,
    type: response.success ? 'success' : 'error',
    errors: response.errors || []
  })
  
  if (response.success) {
    clearSelections()
  }
}

const clearSelections = () => {
  searchDepartment.value = ''
  studentSearchQuery.value = ''
  selectedStudent.value = null
  studentSuggestions.value = []
  selectedStudents.value = []
  selectAll.value = false
  groupCriteria.value = {
    department: '',
    year: ''
  }
  studentsSearched.value = false
}

const showDialogMessage = ({ title, message, type = 'info', errors = [] }) => {
  dialogTitle.value = title
  dialogMessage.value = message
  dialogType.value = type
  dialogErrors.value = errors
  showDialog.value = true
}

const handleClickOutside = (e) => {
  if (isMenuOpen.value && menuRef.value && !menuRef.value.contains(e.target)) {
    isMenuOpen.value = false
  }
}

// Lifecycle hooks
onMounted(() => {
  fetchCourses()
  fetchDepartments()
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
  overflow: hidden;
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

/* Form styles */
.form-group {
  margin-bottom: 1.5rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-row .form-group {
  flex: 1;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
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

/* Method selection buttons */
.method-options {
  display: flex;
  gap: 1rem;
}

.method-btn {
  flex: 1;
  padding: 0.75rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.method-btn.active {
  background: #4f46e5;
  color: white;
  border-color: #4f46e5;
}

.method-btn:hover:not(.active) {
  background: #e2e8f0;
}

/* Student search */
.student-search-container {
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

.student-info {
  display: block;
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.selected-student {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: #f0fdf4;
  border-radius: 0.25rem;
  color: #166534;
}

/* Student confirmation */
.student-confirmation {
  margin-top: 1.5rem;
}

/* Student list for group enrollment */
.student-list-container {
  margin-top: 1.5rem;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.select-all {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.student-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 0.5rem;
}

.student-item {
  padding: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.student-item:last-child {
  border-bottom: none;
}

.student-item label {
  cursor: pointer;
  flex: 1;
}

/* Buttons */
.btn-fetch {
  padding: 0.75rem 1.5rem;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 1.5rem;
}

.btn-fetch:hover {
  background: #4338ca;
  transform: translateY(-1px);
}

.btn-fetch:disabled {
  background: #c7d2fe;
  cursor: not-allowed;
  transform: none;
}

.btn-submit {
  padding: 0.75rem 1.5rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
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

.no-results {
  background: #fee2e2;
  color: #b91c1c;
  text-align: center;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: space-between;
}

/* Dialog styles */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-box {
  background: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.dialog-box h3 {
  margin-top: 0;
  color: #1e293b;
}

.dialog-box p {
  margin: 1rem 0;
}

.dialog-success {
  border-top: 4px solid #10b981;
}

.dialog-error {
  border-top: 4px solid #ef4444;
}

.dialog-warning {
  border-top: 4px solid #f59e0b;
}

.dialog-close {
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 0.25rem;
  padding: 0.5rem 1rem;
  margin-top: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.dialog-close:hover {
  background: #4338ca;
}

.dialog-errors {
  margin-top: 1rem;
  max-height: 200px;
  overflow-y: auto;
  border-top: 1px solid #e2e8f0;
  padding-top: 1rem;
}

.error-item {
  padding: 0.5rem;
  background: #fee2e2;
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
  color: #b91c1c;
  font-size: 0.9rem;
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
  .header-section {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .form-row {
    flex-direction: column;
    gap: 1rem;
  }
  
  .course-management {
    padding-top: 5rem;
  }
  
  .method-options {
    flex-direction: column;
  }
}
</style>