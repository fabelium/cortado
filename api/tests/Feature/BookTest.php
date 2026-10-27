<?php

use App\Engine\Dto\EngineResponse;
use App\Engine\EngineClient;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Tests\Doubles\FakeEngineClient;

uses(RefreshDatabase::class);

it('rejects unauthenticated requests', function () {
    $this->postJson('/api/book', ['query' => 'marte', 'selection' => ['ep237@300-480']])
        ->assertUnauthorized();
});

it('queues the book and exposes the result via the jobs endpoint', function () {
    Sanctum::actingAs(User::factory()->create());

    // The queue runs sync in tests, so by the time we poll the job is done.
    $jobId = $this->postJson('/api/book', [
        'query' => 'Marte',
        'selection' => ['ep237@300-480', 'ep305@120-300'],
        'options' => ['formats' => ['pdf', 'epub']],
    ])
        ->assertStatus(202)
        ->assertJson(['ok' => true, 'job' => ['action' => 'book']])
        ->json('job.id');

    $this->getJson("/api/jobs/{$jobId}")
        ->assertOk()
        ->assertJson(['ok' => true, 'job' => ['status' => 'done']])
        ->assertJsonStructure([
            'job' => ['result' => ['artifacts' => [['path', 'format']]]],
        ]);
});

it('records an engine failure on the job instead of a fake success', function () {
    Sanctum::actingAs(User::factory()->create());
    app()->bind(EngineClient::class, fn () => new FakeEngineClient(
        book: new EngineResponse(ok: false, action: 'book', error: 'pandoc not found.', code: 1),
    ));

    $jobId = $this->postJson('/api/book', ['query' => 'marte', 'selection' => ['ep1@0-60']])
        ->assertStatus(202)
        ->json('job.id');

    $this->getJson("/api/jobs/{$jobId}")
        ->assertOk()
        ->assertJson([
            'ok' => true,
            'job' => ['status' => 'failed', 'error' => 'pandoc not found.', 'code' => 1],
        ]);
});

it('rejects a missing query', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/book', ['selection' => ['ep1@0-60']])
        ->assertStatus(422)
        ->assertJsonValidationErrors('query');
});

it('rejects an unknown export format', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->postJson('/api/book', [
        'query' => 'marte',
        'selection' => ['ep1@0-60'],
        'options' => ['formats' => ['docx']],
    ])
        ->assertStatus(422)
        ->assertJsonValidationErrors('options.formats.0');
});
