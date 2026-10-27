<?php

namespace Tests\Doubles;

use App\Engine\Dto\EngineRequest;
use App\Engine\Dto\EngineResponse;
use App\Engine\EngineClient;

/**
 * Configurable engine double for feature tests. Each action returns the
 * EngineResponse handed to the constructor, or a trivial ok response if none
 * was given — so a test only states the response it cares about.
 */
final class FakeEngineClient implements EngineClient
{
    public function __construct(
        private readonly ?EngineResponse $search = null,
        private readonly ?EngineResponse $generate = null,
        private readonly ?EngineResponse $transcribe = null,
        private readonly ?EngineResponse $chat = null,
        private readonly ?EngineResponse $book = null,
    ) {}

    public function search(EngineRequest $request): EngineResponse
    {
        return $this->search ?? new EngineResponse(ok: true, action: 'search');
    }

    public function generate(EngineRequest $request): EngineResponse
    {
        return $this->generate ?? new EngineResponse(ok: true, action: 'generate');
    }

    public function transcribe(EngineRequest $request): EngineResponse
    {
        return $this->transcribe ?? new EngineResponse(ok: true, action: 'transcribe');
    }

    public function chat(EngineRequest $request): EngineResponse
    {
        return $this->chat ?? new EngineResponse(ok: true, action: 'chat');
    }

    public function book(EngineRequest $request): EngineResponse
    {
        return $this->book ?? new EngineResponse(ok: true, action: 'book');
    }
}
