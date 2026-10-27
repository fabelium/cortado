<?php

use App\Jobs\RunEngineJob;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Queue;
use Laravel\Sanctum\Sanctum;

uses(RefreshDatabase::class);

it('rejects unauthenticated requests', function () {
    $this->getJson('/api/jobs/some-id')->assertUnauthorized();
});

it('returns 404 for an unknown job id', function () {
    Sanctum::actingAs(User::factory()->create());

    $this->getJson('/api/jobs/00000000-0000-0000-0000-000000000000')
        ->assertNotFound();
});

it('hides jobs that belong to another user', function () {
    $owner = User::factory()->create();
    Sanctum::actingAs($owner);
    $jobId = $this->postJson('/api/generate', [
        'query' => 'marte',
        'selection' => ['ep1@0-60'],
    ])->json('job.id');

    Sanctum::actingAs(User::factory()->create());

    $this->getJson("/api/jobs/{$jobId}")->assertNotFound();
});

it('reports a queued job before the worker picks it up', function () {
    Queue::fake();
    Sanctum::actingAs(User::factory()->create());

    $response = $this->postJson('/api/generate', [
        'query' => 'marte',
        'selection' => ['ep1@0-60'],
    ]);

    $response->assertStatus(202)->assertJson([
        'ok' => true,
        'job' => ['action' => 'generate', 'status' => 'queued'],
    ]);
    Queue::assertPushed(RunEngineJob::class);

    $this->getJson('/api/jobs/'.$response->json('job.id'))
        ->assertOk()
        ->assertJson([
            'ok' => true,
            'job' => ['status' => 'queued', 'result' => null, 'error' => null],
        ]);
});
