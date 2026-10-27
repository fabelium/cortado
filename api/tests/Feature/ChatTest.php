<?php

use App\Engine\Dto\EngineResponse;
use App\Engine\EngineClient;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Tests\Doubles\FakeEngineClient;

uses(RefreshDatabase::class);

it('rejects unauthenticated requests', function () {
    $this->postJson('/api/chat', ['query' => '¿Cuándo aterrizó Insight?', 'selection' => ['ep237@300-480']])
        ->assertUnauthorized();
});

it('returns an answer with sources for an authenticated chat', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/chat', [
        'query' => '¿Cuándo aterrizó la sonda Insight en Marte?',
        'selection' => ['ep237@300-480'],
    ])
        ->assertOk()
        ->assertJson(['ok' => true])
        ->assertJsonStructure([
            'ok',
            'answer',
            'sources' => [
                ['episode', 'date', 'topic'],
            ],
        ]);
});

it('propagates an engine error response instead of a fake 200', function () {
    Sanctum::actingAs(User::factory()->create());
    app()->bind(EngineClient::class, fn () => new FakeEngineClient(
        chat: new EngineResponse(ok: false, action: 'chat', error: 'GEMINI_API_KEY missing.', code: 1),
    ));

    $this->postJson('/api/chat', ['query' => 'marte', 'selection' => ['ep1@0-60']])
        ->assertStatus(502)
        ->assertJson(['ok' => false, 'error' => 'GEMINI_API_KEY missing.']);
});

it('rejects a missing query', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/chat', ['selection' => ['ep1@0-60']])
        ->assertStatus(422)
        ->assertJsonValidationErrors('query');
});

it('rejects an empty selection', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/chat', ['query' => 'marte', 'selection' => []])
        ->assertStatus(422)
        ->assertJsonValidationErrors('selection');
});
