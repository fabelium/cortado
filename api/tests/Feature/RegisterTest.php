<?php

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;

uses(RefreshDatabase::class);

it('registers a user and returns a usable token', function () {
    $token = $this->postJson('/api/register', [
        'name' => 'Demo',
        'email' => 'demo@cortado.test',
        'password' => 'password123',
        'password_confirmation' => 'password123',
        'device_name' => 'curl',
    ])
        ->assertCreated()
        ->assertJsonStructure(['token'])
        ->json('token');

    expect(User::where('email', 'demo@cortado.test')->exists())->toBeTrue();

    $this->withToken($token)
        ->getJson('/api/user')
        ->assertOk()
        ->assertJson(['email' => 'demo@cortado.test']);
});

it('rejects a duplicate email', function () {
    User::factory()->create(['email' => 'taken@cortado.test']);

    $this->postJson('/api/register', [
        'name' => 'Demo',
        'email' => 'taken@cortado.test',
        'password' => 'password123',
        'password_confirmation' => 'password123',
    ])
        ->assertStatus(422)
        ->assertJsonValidationErrors('email');
});

it('rejects an unconfirmed or too-short password', function () {
    $this->postJson('/api/register', [
        'name' => 'Demo',
        'email' => 'demo@cortado.test',
        'password' => 'short',
        'password_confirmation' => 'mismatch',
    ])
        ->assertStatus(422)
        ->assertJsonValidationErrors('password');
});

it('requires name, email and password', function () {
    $this->postJson('/api/register', [])
        ->assertStatus(422)
        ->assertJsonValidationErrors(['name', 'email', 'password']);
});
