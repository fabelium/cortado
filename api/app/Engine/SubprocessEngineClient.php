<?php

namespace App\Engine;

use App\Engine\Dto\EngineRequest;
use App\Engine\Dto\EngineResponse;
use Illuminate\Support\Facades\Process;

/**
 * Real engine client. Runs the Python engine (engine/engine.py) as a subprocess
 * following the frozen contract: one JSON request on stdin, one JSON response on
 * stdout, progress on stderr. Replaces StubEngineClient once the engine is
 * reachable (selected via config/engine.php `driver`).
 *
 * The command is injected so tests can point it at a fake engine and stay
 * hermetic (no Python/ffmpeg required).
 */
final class SubprocessEngineClient implements EngineClient
{
    /**
     * @param  list<string>  $command  Base command, e.g. ['python3', '/path/engine.py'].
     */
    public function __construct(
        private readonly array $command,
        private readonly ?string $cwd = null,
        private readonly int $timeout = 120,
    ) {}

    public function withTimeout(int $timeout): self
    {
        return new self($this->command, $this->cwd, $timeout);
    }

    public function search(EngineRequest $request): EngineResponse
    {
        return $this->run($request);
    }

    public function generate(EngineRequest $request): EngineResponse
    {
        return $this->run($request);
    }

    public function transcribe(EngineRequest $request): EngineResponse
    {
        return $this->run($request);
    }

    public function chat(EngineRequest $request): EngineResponse
    {
        return $this->run($request);
    }

    public function book(EngineRequest $request): EngineResponse
    {
        return $this->run($request);
    }

    private function run(EngineRequest $request): EngineResponse
    {
        $result = Process::path($this->cwd ?? base_path())
            ->timeout($this->timeout)
            ->input((string) json_encode($request->toArray()))
            ->run($this->command);

        $decoded = json_decode($result->output(), true);

        // stdout must be a JSON object carrying `ok`. Controlled errors still
        // produce such a body (with ok:false); only a crash / non-JSON output
        // lands here as an infrastructure failure.
        if (! is_array($decoded) || ! array_key_exists('ok', $decoded)) {
            // Clamp crash exit codes (137, 255, …) to the contract enum [1, 2, 130].
            $exitCode = $result->exitCode() ?: 1;

            return new EngineResponse(
                ok: false,
                action: $request->action,
                error: 'Engine returned no valid response.',
                code: in_array($exitCode, [1, 2, 130], true) ? $exitCode : 1,
            );
        }

        return new EngineResponse(
            ok: (bool) $decoded['ok'],
            action: $decoded['action'] ?? $request->action,
            fragments: $decoded['fragments'] ?? [],
            version: $decoded['version'] ?? '1.0',
            error: $decoded['error'] ?? null,
            code: $decoded['code'] ?? null,
            artifacts: $decoded['artifacts'] ?? [],
            transcripts: $decoded['transcripts'] ?? [],
            answer: $decoded['answer'] ?? null,
            sources: $decoded['sources'] ?? [],
        );
    }
}
