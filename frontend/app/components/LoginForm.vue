<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const email = ref('')
const password = ref('')

async function submit() {
  await auth.login({ email: email.value, password: password.value })
  if (auth.isAuthenticated) await navigateTo('/')
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <UInput v-model="email" type="email" placeholder="Correo electrónico" autocomplete="email" required class="w-full" />
    <UInput v-model="password" type="password" placeholder="Contraseña" autocomplete="current-password" required class="w-full" />

    <UAlert
      v-if="auth.status === 'error'"
      color="error"
      icon="i-lucide-triangle-alert"
      :title="auth.error ?? 'No se pudo iniciar sesión'"
    />

    <UButton type="submit" block :loading="auth.status === 'loading'">Entrar</UButton>

    <p class="text-sm text-(--ui-text-muted)">
      ¿Aún no tienes cuenta?
      <NuxtLink to="/register" class="text-primary">Regístrate</NuxtLink>
    </p>
  </form>
</template>
