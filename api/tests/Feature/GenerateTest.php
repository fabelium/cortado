<?php

use App\Engine\Dto\EngineResponse;
use App\Engine\EngineClient;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Tests\Doubles\FakeEngineClient;

uses(RefreshDatabase::class);

it('rejects unauthenticated requests', function () {
    $this->postJson('/api/generate', ['query' => 'marte', 'selection' => ['ep1@0-60']])
        ->assertUnauthorized();
});

it('queues the generation and exposes the result via the jobs endpoint', function () {
    Sanctum::actingAs(User::factory()->create());

    // The queue runs sync in tests, so by the time we poll the job is done.
    $jobId = $this->postJson('/api/generate', [
        'query' => 'marte',
        'selection' => ['ep1@0-60'],
        'options' => ['intro' => true, 'disclaimer' => true],
    ])
        ->assertStatus(202)
        ->assertJson(['ok' => true, 'job' => ['action' => 'generate']])
        ->json('job.id');

    $this->getJson("/api/jobs/{$jobId}")
        ->assertOk()
        ->assertJson(['ok' => true, 'job' => ['status' => 'done']])
        ->assertJsonStructure([
            'job' => ['result' => ['artifacts' => [['path', 'duration', 'size_bytes']]]],
        ]);
});

it('records an engine failure on the job instead of a fake success', function () {
    Sanctum::actingAs(User::factory()->create());
    app()->bind(EngineClient::class, fn () => new FakeEngineClient(
        generate: new EngineResponse(ok: false, action: 'generate', error: 'ffmpeg not found.', code: 1),
    ));

    $jobId = $this->postJson('/api/generate', ['query' => 'marte', 'selection' => ['ep1@0-60']])
        ->assertStatus(202)
        ->json('job.id');

    $this->getJson("/api/jobs/{$jobId}")
        ->assertOk()
        ->assertJson([
            'ok' => true,
            'job' => ['status' => 'failed', 'error' => 'ffmpeg not found.', 'code' => 1],
        ]);
});

it('rejects a missing query', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/generate', ['selection' => ['ep1@0-60']])
        ->assertStatus(422)
        ->assertJsonValidationErrors('query');
});

it('rejects an empty selection', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/generate', ['query' => 'marte', 'selection' => []])
        ->assertStatus(422)
        ->assertJsonValidationErrors('selection');
});
