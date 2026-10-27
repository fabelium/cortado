<?php

use App\Engine\Dto\EngineRequest;
use App\Http\Requests\GenerateRequest;
use Opis\JsonSchema\Errors\ErrorFormatter;
use Opis\JsonSchema\Validator;

it('maps validated input to a v1.0 generate EngineRequest', function () {
    // The public body nests audio options under `options`, mirroring the
    // engine contract (and what the Nuxt client sends).
    $request = GenerateRequest::create('/api/generate', 'POST', [
        'query' => 'agujeros negros',
        'selection' => ['ep237@2340-2880'],
        'options' => [
            'intro' => true,
            'disclaimer' => true,
            'split' => 30,
        ],
    ]);
    $request->setContainer(app())->validateResolved();

    $engineRequest = $request->toEngineRequest();

    expect($engineRequest)->toBeInstanceOf(EngineRequest::class);
    expect($engineRequest->version)->toBe('1.0');
    expect($engineRequest->action)->toBe('generate');
    expect($engineRequest->query)->toBe('agujeros negros');
    expect($engineRequest->selection)->toBe(['ep237@2340-2880']);
    expect($engineRequest->options)->toBe([
        'intro' => true,
        'disclaimer' => true,
        'split' => 30,
    ]);
});

it('casts option types so they honour the contract (string input)', function () {
    // Form-encoded / non-JSON clients deliver scalars as strings.
    $request = GenerateRequest::create('/api/generate', 'POST', [
        'query' => 'marte',
        'selection' => ['ep1@0-60'],
        'options' => [
            'intro' => '1',
            'disclaimer' => '0',
            'split' => '15',
        ],
    ]);
    $request->setContainer(app())->validateResolved();

    $options = $request->toEngineRequest()->options;

    expect($options['intro'])->toBeTrue();
    expect($options['disclaimer'])->toBeFalse();
    expect($options['split'])->toBe(15);
});

it('omits options entirely when the body carries none', function () {
    $request = GenerateRequest::create('/api/generate', 'POST', [
        'query' => 'marte',
        'selection' => ['ep1@0-60'],
    ]);
    $request->setContainer(app())->validateResolved();

    expect($request->toEngineRequest()->options)->toBe([]);
});

it('produces an EngineRequest that satisfies the engine request contract', function () {
    $request = GenerateRequest::create('/api/generate', 'POST', [
        'query' => 'marte',
        'selection' => ['ep1@0-60', 'ep2@120-180'],
        'options' => [
            'intro' => '1',
            'disclaimer' => '1',
            'split' => '30',
        ],
    ]);
    $request->setContainer(app())->validateResolved();

    $data = json_decode(json_encode($request->toEngineRequest()->toArray()));
    $schema = file_get_contents(base_path('../contract/schema/request.schema.json'));

    $result = (new Validator())->validate($data, $schema);

    $errors = $result->isValid()
        ? ''
        : json_encode((new ErrorFormatter())->format($result->error()));

    expect($result->isValid())->toBeTrue($errors);
});
