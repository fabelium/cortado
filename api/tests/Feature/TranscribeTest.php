<?php

use App\Engine\Dto\EngineResponse;
use App\Engine\EngineClient;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Tests\Doubles\FakeEngineClient;

uses(RefreshDatabase::class);

it('rejects unauthenticated requests', function () {
    $this->postJson('/api/transcribe', ['selection' => ['output/a.mp3']])
        ->assertUnauthorized();
});

it('queues the transcription and exposes the result via the jobs endpoint', function () {
    Sanctum::actingAs(User::factory()->create());

    // The queue runs sync in tests, so by the time we poll the job is done.
    $jobId = $this->postJson('/api/transcribe', ['selection' => ['output/a.mp3']])
        ->assertStatus(202)
        ->assertJson(['ok' => true, 'job' => ['action' => 'transcribe']])
        ->json('job.id');

    $this->getJson("/api/jobs/{$jobId}")
        ->assertOk()
        ->assertJson(['ok' => true, 'job' => ['status' => 'done']])
        ->assertJsonStructure([
            'job' => ['result' => ['transcripts' => [['source', 'txt', 'srt']]]],
        ]);
});

it('records an engine failure on the job instead of a fake success', function () {
    Sanctum::actingAs(User::factory()->create());
    app()->bind(EngineClient::class, fn () => new FakeEngineClient(
        transcribe: new EngineResponse(ok: false, action: 'transcribe', error: 'Source not found.', code: 1),
    ));

    $jobId = $this->postJson('/api/transcribe', ['selection' => ['output/missing.mp3']])
        ->assertStatus(202)
        ->json('job.id');

    $this->getJson("/api/jobs/{$jobId}")
        ->assertOk()
        ->assertJson([
            'ok' => true,
            'job' => ['status' => 'failed', 'error' => 'Source not found.', 'code' => 1],
        ]);
});

it('rejects an empty selection', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/transcribe', ['selection' => []])
        ->assertStatus(422)
        ->assertJsonValidationErrors('selection');
});

it('rejects path traversal in the selection', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/transcribe', ['selection' => ['../../etc/passwd']])
        ->assertStatus(422)
        ->assertJsonValidationErrors('selection.0');
});

it('rejects absolute paths in the selection', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/transcribe', ['selection' => ['/etc/passwd']])
        ->assertStatus(422)
        ->assertJsonValidationErrors('selection.0');
});
