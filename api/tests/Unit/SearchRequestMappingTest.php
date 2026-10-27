<?php

use App\Engine\Dto\EngineRequest;
use App\Http\Requests\SearchRequest;
use Opis\JsonSchema\Errors\ErrorFormatter;
use Opis\JsonSchema\Validator;

it('maps validated input to a v1.0 search EngineRequest', function () {
    $request = SearchRequest::create('/api/search', 'POST', [
        'query' => 'marte',
        'semantic' => true,
        'model' => 'local',
        'limit' => 5,
    ]);
    // Simulate validation having populated the request.
    $request->setContainer(app())->validateResolved();

    $engineRequest = $request->toEngineRequest();

    expect($engineRequest)->toBeInstanceOf(EngineRequest::class);
    expect($engineRequest->version)->toBe('1.0');
    expect($engineRequest->action)->toBe('search');
    expect($engineRequest->query)->toBe('marte');
    expect($engineRequest->options)->toBe([
        'semantic' => true,
        'model' => 'local',
        'limit' => 5,
    ]);
});

it('maps and casts the top_k and threshold tuning options', function () {
    $request = SearchRequest::create('/api/search', 'POST', [
        'query' => 'marte',
        'top_k' => '8',
        'threshold' => '0.45',
    ]);
    $request->setContainer(app())->validateResolved();

    $options = $request->toEngineRequest()->options;

    expect($options['top_k'])->toBe(8);
    expect($options['threshold'])->toBe(0.45);
});

it('casts option types so they honour the contract (string input)', function () {
    // Form-encoded / non-JSON clients deliver scalars as strings.
    $request = SearchRequest::create('/api/search', 'POST', [
        'query' => 'marte',
        'semantic' => '1',
        'classify' => '0',
        'limit' => '5',
    ]);
    $request->setContainer(app())->validateResolved();

    $options = $request->toEngineRequest()->options;

    expect($options['semantic'])->toBeTrue();
    expect($options['classify'])->toBeFalse();
    expect($options['limit'])->toBe(5);
});

it('produces an EngineRequest that satisfies the engine request contract', function () {
    $request = SearchRequest::create('/api/search', 'POST', [
        'query' => 'marte',
        'semantic' => '1',
        'classify' => '0',
        'model' => 'local',
        'limit' => '5',
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
