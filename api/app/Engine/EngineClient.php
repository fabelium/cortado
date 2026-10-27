<?php

namespace App\Engine;

use App\Engine\Dto\EngineRequest;
use App\Engine\Dto\EngineResponse;

interface EngineClient
{
    public function search(EngineRequest $request): EngineResponse;

    public function generate(EngineRequest $request): EngineResponse;

    public function transcribe(EngineRequest $request): EngineResponse;

    public function chat(EngineRequest $request): EngineResponse;

    public function book(EngineRequest $request): EngineResponse;
}
