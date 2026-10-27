<?php

namespace App\Engine;

use App\Engine\Dto\EngineRequest;
use App\Engine\Dto\EngineResponse;
use Illuminate\Support\Str;

/**
 * Placeholder engine client. Returns fixed payloads shaped to the frozen
 * contract (contract/schema/response.*.schema.json). Replaced by a real
 * subprocess client once engine.py exists.
 */
final class StubEngineClient implements EngineClient
{
    public function search(EngineRequest $request): EngineResponse
    {
        return new EngineResponse(
            ok: true,
            action: 'search',
            fragments: [[
                'id' => 'ep237@2340-2880',
                'episode' => 237,
                'date' => '2019-10-17',
                'start' => 2340,
                'end' => 2880,
                'duration' => 540,
                'name' => 'Agujeros negros primordiales como candidatos a materia oscura',
                'score' => 0.71,
                'reason' => 'Directly about black holes as dark-matter candidates.',
            ]],
        );
    }

    public function generate(EngineRequest $request): EngineResponse
    {
        $slug = $request->query !== null && $request->query !== ''
            ? Str::slug($request->query)
            : 'clip';

        return new EngineResponse(
            ok: true,
            action: 'generate',
            artifacts: [[
                'path' => "output/{$slug}_2026-06-20.mp3",
                'duration' => 540,
                'size_bytes' => 12976128,
            ]],
        );
    }

    public function transcribe(EngineRequest $request): EngineResponse
    {
        $transcripts = array_map(static function (string $source): array {
            $base = preg_replace('/\.[^.\/]+$/', '', $source);

            return [
                'source' => $source,
                'txt' => "{$base}.txt",
                'srt' => "{$base}.srt",
            ];
        }, $request->selection !== [] ? $request->selection : ['output/clip.mp3']);

        return new EngineResponse(
            ok: true,
            action: 'transcribe',
            transcripts: array_values($transcripts),
        );
    }

    public function chat(EngineRequest $request): EngineResponse
    {
        return new EngineResponse(
            ok: true,
            action: 'chat',
            answer: 'La sonda Insight aterrizó en Marte en noviembre de 2018 (237).',
            sources: [[
                'episode' => 237,
                'date' => '2019-10-17',
                'topic' => 'Insight en Marte',
            ]],
        );
    }

    public function book(EngineRequest $request): EngineResponse
    {
        $slug = $request->query !== null && $request->query !== ''
            ? Str::slug($request->query)
            : 'book';

        // Markdown is always produced; requested formats ride along.
        $formats = array_merge(['markdown'], $request->options['formats'] ?? []);
        $extensions = ['markdown' => 'md', 'pdf' => 'pdf', 'epub' => 'epub'];

        return new EngineResponse(
            ok: true,
            action: 'book',
            artifacts: array_map(static fn (string $format): array => [
                'path' => "output/{$slug}_2026-06-20.{$extensions[$format]}",
                'format' => $format,
            ], $formats),
        );
    }
}
