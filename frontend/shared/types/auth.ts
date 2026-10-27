// Shapes of the Laravel auth endpoints (register/login/logout/user).
export interface User {
  id: number
  name: string
  email: string
}
export interface LoginRequest {
  email: string
  password: string
}
export interface RegisterRequest {
  name: string
  email: string
  password: string
  password_confirmation: string
}
