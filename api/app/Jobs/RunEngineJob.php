<?php

namespace App\Jobs;

use App\Engine\Dto\EngineRequest;
use App\Engine\EngineClient;
use App\Engine\SubprocessEngineClient;
use App\Models\EngineJob;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Queue\SerializesModels;
use Throwable;

/**
 * Runs one queued engine action (generate / transcribe / book) and records
 * the outcome on the EngineJob row the client polls via GET /api/jobs/{id}.
 */
class RunEngineJob implements ShouldQueue
{
    use Queueable;
    use SerializesModels;

    public int $timeout;

    public function __construct(public EngineJob $engineJob)
    {
        // The engine subprocess has its own timeout; give the job headroom
        // so the subprocess limit fires first with a proper error.
        $this->timeout = (int) config('engine.job_timeout') + 60;
    }

    public function handle(EngineClient $engine): void
    {
        $this->engineJob->update(['status' => 'running']);

        // Real runs (download + ffmpeg/whisper) far exceed the sync timeout.
        if ($engine instanceof SubprocessEngineClient) {
            $engine = $engine->withTimeout((int) config('engine.job_timeout'));
        }

        $request = EngineRequest::fromArray($this->engineJob->payload);
        $response = match ($request->action) {
            'generate' => $engine->generate($request),
            'transcribe' => $engine->transcribe($request),
            'book' => $engine->book($request),
        };

        if ($response->ok) {
            $this->engineJob->update([
                'status' => 'done',
                'result' => $response->toArray(),
            ]);
        } else {
            $this->engineJob->update([
                'status' => 'failed',
                'error' => $response->error ?? 'Engine error.',
                'code' => $response->code,
            ]);
        }
    }

    public function failed(?Throwable $exception): void
    {
        $this->engineJob->update([
            'status' => 'failed',
            'error' => $exception?->getMessage() ?? 'Job failed.',
            'code' => 1,
        ]);
    }
}
