<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Cross-Origin Resource Sharing (CORS) Configuration
    |--------------------------------------------------------------------------
    |
    | Scoped to the API and the Sanctum CSRF cookie. The Nuxt SPA authenticates
    | with cookie-based Sanctum, which needs credentialed CORS against SPECIFIC
    | origins — browsers reject credentials when the origin is "*". The allowed
    | origin therefore comes from FRONTEND_URL (defaulting to the Nuxt dev URL).
    |
    */

    'paths' => ['api/*', 'sanctum/csrf-cookie'],

    'allowed_methods' => ['*'],

    'allowed_origins' => array_filter([env('FRONTEND_URL', 'http://localhost:3000')]),

    'allowed_origins_patterns' => [],

    'allowed_headers' => ['*'],

    'exposed_headers' => [],

    'max_age' => 0,

    'supports_credentials' => true,

];
