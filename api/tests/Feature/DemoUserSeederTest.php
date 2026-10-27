<?php

use App\Models\User;
use Database\Seeders\DatabaseSeeder;
use Illuminate\Foundation\Testing\RefreshDatabase;

uses(RefreshDatabase::class);

// The root README hands these credentials to the course evaluators.
beforeEach(function () {
    $this->demoEmail = 'evaluador@cortado.test';
    $this->demoPassword = 'Cortado-2026!';
});

function requestToken($test, string $password)
{
    return $test->postJson('/api/tokens', [
        'email' => $test->demoEmail,
        'password' => $password,
        'device_name' => 'seeder-test',
    ]);
}

it('seeds a demo user that can log in with the documented credentials', function () {
    $this->seed(DatabaseSeeder::class);

    requestToken($this, $this->demoPassword)->assertOk()->assertJsonStructure(['token']);
});

it('can be seeded twice without duplicating the demo user', function () {
    $this->seed(DatabaseSeeder::class);
    $this->seed(DatabaseSeeder::class);

    expect(User::where('email', $this->demoEmail)->count())->toBe(1);
});

it('does not overwrite the password if the demo user already changed it', function () {
    User::factory()->create(['email' => $this->demoEmail, 'password' => 'changed-by-owner-1']);

    $this->seed(DatabaseSeeder::class);

    requestToken($this, $this->demoPassword)->assertUnprocessable();
    requestToken($this, 'changed-by-owner-1')->assertOk();
});

it('never seeds the public demo credentials in production', function () {
    $this->app['env'] = 'production';

    // Called directly: `db:seed` itself asks for interactive confirmation in production.
    $this->app->make(DatabaseSeeder::class)->run();

    expect(User::where('email', $this->demoEmail)->exists())->toBeFalse();
});
