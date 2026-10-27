<?php

namespace App\Http\Controllers;

use App\Models\EngineJob;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class JobController extends Controller
{
    public function __invoke(Request $request, string $id): JsonResponse
    {
        // Scoped to the owner: someone else's job id 404s (no existence leak).
        $job = EngineJob::query()
            ->whereKey($id)
            ->where('user_id', $request->user()->id)
            ->firstOrFail();

        return response()->json([
            'ok' => true,
            'job' => [
                'id' => $job->id,
                'action' => $job->action,
                'status' => $job->status,
                'result' => $job->result,
                'error' => $job->error,
                'code' => $job->code,
            ],
        ]);
    }
}
