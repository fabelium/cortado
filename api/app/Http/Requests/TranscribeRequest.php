<?php

namespace App\Http\Requests;

use App\Engine\Dto\EngineRequest;
use Closure;
use Illuminate\Foundation\Http\FormRequest;

class TranscribeRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true; // route is guarded by auth:sanctum middleware
    }

    public function rules(): array
    {
        return [
            'selection' => ['required', 'array', 'min:1'],
            // Sources are engine-relative paths (e.g. output/clip.mp3). The
            // engine confines them to its output dir, but reject traversal
            // and absolute paths here too — defense in depth at the seam.
            'selection.*' => ['required', 'string', 'min:1', function (string $attribute, mixed $value, Closure $fail): void {
                $path = str_replace('\\', '/', (string) $value);
                if (str_starts_with($path, '/') || in_array('..', explode('/', $path), true)) {
                    $fail("The {$attribute} field must be a relative path without traversal.");
                }
            }],
        ];
    }

    public function toEngineRequest(): EngineRequest
    {
        $validated = $this->validated();

        return new EngineRequest(
            action: 'transcribe',
            selection: array_map('strval', $validated['selection']),
        );
    }
}
