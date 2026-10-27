<?php

namespace App\Http\Requests;

use App\Engine\Dto\EngineRequest;
use Illuminate\Foundation\Http\FormRequest;

class ChatRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true; // route is guarded by auth:sanctum middleware
    }

    public function rules(): array
    {
        return [
            'query' => ['required', 'string', 'min:1', 'max:500'],
            'selection' => ['required', 'array', 'min:1'],
            'selection.*' => ['required', 'string', 'min:1'],
        ];
    }

    public function toEngineRequest(): EngineRequest
    {
        $validated = $this->validated();

        return new EngineRequest(
            action: 'chat',
            query: (string) $validated['query'],
            selection: array_map('strval', $validated['selection']),
        );
    }
}
