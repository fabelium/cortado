# api — Laravel API

API-only Laravel app that drives the Python `engine` and serves the Nuxt
`frontend`. See `../contract/` for the engine seam.

## Current state

Vertical slice `search`: `POST /api/search` (Sanctum-guarded) → `EngineClient`
stub → contract-valid `fragments`.

## Quick start

    composer install
    cp .env.example .env && php artisan key:generate
    ./vendor/bin/pest
    php artisan serve
