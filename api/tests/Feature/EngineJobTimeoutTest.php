<?php

use App\Engine\Dto\EngineRequest;
use App\Engine\EngineClient;
use App\Jobs\RunEngineJob;
use App\Models\EngineJob;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Process\PendingProcess;
use Illuminate\Support\Facades\Process;

uses(RefreshDatabase::class);

function queuedEngineJob(): EngineJob
{
    return EngineJob::create([
        'user_id' => User::factory()->create()->id,
        'action' => 'generate',
        'status' => 'queued',
        'payload' => ['action' => 'generate', 'query' => 'marte', 'selection' => ['ep1@0-60']],
    ]);
}

it('defaults the job timeout to 30 minutes, apart from the 2 minute sync one', function () {
    expect(config('engine.timeout'))->toBe(120);
    expect(config('engine.job_timeout'))->toBe(1800);
});

it('gives the queue worker headroom over the engine job timeout', function () {
    config()->set('engine.job_timeout', 900);

    expect((new RunEngineJob(queuedEngineJob()))->timeout)->toBe(960);
});

it('runs queued jobs with the job timeout, not the sync one', function () {
    config()->set('engine.driver', 'subprocess');
    config()->set('engine.timeout', 120);
    config()->set('engine.job_timeout', 900);
    Process::fake();

    $job = new RunEngineJob(queuedEngineJob());
    $job->handle(app(EngineClient::class));

    Process::assertRan(fn (PendingProcess $process) => $process->timeout === 900);
});

it('keeps the sync timeout for request-time engine calls', function () {
    config()->set('engine.driver', 'subprocess');
    config()->set('engine.timeout', 120);
    config()->set('engine.job_timeout', 900);
    Process::fake();

    app(EngineClient::class)->search(
        new EngineRequest(action: 'search', query: 'marte'),
    );

    Process::assertRan(fn (PendingProcess $process) => $process->timeout === 120);
});

it('keeps the database queue from re-reserving a job that is still running', function () {
    // retry_after must outlast the longest job, or a second worker picks the
    // job up mid-run and fails it with MaxAttemptsExceeded.
    expect(config('queue.connections.database.retry_after'))
        ->toBeGreaterThan(config('engine.job_timeout') + 60);
});

it('applies the same retry_after protection to the redis and beanstalkd queues', function () {
    foreach (['redis', 'beanstalkd'] as $connection) {
        expect(config("queue.connections.{$connection}.retry_after"))
            ->toBeGreaterThan(config('engine.job_timeout') + 60);
    }
});
