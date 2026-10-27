<?php

namespace App\Http\Requests;

use App\Engine\Dto\EngineRequest;
use Illuminate\Foundation\Http\FormRequest;

class BookRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true; // route is guarded by auth:sanctum middleware
    }

    public function rules(): array
    {
        // Export options come nested under `options`, mirroring the engine
        // contract (contract/schema/request.schema.json) and the Nuxt client.
        return [
            'query' => ['required', 'string', 'min:1', 'max:500'],
            'selection' => ['required', 'array', 'min:1'],
            'selection.*' => ['required', 'string', 'min:1'],
            'options' => ['sometimes', 'array'],
            'options.formats' => ['sometimes', 'array'],
            'options.formats.*' => ['required', 'string', 'in:pdf,epub'],
        ];
    }

    public function toEngineRequest(): EngineRequest
    {
        $validated = $this->validated();
        $options = [];
        if (isset($validated['options']['formats'])) {
            $options['formats'] = array_map('strval', $validated['options']['formats']);
        }

        return new EngineRequest(
            action: 'book',
            query: (string) $validated['query'],
            options: $options,
            selection: array_map('strval', $validated['selection']),
        );
    }
}
