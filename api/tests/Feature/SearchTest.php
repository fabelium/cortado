<?php

use App\Engine\Dto\EngineResponse;
use App\Engine\EngineClient;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Tests\Doubles\FakeEngineClient;

uses(RefreshDatabase::class);

it('propagates an engine error response instead of a fake 200', function () {
    Sanctum::actingAs(User::factory()->create());
    app()->bind(EngineClient::class, fn () => new FakeEngineClient(
        search: new EngineResponse(ok: false, action: 'search', error: 'No results for xyz.', code: 1),
    ));

    $this->postJson('/api/search', ['query' => 'xyz'])
        ->assertStatus(502)
        ->assertJson(['ok' => false, 'error' => 'No results for xyz.']);
});

it('rejects unauthenticated requests', function () {
    $this->postJson('/api/search', ['query' => 'marte'])
        ->assertUnauthorized();
});

it('returns fragments for an authenticated search', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/search', ['query' => 'marte'])
        ->assertOk()
        ->assertJson(['ok' => true])
        ->assertJsonStructure([
            'ok',
            'fragments' => [
                ['id', 'episode', 'date', 'start', 'end', 'duration', 'name', 'score', 'reason'],
            ],
        ]);
});

it('rejects a missing query', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/search', [])
        ->assertStatus(422)
        ->assertJsonValidationErrors('query');
});

it('rejects an over-long query', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/search', ['query' => str_repeat('a', 501)])
        ->assertStatus(422)
        ->assertJsonValidationErrors('query');
});
