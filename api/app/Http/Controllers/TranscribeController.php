<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Concerns\QueuesEngineJobs;
use App\Http\Requests\TranscribeRequest;
use Illuminate\Http\JsonResponse;

class TranscribeController extends Controller
{
    use QueuesEngineJobs;

    public function __invoke(TranscribeRequest $request): JsonResponse
    {
        return $this->queueEngineJob($request, $request->toEngineRequest());
    }
}
