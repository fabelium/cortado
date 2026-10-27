<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Concerns\QueuesEngineJobs;
use App\Http\Requests\BookRequest;
use Illuminate\Http\JsonResponse;

class BookController extends Controller
{
    use QueuesEngineJobs;

    public function __invoke(BookRequest $request): JsonResponse
    {
        return $this->queueEngineJob($request, $request->toEngineRequest());
    }
}
