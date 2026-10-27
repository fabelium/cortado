<?php

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;

uses(RefreshDatabase::class);

it('issues a usable bearer token for valid credentials', function () {
    $user = User::factory()->create(['password' => Hash::make('secret-password')]);

    $token = $this->postJson('/api/tokens', [
        'email' => $user->email,
        'password' => 'secret-password',
        'device_name' => 'curl',
    ])
        ->assertOk()
        ->assertJsonStructure(['token'])
        ->json('token');

    // The token authenticates a protected route.
    $this->withToken($token)
        ->getJson('/api/user')
        ->assertOk()
        ->assertJson(['email' => $user->email]);
});

it('rejects token issuance with wrong credentials', function () {
    $user = User::factory()->create(['password' => Hash::make('secret-password')]);

    $this->postJson('/api/tokens', [
        'email' => $user->email,
        'password' => 'wrong',
        'device_name' => 'curl',
    ])
        ->assertStatus(422)
        ->assertJsonValidationErrors('email');
});

it('requires email, password and device_name to issue a token', function () {
    $this->postJson('/api/tokens', [])
        ->assertStatus(422)
        ->assertJsonValidationErrors(['email', 'password', 'device_name']);
});

it('revokes the current token on logout', function () {
    $user = User::factory()->create(['password' => Hash::make('secret-password')]);
    $token = $this->postJson('/api/tokens', [
        'email' => $user->email,
        'password' => 'secret-password',
        'device_name' => 'curl',
    ])->json('token');

    $this->withToken($token)->postJson('/api/logout')->assertNoContent();

    expect($user->tokens()->count())->toBe(0);

    // Drop the in-memory guard so the next call re-resolves auth from scratch,
    // as a fresh production request would. The revoked token no longer works.
    $this->app['auth']->forgetGuards();
    $this->withToken($token)->getJson('/api/user')->assertUnauthorized();
});
