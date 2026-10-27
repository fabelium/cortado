<?php

namespace App\Engine\Dto;

final readonly class EngineResponse
{
    public function __construct(
        public bool $ok,
        public string $action,
        public array $fragments = [],
        public string $version = '1.0',
        public ?string $error = null,
        public ?int $code = null,
        public array $artifacts = [],
        public array $transcripts = [],
        public ?string $answer = null,
        public array $sources = [],
    ) {}

    /**
     * Serialize to the action's success shape. Each response schema sets
     * additionalProperties:false, so the payload carries exactly the keys the
     * action defines: one collection (fragments / artifacts / transcripts)
     * keyed by the action, except chat which pairs `answer` with `sources`.
     */
    public function toArray(): array
    {
        if ($this->action === 'chat') {
            return [
                'version' => $this->version,
                'action' => $this->action,
                'ok' => $this->ok,
                'answer' => (string) $this->answer,
                'sources' => $this->sources,
            ];
        }

        [$key, $value] = match ($this->action) {
            'generate', 'book' => ['artifacts', $this->artifacts],
            'transcribe' => ['transcripts', $this->transcripts],
            default => ['fragments', $this->fragments],
        };

        return [
            'version' => $this->version,
            'action' => $this->action,
            'ok' => $this->ok,
            $key => $value,
        ];
    }
}
