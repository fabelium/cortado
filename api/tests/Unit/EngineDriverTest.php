<?php

use App\Engine\EngineClient;
use App\Engine\StubEngineClient;
use App\Engine\SubprocessEngineClient;

it('resolves the stub client when the driver is stub', function () {
    config()->set('engine.driver', 'stub');

    expect(app(EngineClient::class))->toBeInstanceOf(StubEngineClient::class);
});

it('resolves the subprocess client when the driver is subprocess', function () {
    config()->set('engine.driver', 'subprocess');
    config()->set('engine.command', ['php', base_path('tests/Fixtures/fake-engine.php'), 'ok']);

    expect(app(EngineClient::class))->toBeInstanceOf(SubprocessEngineClient::class);
});
