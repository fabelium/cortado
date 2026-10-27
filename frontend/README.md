# frontend — Nuxt web/UI

The Nuxt 4 SPA/SSR UI where the user curates topics and triggers generation.
Talks to the Laravel `../api` over JSON (auth via Sanctum, SPA cookie-based) —
never to the Python engine directly.

Status: **skeleton only**. No product screens yet. The Nuxt ↔ API contract lives
in `../contract/openapi/` (reserved, not authored yet).

## Stack

Nuxt 4 (SSR universal) · TypeScript · pnpm · Nuxt UI 4 (+ Tailwind v4) · Pinia ·
@nuxt/eslint · Vitest (@nuxt/test-utils).

## Commands

    pnpm install        # install deps
    pnpm run dev        # dev server (http://localhost:3000)
    pnpm run build      # production build (.output/)
    pnpm run lint       # ESLint
    pnpm run test       # Vitest

## Config

`NUXT_PUBLIC_API_BASE` (see `.env.example`) sets the Laravel API base URL,
read via `useRuntimeConfig().public.apiBase`. Never hardcode the API URL.

Design: `../docs/laravel-web.md`.
