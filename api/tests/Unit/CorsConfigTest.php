<?php

it('configures CORS for the SPA without a wildcard origin', function () {
    $cors = config('cors');

    // Sanctum SPA cookie auth requires credentials + specific origins.
    expect($cors['supports_credentials'])->toBeTrue();
    expect($cors['allowed_origins'])->not->toContain('*');
    expect($cors['paths'])->toContain('api/*');
});
