<template>
  <div class="dashboard-container">
    <nav class="top-navbar">
      <RouterLink to="/profile" class="nav-item">Profile</RouterLink>
      <RouterLink to="/courses" class="nav-item">
        {{ auth.userRole === 'admin' ? 'Course Management' : 'Courses' }}
      </RouterLink>
      <RouterLink v-if="auth.userRole === 'admin'" to="/admin/register" class="nav-item">Register</RouterLink>
      <RouterLink v-if="auth.userRole === 'admin'" to="/enrollment" class="nav-item">Enrollment</RouterLink>
      <RouterLink to="/schedule" class="nav-item">Schedule</RouterLink>
      <RouterLink to="/chatbot" class="nav-item">Chat Assistant</RouterLink>
          <button @click="auth.logout()" class="btn-logout">
            <span class="logout-icon">→</span> Logout
          </button>
    </nav>
 <div class="dashboard-content">
    <header class="dashboard-header">
      <div class="header-content">
        <div class="welcome-section">
          <h1>Welcome to Smart Campus</h1>
          <p v-if="auth.userRole === 'admin'" >Manage teacher,student,courses and schedules in one place with chat assistant</p>
        </div>
        
      </div>
    </header>

    <section v-if="auth.userRole === 'admin'" class="admin-stats">
      <div class="stats-container">
        <h2 class="stats-title">Campus Overview</h2>
        
        <div v-if="loading" class="loading-indicator">
          <div class="spinner"></div>
          Loading statistics...
        </div>
        
        <div v-if="error" class="error-message">
          Error loading statistics: {{ error }}
          <button @click="fetchStats" class="btn-retry">Retry</button>
        </div>
        
        <div v-if="!loading && !error">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ stats.totalStudents }}</div>
              <div class="stat-label">Total Students</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-value">{{ stats.totalTeachers }}</div>
              <div class="stat-label">Faculty Members</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-value">{{ stats.activeCourses }}</div>
              <div class="stat-label">Active Courses</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-value">{{ stats.currentEnrollments }}</div>
              <div class="stat-label">Current Enrollments</div>
            </div>
          </div>
          
          <div class="charts-container">
            <div class="chart-card">
              <h3>Students by Department</h3>
              <BarChart 
                v-if="stats.departmentDistribution"
                :chartData="stats.departmentDistribution"
                :options="barChartOptions"
              />
            </div>
            
            <div class="chart-card">
              <h3>Enrollment Trend</h3>
              <LineChart 
                v-if="stats.enrollmentTrend"
                :chartData="stats.enrollmentTrend"
                :options="lineChartOptions"
              />
            </div>
            
            <div class="chart-card">
              <h3>Course Distribution</h3>
              <PieChart 
                v-if="stats.courseDistribution"
                :chartData="stats.courseDistribution"
                :options="pieChartOptions"
              />
            </div>
          </div>
          
          <div class="data-tables">
            <div class="table-card">
              <h3>Recent Enrollments</h3>
              <table class="stats-table">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Course</th>
                    <th>Department</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="enrollment in stats.recentEnrollments" :key="enrollment.enrollment_date">
                    <td>{{ enrollment.student_name }}</td>
                    <td>{{ enrollment.course_name }}</td>
                    <td>{{ enrollment.department }}</td>
                    <td>{{ formatDate(enrollment.enrollment_date) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div class="table-card">
              <h3>Upcoming Classes</h3>
              <table class="stats-table">
                <thead>
                  <tr>
                    <th>Course</th>
                    <th>Teacher</th>
                    <th>Day</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="schedule in stats.upcomingSchedules" :key="schedule.course_name + schedule.start_time">
                    <td>{{ schedule.course_name }}</td>
                    <td>{{ schedule.teacher_name }}</td>
                    <td>{{ formatDay(schedule.day_of_week) }}</td>
                    <td>{{ formatTime(schedule.start_time) }} - {{ formatTime(schedule.end_time) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { BarChart, LineChart, PieChart } from 'vue-chart-3'
import { Chart, registerables } from 'chart.js'
import { format, parseISO } from 'date-fns'
import { userService } from '@/services/api'

Chart.register(...registerables)

const auth = useAuthStore()
const loading = ref(true)
const error = ref(null)
const stats = ref({
  totalStudents: 0,
  totalTeachers: 0,
  activeCourses: 0,
  currentEnrollments: 0,
  departmentDistribution: null,
  enrollmentTrend: null,
  courseDistribution: null,
  recentEnrollments: [],
  upcomingSchedules: []
})

const formatDate = (dateString) => format(parseISO(dateString), 'MMM dd, yyyy')
const formatTime = (timeString) => new Date(`1970-01-01T${timeString}`).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
const formatDay = (dayIndex) => ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'][dayIndex] || dayIndex

const barChartOptions = ref({
  responsive: true,
  plugins: {
    legend: { position: 'top' },
    tooltip: {
      callbacks: {
        label: (context) => `${context.dataset.label}: ${context.raw} students`
      }
    }
  }
})

const lineChartOptions = ref({
  responsive: true,
  plugins: {
    legend: { position: 'top' },
    tooltip: {
      callbacks: {
        label: (context) => `${context.dataset.label}: ${context.raw} enrollments`
      }
    }
  }
})

const pieChartOptions = ref({
  responsive: true,
  plugins: {
    legend: { position: 'right' },
    tooltip: {
      callbacks: {
        label: (context) => {
          const label = context.label || ''
          const value = context.raw || 0
          const total = context.dataset.data.reduce((a, b) => a + b, 0)
          const percentage = Math.round((value / total) * 100)
          return `${label}: ${value} (${percentage}%)`
        }
      }
    }
  }
})

const fetchStats = async () => {
  if (auth.userRole !== 'admin') return
  
  try {
    loading.value = true
    error.value = null
    const data = await userService.getStats()
    
    stats.value = {
      ...data,
      recentEnrollments: data.recentEnrollments.map(enrollment => ({
        ...enrollment,
        formattedDate: formatDate(enrollment.enrollment_date)
      })),
      upcomingSchedules: data.upcomingSchedules.map(schedule => ({
        ...schedule,
        formattedStartTime: formatTime(schedule.start_time),
        formattedEndTime: formatTime(schedule.end_time),
        formattedDay: formatDay(schedule.day_of_week)
      }))
    }
  } catch (err) {
    error.value = err.response?.data?.message || err.message
    console.error('Error fetching stats:', err)
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>
<style>
/* Root level reset */
html, body, #app {
  height: 100%;
  margin: 0;
  overflow: auto; /* or scroll */
}
</style>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.dashboard-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto; /* This enables scrolling */
}
.top-navbar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  background-color: #4f46e5;
  padding: 1rem 2rem;
  border-bottom: 1px solid #cbd5e1;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  border-radius: 0.2rem;
  z-index: 1000;
}

.nav-item {
  color: #f8fafc;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.nav-item:hover {
  background-color: #4338ca;
  color: #ffffff;
  border: 1px solid #dcd4d4dc;
  transform: translateY(3px);
}

.dashboard-header {
  background: white;
  padding: 2rem;
  text-align: center;
  border-bottom: 1px solid #e2e8f08f;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-section h1 {
  color: #1e293b;
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.welcome-section p {
  color: #64748b;
  font-size: 1.1rem;
}

.auth-status {
  margin-top: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: #64748b;
}

.btn-logout {
  background: white;
  color: #ef4444;
  padding: 0.5rem 1rem;
  border: 1px solid #ef4444;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: clamp(0.8rem, 1.2vw, 1rem);
}

.btn-logout:hover {
  background: #ef4444;
  color: white;
  transform: translateX(4px);
}

.logout-icon {
  transition: transform 0.3s ease;
}

.btn-logout:hover .logout-icon {
  transform: translateX(2px);
}

.admin-stats {
  background: #f8fafc;
  padding: 2rem;
  flex: 1;
  overflow-y: visible;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}



.stats-container {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-title {
  color: #1e293b;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  text-align: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  text-align: center;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
  color: #3b82f6;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #64748b;
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
}

.chart-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.chart-card h3 {
  color: #1e293b;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.data-tables {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.table-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.stats-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.stats-table th,
.stats-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.stats-table th {
  background: #f1f5f9;
  font-weight: 600;
}

.stats-table tr:hover {
  background: #f8fafc;
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

.error-message {
  padding: 2rem;
  text-align: center;
  background: white;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.error-message {
  color: #ef4444;
  background: #fee2e2;
}

@media (max-width: 768px) {
  .top-navbar {
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.5rem;
  }
  
  .stats-grid,
  .charts-container,
  .data-tables {
    grid-template-columns: 1fr;
  }
  
  .stats-table {
    display: block;
    overflow-x: auto;
  }
  
  .auth-status {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>