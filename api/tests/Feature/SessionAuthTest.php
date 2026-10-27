<?php

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;

uses(RefreshDatabase::class);

// Simulate the Nuxt SPA so Sanctum treats the request as stateful (cookie auth).
beforeEach(fn () => $this->withHeader('Origin', 'http://localhost:3000'));

it('logs in a SPA session with valid credentials', function () {
    $user = User::factory()->create(['password' => Hash::make('secret-password')]);

    $this->postJson('/api/login', [
        'email' => $user->email,
        'password' => 'secret-password',
    ])->assertNoContent();

    $this->assertAuthenticatedAs($user);

    // The session cookie carries auth to a protected route.
    $this->getJson('/api/user')
        ->assertOk()
        ->assertJson(['email' => $user->email]);
});

it('rejects a SPA login with wrong credentials', function () {
    $user = User::factory()->create(['password' => Hash::make('secret-password')]);

    $this->postJson('/api/login', [
        'email' => $user->email,
        'password' => 'wrong',
    ])->assertStatus(422)->assertJsonValidationErrors('email');

    $this->assertGuest();
});

it('logs out and ends the SPA session', function () {
    $user = User::factory()->create(['password' => Hash::make('secret-password')]);

    $this->postJson('/api/login', [
        'email' => $user->email,
        'password' => 'secret-password',
    ])->assertNoContent();

    $this->postJson('/api/logout')->assertNoContent();

    // Re-resolve auth from scratch (as a fresh request would): the invalidated
    // session no longer authenticates a protected route.
    $this->app['auth']->forgetGuards();
    $this->getJson('/api/user')->assertUnauthorized();
});
