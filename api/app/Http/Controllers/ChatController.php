<?php

namespace App\Http\Controllers;

use App\Engine\EngineClient;
use App\Http\Requests\ChatRequest;
use Illuminate\Http\JsonResponse;

class ChatController extends Controller
{
    public function __construct(private readonly EngineClient $engine) {}

    public function __invoke(ChatRequest $request): JsonResponse
    {
        $response = $this->engine->chat($request->toEngineRequest());

        // Surface engine failures instead of returning a misleading 200.
        if (! $response->ok) {
            return response()->json([
                'ok' => false,
                'error' => $response->error ?? 'Engine error.',
                'code' => $response->code,
            ], 502);
        }

        return response()->json([
            'ok' => true,
            'answer' => $response->answer,
            'sources' => $response->sources,
        ]);
    }
}
