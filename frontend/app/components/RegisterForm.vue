<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const name = ref('')
const email = ref('')
const password = ref('')
const passwordConfirmation = ref('')

async function submit() {
  await auth.register({
    name: name.value,
    email: email.value,
    password: password.value,
    password_confirmation: passwordConfirmation.value,
  })
  if (auth.isAuthenticated) await navigateTo('/')
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <UInput v-model="name" name="name" placeholder="Nombre" autocomplete="name" required class="w-full" />
    <UInput v-model="email" type="email" placeholder="Correo electrónico" autocomplete="email" required class="w-full" />
    <UInput v-model="password" name="password" type="password" placeholder="Contraseña" autocomplete="new-password" required class="w-full" />
    <UInput v-model="passwordConfirmation" name="password_confirmation" type="password" placeholder="Repite la contraseña" autocomplete="new-password" required class="w-full" />

    <UAlert
      v-if="auth.status === 'error'"
      color="error"
      icon="i-lucide-triangle-alert"
      :title="auth.error ?? 'No se pudo crear la cuenta'"
    />

    <UButton type="submit" block :loading="auth.status === 'loading'">Crear cuenta</UButton>

    <p class="text-sm text-(--ui-text-muted)">
      ¿Ya tienes cuenta?
      <NuxtLink to="/login" class="text-primary">Entra</NuxtLink>
    </p>
  </form>
</template>
