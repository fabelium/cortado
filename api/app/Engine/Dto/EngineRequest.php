<?php

namespace App\Engine\Dto;

final readonly class EngineRequest
{
    public function __construct(
        public string $action,
        public ?string $query = null,
        public array $options = [],
        public string $version = '1.0',
        public array $selection = [],
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            action: (string) $data['action'],
            query: $data['query'] ?? null,
            options: $data['options'] ?? [],
            version: $data['version'] ?? '1.0',
            selection: $data['selection'] ?? [],
        );
    }

    public function toArray(): array
    {
        $out = [
            'version' => $this->version,
            'action' => $this->action,
        ];
        if ($this->query !== null) {
            $out['query'] = $this->query;
        }
        if ($this->selection !== []) {
            $out['selection'] = $this->selection;
        }
        if ($this->options !== []) {
            $out['options'] = $this->options;
        }
        return $out;
    }
}
