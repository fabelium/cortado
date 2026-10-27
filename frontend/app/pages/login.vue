<template>
  <UContainer class="py-16 max-w-md space-y-8">
    <header class="flex items-center gap-3">
      <UIcon name="i-lucide-coffee" class="text-2xl text-primary" />
      <AppLogo class="text-xl" />
    </header>
    <UCard>
      <template #header>
        <div class="space-y-1">
          <h1 class="font-extrabold tracking-tight">Entrar</h1>
          <p class="text-sm text-(--ui-text-muted)">
            Un cortado, por favor convierte los episodios de Coffee Break en
            recopilaciones a tu medida. Entra para preparar el tuyo.
          </p>
        </div>
      </template>
      <LoginForm />
    </UCard>
  </UContainer>
</template>
