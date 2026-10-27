import { useAuthStore } from '~/stores/auth'

const PUBLIC_ROUTES = ['/login', '/register']

export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  if (!auth.isAuthenticated && !PUBLIC_ROUTES.includes(to.path)) {
    return navigateTo('/login')
  }
  if (auth.isAuthenticated && PUBLIC_ROUTES.includes(to.path)) {
    return navigateTo('/')
  }
})
