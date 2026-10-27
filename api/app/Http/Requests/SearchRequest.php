<?php

namespace App\Http\Requests;

use App\Engine\Dto\EngineRequest;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class SearchRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true; // route is guarded by auth:sanctum middleware
    }

    public function rules(): array
    {
        return [
            'query' => ['required', 'string', 'min:1', 'max:500'],
            'semantic' => ['sometimes', 'boolean'],
            'model' => ['sometimes', Rule::in(['local', 'gemini'])],
            'classify' => ['sometimes', 'boolean'],
            'limit' => ['sometimes', 'integer', 'min:1'],
            'top_k' => ['sometimes', 'integer', 'min:1'],
            'threshold' => ['sometimes', 'numeric', 'between:0,1'],
        ];
    }

    public function toEngineRequest(): EngineRequest
    {
        // Validation checks types but does not coerce them: non-JSON clients
        // deliver scalars as strings. Cast to the contract types so the
        // EngineRequest honours contract/schema/request.schema.json.
        $validated = $this->validated();
        $options = [];
        if (array_key_exists('semantic', $validated)) {
            $options['semantic'] = $this->boolean('semantic');
        }
        if (array_key_exists('model', $validated)) {
            $options['model'] = (string) $validated['model'];
        }
        if (array_key_exists('classify', $validated)) {
            $options['classify'] = $this->boolean('classify');
        }
        if (array_key_exists('limit', $validated)) {
            $options['limit'] = (int) $validated['limit'];
        }
        if (array_key_exists('top_k', $validated)) {
            $options['top_k'] = (int) $validated['top_k'];
        }
        if (array_key_exists('threshold', $validated)) {
            $options['threshold'] = (float) $validated['threshold'];
        }

        return new EngineRequest(
            action: 'search',
            query: (string) $validated['query'],
            options: $options,
        );
    }
}
