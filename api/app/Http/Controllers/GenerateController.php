<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Concerns\QueuesEngineJobs;
use App\Http\Requests\GenerateRequest;
use Illuminate\Http\JsonResponse;

class GenerateController extends Controller
{
    use QueuesEngineJobs;

    public function __invoke(GenerateRequest $request): JsonResponse
    {
        return $this->queueEngineJob($request, $request->toEngineRequest());
    }
}
