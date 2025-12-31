import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
const api = axios.create({
  baseURL: 'http://localhost:8000'
})
const authStore = useAuthStore()
// Request interceptor for auth token
api.interceptors.request.use(config => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// Error interceptor
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      // Handle specific status codes
      if (error.response.status === 401) {
        const auth = useAuthStore()
        auth.logout()
        window.location.reload()
      }
      return Promise.reject(error.response.data)
    }
    return Promise.reject(error)
  }
)

export const courseService = {
  async getAll() {
    const response = await api.get('/courses/getCourse')
    return response.data
  },
  async getforTeacher(teacher_id) {
    const response = await api.get(`/courses/getTeachersCourse/${teacher_id}`)
    return response.data
  },
  async getforStudent(student_id) {
    const response = await api.get(`/courses/getStudentsCourse/${student_id}`)
    return response.data
  },
  async getCommonCourses(studentIds) {
  try {
    const response = await api.post('/courses/common-courses', {
      student_ids: studentIds
    });
    return response.data;
  } catch (error) {
    console.error('API call failed:', error);
    throw error;  // Let caller handle error if needed
  }
},
  async create(courseData) {
    const response = await api.post('/courses/createCouse', courseData)
    return response.data
  },
  
  async delete(courseId) {
    try {
      await api.delete(`/courses/${courseId}`);
    } catch (error) {
      console.error('Error deleting course:', error);
      throw error.response?.data || error.message;
    }
  }
}



  // Add to your existing api.js
export const userService = {
  async register(userData) {
    console.log("UserData");
    for (let pair of userData.entries()) {
        console.log(`${pair[0]}:`, pair[1])
      }
    const response = await api.post('/register', userData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    console.log("Response: ",response)
    return response;
  },

  async getDepartments() {
    const response = await api.get('/departments');
    return response.data;
  },
    async searchTeachers(departmentCode, query = '') {
  try {
    const response = await api.get('/teachers/search', {
      params: {
        department: departmentCode,
        query: query.trim() // Send trimmed query
      }
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return []; // Return empty array for "no teachers found"
    }
    console.error("Teacher search error:", error);
    throw error;
  }
},
 async searchStudents(params) {
    try {
    const response = await api.get('/students/search', {
      params: {
        department: params.department,
        query: params.query.trim() // Send trimmed query
      }
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return []; // Return empty array for "no teachers found"
    }
    console.error("Student search error:", error);
    throw error;
  }
},
 async getStudents(params) {
    try {
    const response = await api.get('/students/search-by-year', {
      params: {
        year: params.year,
        department: params.department // Send trimmed query
      }
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return []; // Return empty array for "no teachers found"
    }
    console.error("Student search error:", error);
    throw error;
  }
},
async getAllStudents() {
    try {
      const response = await api.get('/students')
      return response.data
    } catch (error) {
      console.error('Error fetching students:', error)
      return []
    }
  },
  async getStats() {
    const response = await api.get('/stats')
    return response.data
  }
};
export const fetchUserProfile = {
  async getProfile() {
    try {
      const token = authStore.token // Access the token value
      if (!token) {
        throw new Error('No authentication token found')
      }

      const profileResponse = await api.get('/profile', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return profileResponse.data
      
    } catch (error) {
      console.error('Error fetching profile:', error)
      throw error
    }
  },
 async getImage() {
    try {
      const user_id = authStore.userId // Properly declare user_id
      console.log("Fetching image for user:", user_id)
      
      const imageResponse = await api.get(`/image/${user_id}`, {
        responseType: 'blob' // Important for handling binary image data
      })
      
      // Create a URL that can be used in img src
      const imageUrl = URL.createObjectURL(imageResponse.data)
      console.log("Generated image URL:", imageUrl)
      
      return imageUrl
    } catch (error) {
      console.error('Error fetching image:', error)
      return '/default-profile.png' // Fallback image
    }
  }
};
export const enrollmentService = {
  // Enroll single student
  async enrollStudent(courseId, studentId) {
    try {
      const response = await api.post('/enrollments', {
        course_id: courseId,
        student_id: studentId
      });
      
      // Return consistent response format
      return {
        success: response.data.check === "success",
        title: response.data.check === "success" ? "Success" : "Failed",
        message: response.data.massage || response.data.message,
        data: response.data
      };
    } catch (error) {
      console.error('Enrollment error:', error.response?.data || error.message);
      return {
        success: false,
        title: "Error",
        message: error.response?.data?.message || error.response?.data?.massage || 'Enrollment failed',
        error: error.response?.data || error.message
      };
    }
  },

  // Bulk enroll students
  async bulkEnroll(courseId, studentIds) {
    try {
      const response = await api.post('/enrollments/bulk', {
        course_id: courseId,
        student_ids: studentIds
      });
      
      return {
        success: true,
        title: "Bulk Enrollment",
        message: response.data.message,
        enrolledCount: response.data.enrolled_count,
        errors: response.data.errors || [],
        data: response.data
      };
    } catch (error) {
      console.error('Bulk enrollment error:', error.response?.data || error.message);
      return {
        success: false,
        title: "Error",
        message: error.response?.data?.message || 'Bulk enrollment failed',
        errors: error.response?.data?.errors || [],
        error: error.response?.data || error.message
      };
    }
  }
};
export const scheduleService = {


  // Get teacher's schedule

async getTeacherSchedule(teacherId, academicYear, semester) {
    try {
      const response = await api.get(`/schedules/teacher/${teacherId}`, {
        params: { academic_year: academicYear, semester: semester }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching teacher schedule:', error);
      throw error.response?.data || error.message;
    }
  },

  // Get student's schedule
  async getStudentSchedule(studentId, academicYear, semester) {
    try {
      const response = await api.get(`/schedules/student/${studentId}`, {
        params: { academic_year: academicYear, semester }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching student schedule:', error);
      throw error.response?.data || error.message;
    }
  },


  // Get common group schedule
async getCommonGroupSchedule(group_code, academicYear, semester) {
  try {
    const response = await api.get(`/schedules/group/${group_code}`, {
      params: {  // Add params object for query parameters
        academic_year: academicYear,
        semester: semester
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching group schedule:', error);
    throw error.response?.data || error.message;
  }
},

  // Update group schedule
async updateGroupSchedule(group_code, scheduleData, academicYear, semester) {
  try {
    const response = await api.put('/schedules/group', {
      group_code,
      schedule: scheduleData,
      academic_year: academicYear,
      semester
    });
    return response.data;
  } catch (error) {
    console.log('Error updating group schedule:', error);

    // If error is already a plain object (like {detail: "..."}), wrap it into Error so it has .message
    if (error && typeof error === 'object' && error.detail) {
      throw new Error(error.detail);
    }
    // Otherwise throw the original error (Axios error object)
    throw error;
  }
}




};

  export default api