<?php

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Opis\JsonSchema\Errors\ErrorFormatter;
use Opis\JsonSchema\Validator;

uses(RefreshDatabase::class);

/**
 * Guard the seam end to end over real HTTP: what the API hands out (job
 * results for the queued actions, reassembled envelopes for the sync ones)
 * must satisfy the frozen contract response schemas.
 */
function assertMatchesContractSchema(array $document, string $schemaFile): void
{
    $schema = file_get_contents(base_path("../contract/schema/{$schemaFile}"));
    $result = (new Validator())->validate(json_decode(json_encode($document)), $schema);

    $errors = $result->isValid()
        ? ''
        : json_encode((new ErrorFormatter())->format($result->error()));

    expect($result->isValid())->toBeTrue($errors);
}

it('serves a contract-valid generate result through the jobs endpoint', function () {
    Sanctum::actingAs(User::factory()->create());

    $jobId = $this->postJson('/api/generate', [
        'query' => 'marte',
        'selection' => ['ep1@0-60'],
        'options' => ['intro' => true],
    ])->json('job.id');

    $result = $this->getJson("/api/jobs/{$jobId}")->json('job.result');

    assertMatchesContractSchema($result, 'response.generate.schema.json');
});

it('serves a contract-valid transcribe result through the jobs endpoint', function () {
    Sanctum::actingAs(User::factory()->create());

    $jobId = $this->postJson('/api/transcribe', ['selection' => ['output/a.mp3']])
        ->json('job.id');

    $result = $this->getJson("/api/jobs/{$jobId}")->json('job.result');

    assertMatchesContractSchema($result, 'response.transcribe.schema.json');
});

it('serves a contract-valid book result through the jobs endpoint', function () {
    Sanctum::actingAs(User::factory()->create());

    $jobId = $this->postJson('/api/book', [
        'query' => 'Marte',
        'selection' => ['ep1@0-60'],
        'options' => ['formats' => ['pdf', 'epub']],
    ])->json('job.id');

    $result = $this->getJson("/api/jobs/{$jobId}")->json('job.result');

    assertMatchesContractSchema($result, 'response.book.schema.json');
});

it('serves contract-valid chat data over HTTP', function () {
    Sanctum::actingAs(User::factory()->create());

    $body = $this->postJson('/api/chat', [
        'query' => '¿Cuándo aterrizó Insight?',
        'selection' => ['ep237@300-480'],
    ])->assertOk()->json();

    // The public body drops the envelope; rebuild it to check the payload.
    assertMatchesContractSchema([
        'version' => '1.0',
        'action' => 'chat',
        'ok' => $body['ok'],
        'answer' => $body['answer'],
        'sources' => $body['sources'],
    ], 'response.chat.schema.json');
});

it('serves contract-valid search data over HTTP', function () {
    Sanctum::actingAs(User::factory()->create());

    $body = $this->postJson('/api/search', ['query' => 'agujeros negros'])
        ->assertOk()->json();

    assertMatchesContractSchema([
        'version' => '1.0',
        'action' => 'search',
        'ok' => $body['ok'],
        'fragments' => $body['fragments'],
    ], 'response.search.schema.json');
});
