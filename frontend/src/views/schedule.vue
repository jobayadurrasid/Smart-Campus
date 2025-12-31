<template>
  <div class="app-container">
    <!-- Corner Menu -->
    <div v-if="showDialog" class="dialog-overlay" @click.self="showDialog = false">
      <div class="dialog-box" :class="dialogClass">
        <h3>{{ dialogTitle }}</h3>
        <p>{{ dialogMessage }}</p>
        <div v-if="dialogErrors.length > 0" class="dialog-errors">
          <div v-for="(error, index) in dialogErrors" :key="index" class="error-item">
            {{ error }}
          </div>
        </div>
        <button @click="showDialog = false" class="dialog-close">OK</button>
      </div>
    </div>
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
      <RouterLink to="/chatbot" class="menu-item">Chat Assistant</RouterLink>
        <RouterLink to="/profile" class="menu-item">Profile</RouterLink>
        <button @click="auth.logout()" class="menu-item logout-item">
          Logout
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="schedule-management">
      <div v-if="error" class="error-message">
        {{ error }}
        <button @click="error = null" class="error-close">×</button>
      </div>
      <div class="header-section">
        <h2>{{ auth.userRole === 'admin' ? 'Schedule Management' : 'My Schedule' }}</h2>
      </div>

      <!-- Method Selection (Admin Only) -->
      <div v-if="auth.userRole === 'admin'" class="form-group">
        <label>Schedule Method</label>
        <div class="method-options">
          <button 
            @click="scheduleMethod = 'individual'" 
            :class="{ active: scheduleMethod === 'individual' }"
            class="method-btn"
          >
            Individual
          </button>
          <button 
            @click="scheduleMethod = 'group'" 
            :class="{ active: scheduleMethod === 'group' }"
            class="method-btn"
          >
            Group
          </button>
        </div>
      </div>

      <!-- Individual Schedule View -->
      <div v-if="auth.userRole === 'admin' ? scheduleMethod === 'individual' : true" class="schedule-section">
        <!-- Search/Select Controls (Admin Only) -->
        <div v-if="auth.userRole === 'admin'" class="form-row">
          <div class="form-group">
            <select v-model="individualType" @change="onTypeChange" class="form-input">
              <option value="student">Student</option>
              <option value="teacher">Teacher</option>
            </select>
          </div>
          
          <div class="form-group">
            <select 
              v-model="searchDepartment" 
              @change="onDepartmentChange"
              :disabled="!departments.length"
              class="form-input"
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

        <div v-if="auth.userRole === 'admin' && searchDepartment" class="form-group">
          <label>Search {{ individualType === 'teacher' ? 'Teacher' : 'Student' }}</label>
          <div class="search-container">
            <input
              v-model="searchQuery"
              @input="searchIndividuals"
              @focus="showSuggestions = true"
              :placeholder="`Search ${individualType} by name or ID`"
              class="form-input"
            />
            <div v-if="showSuggestions && searchQuery" class="suggestions-dropdown">
              <div 
                v-for="person in filteredIndividuals" 
                :key="person.id"
                @click="selectPerson(person)"
                class="suggestion-item"
              >
                {{ person.name }} (ID: {{ person.id }})
                <span class="person-info" v-if="individualType === 'student'">
                  Year: {{ getYearFromId(person.id) }}
                </span>
              </div>
              <div v-if="filteredIndividuals.length === 0" class="suggestion-item no-results">
                No {{ individualType }}s found in {{ getDepartmentName(searchDepartment) }}
              </div>
            </div>
          </div>
          <div v-if="selectedIndividual" class="selected-person">
            Selected: {{ selectedIndividual.name }} (ID: {{ selectedIndividual.id }})
          </div>
        </div>

        <!-- Academic Controls -->
        <div v-if="auth.userRole !== 'admin' || selectedIndividual" class="form-row">
          <div class="form-group">
            <label>Academic Year</label>
            <select v-model="academicYear" class="form-input" @change="fetchSchedule">
              <option v-for="year in availableAcademicYears" :key="year" :value="year">
                {{ year }}-{{ year + 1 }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Semester</label>
            <select v-model="semester" class="form-input" @change="fetchSchedule">
              <option value="fall">Fall</option>
              <option value="spring">Spring</option>
            </select>
          </div>
        </div>

        <!-- Selected Person Info -->
        <div v-if="selectedIndividual && auth.userRole === 'admin'" class="selected-person">
          Viewing schedule for: <strong>{{ selectedIndividual.name }}</strong> ({{ selectedIndividual.id }})
        </div>
        <div v-else-if="auth.userRole !== 'admin'" class="selected-person">
          Viewing your schedule: <strong>{{ auth.userName }}</strong> ({{ auth.userId }})
        </div>

        <!-- Schedule Display -->
        <div v-if="auth.userRole !== 'admin' || selectedIndividual" class="schedule-container">
          <div class="schedule-grid">
            <!-- Header Row -->
            <div class="header-row">
              <div class="time-col">Time</div>
              <div v-for="day in days" :key="day">{{ day }}</div>
            </div>

            <!-- Time Slots -->
            <div v-for="timeSlot in timeSlots" :key="timeSlot.start" class="schedule-row">
              <div class="time-col">{{ formatTime(timeSlot.start) }} - {{ formatTime(timeSlot.end) }}</div>
              <div
                v-for="(day, dayIndex) in days"
                :key="day"
                :class="[
                  'day-col',
                  {
                    'has-conflict': hasConflict(dayIndex, timeSlot)
                  }
                ]"
              >
                <div v-if="hasIndividualClass(dayIndex, timeSlot)" class="scheduled-class">
                  {{ getCourseName(getIndividualClass(dayIndex, timeSlot).course_id) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Group Schedule View (Admin Only) -->
      <div v-if="auth.userRole === 'admin' && scheduleMethod === 'group'" class="schedule-section">
        <div class="form-row">
          <div class="form-group">
            <label>Department</label>
            <select v-model="groupCriteria.department" class="form-input" required>
              <option value="" disabled>Select Department</option>
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
            <label>Student Year</label>
            <select v-model="groupCriteria.year" class="form-input">
              <option value="" disabled>Select Year</option>
              <option 
                v-for="year in availableYears" 
                :key="year" 
                :value="year"
              >
                {{ year }}
              </option>
            </select>
          </div>
        </div>

        <button 
          class="btn-fetch" 
          @click="fetchStudentGroups" 
          :disabled="!groupCriteria.department || !groupCriteria.year"
        >
          Search Students
        </button>

        <div class="student-list-container">
          <div v-if="groupFilteredStudents.length > 0" class="list-header">
            <h3>Matching Students ({{ groupFilteredStudents.length }})</h3>
          </div>
          
          <div class="student-list">
            <div 
              v-for="student in groupFilteredStudents" 
              :key="student.id" 
              class="student-item"
              @click="toggleStudentSelection(student.id)"
              :class="{ 'selected': selectedStudents.includes(student.id) }"
            >
              <input
                type="checkbox"
                :id="'student-' + student.id"
                :value="student.id"
                v-model="selectedStudents"
                style="display: none"
              >
              <label :for="'student-' + student.id">
                {{ student.name }} ({{ student.id }}) - Year {{ getYearFromId(student.id) }}
              </label>
            </div>
          </div>

          <div v-if="groupsSearched && groupFilteredStudents.length === 0" class="no-results">
            No students found matching the criteria
          </div>

          <div v-if="groupFilteredStudents.length > 0" class="group-actions">
            <button 
              @click="viewGroupSchedule" 
              :disabled="selectedStudents.length === 0"
              class="btn-view"
            >
              View Schedule
            </button>
          </div>
        </div>

        <!-- Academic Controls for Group (Admin Only) -->
        <div v-if="selectedStudents.length > 0 && groupScheduleVisible" class="form-row">
          <div class="form-group">
            <label>Academic Year</label>
            <select v-model="academicYear" class="form-input">
              <option v-for="year in availableAcademicYears" :key="year" :value="year">
                {{ year }}-{{ year + 1 }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Semester</label>
            <select v-model="semester" class="form-input">
              <option value="fall">Fall</option>
              <option value="spring">Spring</option>
            </select>
          </div>
        </div>

        <!-- Group Schedule Display (Admin Only) -->
        <div v-if="selectedStudents.length > 0 && groupScheduleVisible" class="schedule-container">
          <div class="schedule-header">
            <h3>Group Schedule ({{ academicYear }} {{ semester }}) for {{ selectedStudents.length }} Students</h3>
            <div class="action-buttons">
              <button 
                class="btn-edit" 
                @click="editMode = !editMode"
                :class="{ active: editMode }"
              >
                {{ editMode ? 'Cancel Edit' : 'Edit Schedule' }}
              </button>
              <button 
                v-if="editMode" 
                class="btn-submit"
                @click="saveGroupSchedule" 
                :disabled="!hasGroupChanges || isSaving"
              >
                {{ isSaving ? 'Saving...' : 'Save Changes' }}
              </button>
            </div>
          </div>

          <div class="schedule-grid">
            <!-- Header Row -->
            <div class="header-row">
              <div class="time-col">Time</div>
              <div v-for="day in days" :key="day">{{ day }}</div>
            </div>

            <!-- Time Slots -->
            <div v-for="timeSlot in timeSlots" :key="timeSlot.start" class="schedule-row">
              <div class="time-col">{{ formatTime(timeSlot.start) }} - {{ formatTime(timeSlot.end) }}</div>
              <div
                v-for="(day, dayIndex) in days"
                :key="day"
                @click="editGroupSlot(dayIndex, timeSlot)"
                :class="[
                  'day-col',
                  {
                    editable: editMode,
                    'has-conflict': hasGroupConflict(dayIndex, timeSlot)
                  }
                ]"
              >
                <div v-if="hasGroupClass(dayIndex, timeSlot)" class="scheduled-class">
                  {{ getCourseName(getGroupClass(dayIndex, timeSlot).course_id) }}
                </div>
                <div v-else-if="editMode" class="empty-slot">
                  {{ editMode ? '+' : '' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal (Admin Only) -->
    <div v-if="showEditModal && auth.userRole === 'admin'" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <h3>{{ editingSlot ? 'Edit Class' : 'Add Class' }}</h3>
        <div class="modal-body">
          <div class="form-group">
            <label>Course:</label>
            <select v-model="currentEdit.course" class="form-input">
              <option value="" disabled>Select Course</option>
              <option v-for="course in courses" :key="course.id" :value="course.id">
                {{ course.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Day:</label>
            <select v-model="currentEdit.day" class="form-input">
              <option v-for="(day, index) in days" :key="day" :value="index">
                {{ day }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Time Slot:</label>
            <select v-model="currentEdit.timeSlot" class="form-input">
              <option v-for="slot in timeSlots" :key="slot.start" :value="slot">
                {{ formatTime(slot.start) }} - {{ formatTime(slot.end) }}
              </option>
            </select>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="saveScheduleChanges" class="btn-submit">Save</button>
          <button @click="deleteClass" class="btn-delete" v-if="editingSlot">Delete</button>
          <button @click="closeEditModal" class="btn-cancel">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { scheduleService, userService, courseService } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { debounce } from 'lodash-es'

const auth = useAuthStore()

// Data
const scheduleMethod = ref('individual')
const individualType = ref('student')
const searchDepartment = ref('')
const selectedIndividual = ref(null)
const editMode = ref(false)
const isSaving = ref(false)
const departments = ref([])
const teachers = ref([])
const students = ref([])
const filteredIndividuals = ref([])
const courses = ref([])
const groupFilteredStudents = ref([])
const selectedStudents = ref([])
const selectAll = ref(true)
const groupsSearched = ref(false)
const groupScheduleVisible = ref(false)
const currentSchedule = ref([])
const originalSchedule = ref([])
const groupSchedule = ref([])
const originalGroupSchedule = ref([])
const error = ref(null)
const isMenuOpen = ref(false)
const menuRef = ref(null)
const searchQuery = ref('')
const showSuggestions = ref(false)

const academicYear = ref(new Date().getFullYear())
const semester = ref("fall")

// Group schedule criteria
const groupCriteria = ref({
  department: '',
  year: -1
})

const availableAcademicYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({length: 5}, (_, i) => currentYear - i)
})

const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({length: 5}, (_, i) => currentYear - i)
})

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
const timeSlots = Array.from({ length: 9 }, (_, i) => ({
  start: 8 + i,
  end: 9 + i
}))

// Modal state
const showEditModal = ref(false)
const editingSlot = ref(null)
const currentEdit = ref({
  day: 0,
  timeSlot: { start: 8, end: 9 },
  course: '',
  isGroupEdit: false
})

// Dialog state
const showDialog = ref(false)
const dialogTitle = ref('')
const dialogMessage = ref('')
const dialogErrors = ref([])
const dialogType = ref('info')

// Helper functions
const parseApiTime = (timeStr) => {
  if (typeof timeStr === 'number') return timeStr
  if (!timeStr) return 0
  const [hours] = timeStr.toString().split(':')
  return parseFloat(hours) || 0
}

const processScheduleData = (schedule) => {
  return (schedule || []).map(item => ({
    ...item,
    day: parseInt(item.day_of_week || item.day),
    start_time: parseApiTime(item.start_time),
    end_time: parseApiTime(item.end_time),
    course_id: item.course_id
  }))
}

// Unified schedule methods
const hasClass = (dayIndex, timeSlot, schedule) => {
  return schedule.some(c => 
    c.day === dayIndex && 
    parseApiTime(c.start_time) === timeSlot.start && 
    parseApiTime(c.end_time) === timeSlot.end
  )
}

const getClass = (dayIndex, timeSlot, schedule) => {
  return schedule.find(c => 
    c.day === dayIndex && 
    parseApiTime(c.start_time) === timeSlot.start && 
    parseApiTime(c.end_time) === timeSlot.end
  )
}

// Individual schedule methods
const hasIndividualClass = (dayIndex, timeSlot) => 
  hasClass(dayIndex, timeSlot, currentSchedule.value)

const getIndividualClass = (dayIndex, timeSlot) => 
  getClass(dayIndex, timeSlot, currentSchedule.value)

// Group schedule methods
const hasGroupClass = (dayIndex, timeSlot) => 
  hasClass(dayIndex, timeSlot, groupSchedule.value)

const getGroupClass = (dayIndex, timeSlot) => 
  getClass(dayIndex, timeSlot, groupSchedule.value)

// Computed properties
const getDepartmentName = (code) => {
  const dept = departments.value.find(d => d.code === code)
  return dept ? dept.name : code
}

const getYearFromId = (id) => {
  return id.toString().substring(0, 4)
}

const hasGroupChanges = computed(() => {
  return JSON.stringify(groupSchedule.value) !== JSON.stringify(originalGroupSchedule.value)
})

const dialogClass = computed(() => {
  return {
    'dialog-success': dialogType.value === 'success',
    'dialog-error': dialogType.value === 'error',
    'dialog-warning': dialogType.value === 'warning'
  }
})

// Watchers
watch([academicYear, semester], () => {
  if (selectedIndividual.value || auth.userRole !== 'admin') {
    fetchSchedule()
  }
  if (groupScheduleVisible.value) {
    viewGroupSchedule()
  }
})

// Methods
const fetchDepartments = async () => {
  try {
    departments.value = await userService.getDepartments()
  } catch (err) {
    showError('Failed to fetch departments')
  }
}

const searchIndividuals = debounce(async () => {
  if (!searchQuery.value || searchQuery.value.trim().length < 1) {
    if (searchDepartment.value) {
      if (individualType.value === 'teacher') {
        filteredIndividuals.value = teachers.value
      } else {
        filteredIndividuals.value = students.value
      }
    }
    return
  }

  if (!searchDepartment.value) {
    error.value = "Please select a department first"
    return
  }

  try {
    let results
    if (individualType.value === "teacher") {
      results = await userService.searchTeachers(
        searchDepartment.value,
        searchQuery.value.trim()
      )
    } else {
      results = await userService.searchStudents({
        department: searchDepartment.value,
        query: searchQuery.value.trim()
      })
    }
    filteredIndividuals.value = results
    error.value = null
  } catch (err) {
    showError(`Failed to search ${individualType.value}s`)
    console.error(err)
    filteredIndividuals.value = []
  }
}, 300)

const selectPerson = (person) => {
  selectedIndividual.value = person
  searchQuery.value = person.name
  showSuggestions.value = false
  fetchCourses()
  fetchSchedule()
}

const fetchCourses = async () => {
  try {
    const endpoint = individualType.value === 'teacher' 
      ? 'getforTeacher' 
      : 'getforStudent'
    courses.value = await courseService[endpoint](selectedIndividual.value.id)
  } catch (err) {
    showDialogMessage({
      title: 'Error',
      message: 'Failed to fetch courses',
      type: 'error'
    })
    console.error("Failed to fetch courses:", err)
  }
}

const fetchSchedule = async () => {
  if (auth.userRole !== 'admin' && !auth.userId) return
  
  try {
    const userId = auth.userRole === 'admin' ? selectedIndividual.value?.id : auth.userId
    if (!userId) return
    
    const endpoint =individualType.value === 'teacher' 
      ? 'getTeacherSchedule' 
      : 'getStudentSchedule'
    
    const schedule = await scheduleService[endpoint](
      userId,
      academicYear.value,
      semester.value
    )
    
    currentSchedule.value = processScheduleData(schedule)
    originalSchedule.value = JSON.parse(JSON.stringify(currentSchedule.value))
  } catch (err) {
    showError(`Failed to fetch schedule`)
  }
}

const fetchStudentGroups = async () => {
  try {
    groupsSearched.value = true;
    groupScheduleVisible.value = false;
    
    const params = {
      department: groupCriteria.value.department,
      year: groupCriteria.value.year
    };
    
    const students = await userService.getStudents(params);
    groupFilteredStudents.value = students;
    
    // Auto-select all students
    selectedStudents.value = students.map(student => student.id);
  } catch (err) {
    showError('Failed to fetch students');
  }
};

const toggleStudentSelection = (studentId) => {
  const index = selectedStudents.value.indexOf(studentId);
  if (index === -1) {
    selectedStudents.value.push(studentId);
  } else {
    selectedStudents.value.splice(index, 1);
  }
};

const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedStudents.value = groupFilteredStudents.value.map(student => student.id)
  } else {
    selectedStudents.value = []
  }
}

const fetchCommonCourses = async () => {
  if (selectedStudents.value.length === 0) return;

  try {
    courses.value = await courseService.getCommonCourses(selectedStudents.value)
  } catch (err) {
    console.error('Failed to get courses:', err)
  }
}

const viewGroupSchedule = async () => {
  if (selectedStudents.value.length === 0) return;
  
  try {
    groupSchedule.value = [];
    await fetchCommonCourses();
    
    const year = String(groupCriteria.value.year).padStart(4, '0');
    const dept = String(groupCriteria.value.department).padStart(2, '0');
    const groupcode = `${year}${dept}`;
    
    const response = await scheduleService.getCommonGroupSchedule(
      groupcode,
      academicYear.value,
      semester.value
    );
    
    const rawSchedule = Array.isArray(response) ? response : (response?.schedule || [])
    groupSchedule.value = processScheduleData(rawSchedule)
    originalGroupSchedule.value = JSON.parse(JSON.stringify(groupSchedule.value))
    groupScheduleVisible.value = true;
    editMode.value = false;
  } catch (err) {
    console.error("Failed to fetch group schedule:", err);
    showDialogMessage({
      title: 'Error',
      message: 'Failed to fetch group schedule',
      type: 'error',
      errors: [err.message]
    });
    groupSchedule.value = [];
    originalGroupSchedule.value = [];
    groupScheduleVisible.value = true;
    editMode.value = false;
  }
};

const editSlot = (dayIndex, timeSlot) => {
  if (!editMode.value) return
  
  const existingClass = getIndividualClass(dayIndex, timeSlot)
  editingSlot.value = existingClass || null
  
  currentEdit.value = {
    day: dayIndex,
    timeSlot,
    course: existingClass?.course_id || courses.value[0]?.id || '',
    isGroupEdit: false
  }
  
  showEditModal.value = true
}

const editGroupSlot = (dayIndex, timeSlot) => {
  if (!editMode.value) return
  
  const existingClass = getGroupClass(dayIndex, timeSlot)
  editingSlot.value = existingClass || null
  
  currentEdit.value = {
    day: dayIndex,
    timeSlot,
    course: existingClass?.course_id || courses.value[0]?.id || '',
    isGroupEdit: true
  }
  
  showEditModal.value = true
}

const saveScheduleChanges = () => {
  const newClass = {
    day: currentEdit.value.day,
    start_time: currentEdit.value.timeSlot.start,
    end_time: currentEdit.value.timeSlot.end,
    course_id: currentEdit.value.course,
  }
  
  if (currentEdit.value.isGroupEdit) {
    // Handle group schedule edit
    if (editingSlot.value) {
      // Update existing class
      const index = groupSchedule.value.findIndex(c => 
        c.day === editingSlot.value.day &&
        c.start_time === editingSlot.value.start_time &&
        c.end_time === editingSlot.value.end_time
      )
      if (index !== -1) {
        groupSchedule.value[index] = newClass
      }
    } else {
      // Add new class
      groupSchedule.value.push(newClass)
    }
  } else {
    // Handle individual schedule edit
    if (editingSlot.value) {
      // Update existing class
      const index = currentSchedule.value.findIndex(c => 
        c.day === editingSlot.value.day &&
        c.start_time === editingSlot.value.start_time &&
        c.end_time === editingSlot.value.end_time
      )
      if (index !== -1) {
        currentSchedule.value[index] = newClass
      }
    } else {
      // Add new class
      currentSchedule.value.push(newClass)
    }
  }
  
  closeEditModal()
}

const saveGroupSchedule = async () => {
  try {
    isSaving.value = true;

    const formatTime = (time) => {
      const hours = Math.floor(time);
      const minutes = Math.round((time - hours) * 60);
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:00`;
    };

    const updatedSchedule = groupSchedule.value.filter(currentItem => {
      const matchingOriginal = originalGroupSchedule.value.find(originalItem =>
        originalItem.course_id === currentItem.course_id &&
        originalItem.day === currentItem.day
      );

      if (!matchingOriginal) return true;

      return (
        currentItem.start_time !== matchingOriginal.start_time ||
        currentItem.end_time !== matchingOriginal.end_time
      );
    });

    if (updatedSchedule.length === 0) {
      showSuccess('No changes to save.');
      return;
    }

    const transformedGroupSchedule = updatedSchedule.map(item => ({
      academic_year: academicYear.value,
      semester: semester.value,
      day_of_week: item.day.toString(),
      start_time: formatTime(item.start_time),
      end_time: formatTime(item.end_time),
      course_id: item.course_id,
    }));

    const year = String(groupCriteria.value.year).padStart(4, '0');
    const dept = String(groupCriteria.value.department).padStart(2, '0');
    const groupcode = `${year}${dept}`;

    await scheduleService.updateGroupSchedule(
      groupcode,
      transformedGroupSchedule,
      academicYear.value,
      semester.value
    );

    // Only update original schedule on successful save
    originalGroupSchedule.value = JSON.parse(JSON.stringify(groupSchedule.value));
    showSuccess('Group schedule saved successfully');

  } catch (err) {
    const errorMessage =
      err?.response?.data?.detail ||
      err?.response?.data?.message ||
      err?.message ||
      'Unknown error';

    saveError(errorMessage);
  } finally {
    isSaving.value = false;
  }
};

const deleteClass = () => {
  if (currentEdit.value.isGroupEdit) {
    groupSchedule.value = groupSchedule.value.filter(c => 
      !(c.day === editingSlot.value.day &&
      c.start_time === editingSlot.value.start_time &&
      c.end_time === editingSlot.value.end_time)
    )
  } else {
    currentSchedule.value = currentSchedule.value.filter(c => 
      !(c.day === editingSlot.value.day &&
      c.start_time === editingSlot.value.start_time &&
      c.end_time === editingSlot.value.end_time)
    )
  }
  
  closeEditModal()
}

const closeEditModal = () => {
  showEditModal.value = false
  editingSlot.value = null
}

const resetGroupView = () => {
  groupScheduleVisible.value = false
  selectedStudents.value = []
  groupFilteredStudents.value = []
  groupsSearched.value = false
}

const resetIndividualView = () => {
  selectedIndividual.value = null
  currentSchedule.value = []
  originalSchedule.value = []
  searchQuery.value = ''
  showSuggestions.value = false
}

const onDepartmentChange = () => {
  selectedIndividual.value = null
  currentSchedule.value = []
  originalSchedule.value = []
  searchQuery.value = ''
  showSuggestions.value = false
}

const onTypeChange = () => {
  searchDepartment.value = ''
  selectedIndividual.value = null
  currentSchedule.value = []
  originalSchedule.value = []
  filteredIndividuals.value = []
  searchQuery.value = ''
  showSuggestions.value = false
}

const getCourseName = (courseId) => {
  const course = courses.value.find(c => c.id === courseId)
  return course ? course.name : 'Unknown Course'
}

const hasConflict = (dayIndex, timeSlot) => {
  const currentClass = getIndividualClass(dayIndex, timeSlot)
  if (!currentClass) return false
  
  return false
}

const hasGroupConflict = (dayIndex, timeSlot) => {
  if (!editingSlot.value) return false
  
  const currentClass = getGroupClass(dayIndex, timeSlot)
  if (!currentClass) return false
  
  if (editingSlot.value && 
      currentClass.day === editingSlot.value.day &&
      currentClass.start_time === editingSlot.value.start_time &&
      currentClass.end_time === editingSlot.value.end_time) {
    return false
  }
  
  return true
}

const formatTime = (hour) => {
  const hourInt = Math.floor(hour)
  const period = hourInt >= 12 ? 'pm' : 'am'
  const displayHour = hourInt > 12 ? hourInt - 12 : hourInt
  return `${displayHour}${period}`
}

const showError = (message) => {
  error.value = message
}
const saveError = (message) => {
  showDialogMessage({
    title: 'Conflict',
    message: message,
    type: 'error'
  })
}
const showSuccess = (message) => {
  showDialogMessage({
    title: 'Success',
    message: message,
    type: 'success'
  })
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
onMounted(async () => {
  fetchDepartments()
  
  // For non-admin users, automatically set themselves as the selected individual
  if (auth.userRole !== 'admin') {
    individualType.value = auth.userRole
    selectedIndividual.value = {
      id: auth.userId,
      name: auth.userName,
      // Add other necessary properties based on your user object
    }
    console.log(individualType)
    fetchCourses()
    fetchSchedule()
  }
  
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

/* Centered schedule management */
.schedule-management {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 3rem 1rem 1rem;
  flex: 1;
  box-sizing: border-box;
}

.header-section {
  margin-bottom: 2rem;
}

.header-section h2 {
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

select.form-input {
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  background-size: 1em;
  padding-right: 2.5rem;
}

/* Method selection buttons */
.method-options {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.method-btn {
  flex: 1;
  padding: 0.5rem 1rem;
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

/* Search container */
.search-container {
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

.person-info {
  display: block;
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.selected-person {
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

/* Schedule container */
.schedule-container {
  margin-top: 1.5rem;
}

.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
}

/* Schedule grid */
.schedule-grid {
  display: grid;
  grid-template-columns: 120px repeat(5, 1fr);
  gap: 1px;
  background: #e2e8f0;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  overflow: hidden;
}

.header-row, .schedule-row {
  display: contents;
}

.header-row > div {
  background: #0d9f6e;
  color: white;
  padding: 1rem;
  text-align: center;
  font-weight: bold;
}

.time-col {
  background: #436c95;
  padding: 1rem;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
}

.day-col {
  background: rgb(188, 170, 170);
  min-height: 60px;
  padding: 0.5rem;
  transition: background 0.2s;
}

.day-col.editable {
  cursor: pointer;
}

.day-col.editable:hover {
  background: #f8fafc;
}

.scheduled-class {
  background: #e0f2fe;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.9rem;
  text-align: center;
}

.class-info {
  font-size: 0.8rem;
  color: #0369a1;
  margin-top: 0.25rem;
}

.empty-slot {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0d9f6e;
  font-size: 1.2rem;
}

/* Group list */
.group-list-container {
  margin-top: 1.5rem;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.group-list {
  max-height: 500px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
}

.group-item {
  padding: 1rem;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.group-item:last-child {
  border-bottom: none;
}

.group-info h4 {
  margin: 0 0 0.5rem 0;
  color: #1e293b;
}

.group-info p {
  margin: 0.25rem 0;
  color: #64748b;
  font-size: 0.9rem;
}

.group-actions {
  display: flex;
  gap: 0.5rem;
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
}

.btn-submit:hover {
  background: #0d9f6e;
  transform: translateY(-1px);
}

.btn-generate {
  padding: 0.75rem 1.5rem;
  background: #f59e0b;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-generate:hover {
  background: #d97706;
  transform: translateY(-1px);
}

.btn-edit {
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-edit:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

.btn-edit.active {
  background: #dc2626;
}

.btn-edit.active:hover {
  background: #b91c1c;
}

.btn-view {
  padding: 0.75rem 1.5rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
}

.btn-view:hover {
  background: #0d9f6e;
  transform: translateY(-1px);
}
.btn-view:disabled {
  background: #a7f3d0;
  cursor: not-allowed;
  transform: none;
}
.btn-cancel {
  padding: 0.75rem 1.5rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #dc2626;
  transform: translateY(-1px);
}

.btn-delete {
  padding: 0.75rem 1.5rem;
  background: #f97316;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete:hover {
  background: #ea580c;
  transform: translateY(-1px);
}

.no-results {
  background: #fee2e2;
  color: #b91c1c;
  text-align: center;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-content h3 {
  margin-top: 0;
  color: #1e293b;
}

.modal-body {
  margin: 1.5rem 0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
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
  border-top: 1px solid;
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
.form-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-row .form-group {
  flex: 1;
}
/* Responsive adjustments */
@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 1rem;
  }
  
  .schedule-management {
    padding-top: 5rem;
  }
  
  .method-options {
    flex-direction: column;
  }
  
  .schedule-grid {
    grid-template-columns: 80px repeat(5, 1fr);
    font-size: 0.8rem;
  }
  
  .time-col, .header-row > div {
    padding: 0.5rem;
  }
  
  .group-item {
    flex-direction: column;
  }
  
  .group-actions {
    width: 100%;
    flex-direction: column;
  }
  
  .group-actions button {
    width: 80%;
  }
  
  .action-buttons, .modal-actions {
    flex-direction: column;
  }
  
  .action-buttons button, .modal-actions button {
    width: 100%;
  }
  
  .list-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>