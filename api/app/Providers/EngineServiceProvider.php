<?php

namespace App\Providers;

use App\Engine\EngineClient;
use App\Engine\StubEngineClient;
use App\Engine\SubprocessEngineClient;
use Illuminate\Support\ServiceProvider;

class EngineServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->bind(EngineClient::class, function ($app) {
            if ($app['config']->get('engine.driver') === 'subprocess') {
                return new SubprocessEngineClient(
                    command: $app['config']->get('engine.command'),
                    cwd: $app['config']->get('engine.cwd'),
                    timeout: (int) $app['config']->get('engine.timeout'),
                );
            }

            return new StubEngineClient();
        });
    }
}
