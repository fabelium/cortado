<?php

use App\Engine\Dto\EngineRequest;
use App\Engine\SubprocessEngineClient;

/**
 * Build a client wired to the PHP fake engine (tests/Fixtures/fake-engine.php)
 * in the given mode. Keeps the suite hermetic — no Python/ffmpeg needed.
 */
function fakeEngineClient(string $mode = 'ok'): SubprocessEngineClient
{
    return new SubprocessEngineClient(
        command: ['php', base_path('tests/Fixtures/fake-engine.php'), $mode],
        cwd: base_path(),
        timeout: 30,
    );
}

it('pipes the request to the engine over stdin and parses the response', function () {
    $response = fakeEngineClient('ok')->search(
        new EngineRequest(action: 'search', query: 'agujero negro'),
    );

    expect($response->ok)->toBeTrue();
    expect($response->action)->toBe('search');
    // The fake echoes the query back as the fragment name: proves stdin round-trip.
    expect($response->fragments[0]['name'])->toBe('agujero negro');
});

it('maps generate and transcribe payloads', function () {
    $generate = fakeEngineClient('ok')->generate(
        new EngineRequest(action: 'generate', query: 'x', selection: ['ep1@0-60']),
    );
    $transcribe = fakeEngineClient('ok')->transcribe(
        new EngineRequest(action: 'transcribe', selection: ['output/x.mp3']),
    );

    expect($generate->artifacts)->not->toBeEmpty();
    expect($generate->artifacts[0]['path'])->toBe('output/x.mp3');
    expect($transcribe->transcripts[0]['srt'])->toBe('output/x.srt');
});

it('maps chat and book payloads', function () {
    $chat = fakeEngineClient('ok')->chat(
        new EngineRequest(action: 'chat', query: '¿Insight?', selection: ['ep1@0-60']),
    );
    $book = fakeEngineClient('ok')->book(
        new EngineRequest(action: 'book', query: 'marte', selection: ['ep1@0-60']),
    );

    // The fake echoes the query back as the answer: proves stdin round-trip.
    expect($chat->answer)->toBe('¿Insight?');
    expect($chat->sources[0]['episode'])->toBe(1);
    expect($book->artifacts[0]['format'])->toBe('markdown');
});

it('passes a controlled engine error through (ok:false + code)', function () {
    $response = fakeEngineClient('error')->search(
        new EngineRequest(action: 'search', query: 'xyzzy'),
    );

    expect($response->ok)->toBeFalse();
    expect($response->error)->toBe('No results.');
    expect($response->code)->toBe(1);
});

it('returns an infrastructure error when the engine emits no valid JSON', function () {
    $response = fakeEngineClient('garbage')->search(
        new EngineRequest(action: 'search', query: 'marte'),
    );

    expect($response->ok)->toBeFalse();
    expect($response->error)->not->toBeNull();
});

it('clamps out-of-contract exit codes to 1', function () {
    // A crash can exit with e.g. 137; the contract error enum is [1, 2, 130].
    $response = fakeEngineClient('crash')->search(
        new EngineRequest(action: 'search', query: 'marte'),
    );

    expect($response->ok)->toBeFalse();
    expect($response->code)->toBe(1);
});
