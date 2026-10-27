<?php

/**
 * Fake engine for SubprocessEngineClient tests. Speaks the same protocol as
 * engine/engine.py (one JSON request on stdin, one JSON response on stdout,
 * contract exit codes) without needing Python/ffmpeg, so the API test suite
 * stays hermetic.
 *
 * Mode is the first CLI arg:
 *   ok       — echo a valid success response for the request's action (exit 0).
 *              The search payload echoes the query back as the fragment name so
 *              a test can prove the request reached stdin.
 *   error    — echo a controlled JSON error response (ok:false) and exit 1.
 *   garbage  — write non-JSON to stdout and exit 1 (infrastructure failure).
 */

$mode = $argv[1] ?? 'ok';
$raw = stream_get_contents(STDIN);
$request = json_decode($raw, true) ?: [];
$action = $request['action'] ?? 'search';

if ($mode === 'garbage') {
    fwrite(STDOUT, 'boom: not json');
    exit(1);
}

if ($mode === 'crash') {
    fwrite(STDOUT, 'killed');
    exit(137);
}

if ($mode === 'error') {
    echo json_encode([
        'version' => '1.0',
        'action' => $action,
        'ok' => false,
        'error' => 'No results.',
        'code' => 1,
    ]);
    exit(1);
}

$payloads = [
    'search' => ['fragments' => [[
        'id' => 'ep1@0-60', 'episode' => 1, 'date' => '2020-01-01',
        'start' => 0, 'end' => 60, 'duration' => 60,
        'name' => $request['query'] ?? '', 'score' => null, 'reason' => null,
    ]]],
    'generate' => ['artifacts' => [[
        'path' => 'output/x.mp3', 'duration' => 60, 'size_bytes' => 1000,
    ]]],
    'transcribe' => ['transcripts' => [[
        'source' => 'output/x.mp3', 'txt' => 'output/x.txt', 'srt' => 'output/x.srt',
    ]]],
    // Chat echoes the query back as the answer to prove the stdin round-trip.
    'chat' => [
        'answer' => $request['query'] ?? '',
        'sources' => [['episode' => 1, 'date' => '2020-01-01', 'topic' => 'x']],
    ],
    'book' => ['artifacts' => [[
        'path' => 'output/x.md', 'format' => 'markdown',
    ]]],
];

echo json_encode(array_merge(
    ['version' => '1.0', 'action' => $action, 'ok' => true],
    $payloads[$action] ?? [],
));
exit(0);
