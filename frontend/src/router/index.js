import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import UsersView from '../views/UsersView.vue'
import CoursesAdminView from '../views/CoursesAdminView.vue'
import UserFrontView from '../views/UserFrontView.vue'
import MyCoursesView from '../views/MyCoursesView.vue'
import CourseDetailView from '../views/CourseDetailView.vue'
import PaymentResultView from '../views/PaymentResultView.vue'

const routes = [
  { path: '/', component: UserFrontView },
  { path: '/my-courses', component: MyCoursesView },
  { path: '/my-courses/:id', component: CourseDetailView },
  { path: '/payments/success', component: PaymentResultView },
  { path: '/payments/failure', component: PaymentResultView },
  { path: '/payments/pending', component: PaymentResultView },
  { path: '/login', component: LoginView },
  { path: '/admin', redirect: '/admin/courses' },
  { path: '/admin/users', component: UsersView },
  { path: '/admin/courses', component: CoursesAdminView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if(!to.path.startsWith('/admin')) return true

  try{
    const appUser = JSON.parse(localStorage.getItem('app_user') || 'null')
    if(appUser?.is_admin) return true
  }catch(e){ /* invalid cache falls through */ }

  return '/'
})

export default router
