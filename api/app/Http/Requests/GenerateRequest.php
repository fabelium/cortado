<?php

namespace App\Http\Requests;

use App\Engine\Dto\EngineRequest;
use Illuminate\Foundation\Http\FormRequest;

class GenerateRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true; // route is guarded by auth:sanctum middleware
    }

    public function rules(): array
    {
        // Audio options come nested under `options`, mirroring the engine
        // contract (contract/schema/request.schema.json) and the Nuxt client.
        return [
            'query' => ['required', 'string', 'min:1', 'max:500'],
            'selection' => ['required', 'array', 'min:1'],
            'selection.*' => ['required', 'string', 'min:1'],
            'options' => ['sometimes', 'array'],
            'options.intro' => ['sometimes', 'boolean'],
            'options.disclaimer' => ['sometimes', 'boolean'],
            'options.split' => ['sometimes', 'nullable', 'integer', 'min:1'],
        ];
    }

    public function toEngineRequest(): EngineRequest
    {
        // Validation checks types but does not coerce them: non-JSON clients
        // deliver scalars as strings. Cast to the contract types so the
        // EngineRequest honours contract/schema/request.schema.json.
        $validated = $this->validated();
        $input = $validated['options'] ?? [];
        $options = [];
        if (array_key_exists('intro', $input)) {
            $options['intro'] = $this->boolean('options.intro');
        }
        if (array_key_exists('disclaimer', $input)) {
            $options['disclaimer'] = $this->boolean('options.disclaimer');
        }
        if (array_key_exists('split', $input)) {
            $options['split'] = $input['split'] === null ? null : (int) $input['split'];
        }

        return new EngineRequest(
            action: 'generate',
            query: (string) $validated['query'],
            options: $options,
            selection: array_map('strval', $validated['selection']),
        );
    }
}
