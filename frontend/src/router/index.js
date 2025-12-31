import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/courses',
    name: 'courses',
    component: () => import('@/views/CourseView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/register',
    name: 'admin-register',
    component: () => import('@/views/AdminRegisterView.vue'),
    meta: { 
      requiresAuth: true,
      allowedRoles: ['admin']  // Only admin role can access
    }
  },
   {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { 
      requiresAuth: true
    }
  },
  {
    path: '/enrollment',
    name: 'enrollment',
    component: () => import('@/views/EnrollmentView.vue'),
    meta: { 
      requiresAuth: true,
      allowedRoles: ['admin']  // Only admin role can access
    }
  },
  {
    path: '/schedule',
    name: 'schedule',
    component: () => import('@/views/schedule.vue'),
    meta: { 
      requiresAuth: true  // Only admin role can access
    }
  },
   {
    path: '/chatbot',
    name: 'chatbot',
    component: () => import('@/views/ChatAsistant.vue'),
    meta: { 
      requiresAuth: true
    }
  },
  {
    path: '/test',
    name: 'test',
    component: () => import('@/views/test.vue'),
    meta: { 
      requiresAuth: false
    }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  const token = auth.token
  const decoded = auth.decodeToken(token)

  // If no token or failed decoding
  if (!decoded) {
    // If already on the login page, no need to redirect again
    if (to.path !== '/login') {
      auth.logout()
      return next('/login')
    }
  }

  // If token is expired
  if (decoded && decoded.exp * 1000 < Date.now()) {
    console.log("Token expired at:", new Date(decoded.exp * 1000).toLocaleString())
    auth.logout()
    return next('/login')
  }

  // If route requires authentication but there's no valid token
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  next() // Allow navigation if all checks pass
})




export default router