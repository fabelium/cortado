<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()

async function logout() {
  await auth.logout()
  await navigateTo('/login')
}
</script>

<template>
  <header class="flex items-center gap-3 border-b-2 border-neutral-900 pb-3">
    <UIcon name="i-lucide-coffee" class="text-2xl text-primary" />
    <AppLogo class="text-xl font-black tracking-tight" />
    <div v-if="auth.isAuthenticated" class="ml-auto flex items-center gap-3">
      <span class="text-sm text-(--ui-text-muted)">{{ auth.user!.email }}</span>
      <UButton variant="outline" size="sm" icon="i-lucide-log-out" @click="logout">Salir</UButton>
    </div>
  </header>
</template>
