<?php

namespace App\Http\Controllers\Concerns;

use App\Engine\Dto\EngineRequest;
use App\Jobs\RunEngineJob;
use App\Models\EngineJob;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * Long-running engine actions (generate / transcribe / book) are queued
 * instead of run in-request: the client gets 202 + a job id and polls
 * GET /api/jobs/{id} for the outcome.
 */
trait QueuesEngineJobs
{
    protected function queueEngineJob(Request $request, EngineRequest $engineRequest): JsonResponse
    {
        $job = EngineJob::create([
            'user_id' => $request->user()->id,
            'action' => $engineRequest->action,
            'status' => 'queued',
            'payload' => $engineRequest->toArray(),
        ]);

        RunEngineJob::dispatch($job);

        return response()->json([
            'ok' => true,
            'job' => [
                'id' => $job->id,
                'action' => $job->action,
                'status' => 'queued',
            ],
        ], 202);
    }
}
