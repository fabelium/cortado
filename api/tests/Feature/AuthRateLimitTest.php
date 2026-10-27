<?php

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;

uses(RefreshDatabase::class);

it('throttles login attempts', function () {
    User::factory()->create(['email' => 'user@example.com']);

    foreach (range(1, 5) as $i) {
        $this->postJson('/api/login', [
            'email' => 'user@example.com',
            'password' => 'wrong-password',
        ])->assertStatus(422);
    }

    $this->postJson('/api/login', [
        'email' => 'user@example.com',
        'password' => 'wrong-password',
    ])->assertStatus(429);
});

it('throttles registration attempts', function () {
    foreach (range(1, 5) as $i) {
        $this->postJson('/api/register', [
            'name' => 'u',
            'email' => "u{$i}@example.com",
            'password' => 'secret-password',
            'password_confirmation' => 'secret-password',
            'device_name' => 'test',
        ])->assertCreated();
    }

    $this->postJson('/api/register', [
        'name' => 'u',
        'email' => 'u6@example.com',
        'password' => 'secret-password',
        'password_confirmation' => 'secret-password',
        'device_name' => 'test',
    ])->assertStatus(429);
});

it('throttles token issuance attempts', function () {
    User::factory()->create(['email' => 'user@example.com']);

    foreach (range(1, 5) as $i) {
        $this->postJson('/api/tokens', [
            'email' => 'user@example.com',
            'password' => 'wrong-password',
            'device_name' => 'test',
        ])->assertStatus(422);
    }

    $this->postJson('/api/tokens', [
        'email' => 'user@example.com',
        'password' => 'wrong-password',
        'device_name' => 'test',
    ])->assertStatus(429);
});
