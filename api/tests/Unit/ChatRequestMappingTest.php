<?php

use App\Engine\Dto\EngineRequest;
use App\Http\Requests\ChatRequest;
use Opis\JsonSchema\Errors\ErrorFormatter;
use Opis\JsonSchema\Validator;

it('maps validated input to a v1.0 chat EngineRequest', function () {
    $request = ChatRequest::create('/api/chat', 'POST', [
        'query' => '¿Cuándo aterrizó la sonda Insight en Marte?',
        'selection' => ['ep237@300-480'],
    ]);
    $request->setContainer(app())->validateResolved();

    $engineRequest = $request->toEngineRequest();

    expect($engineRequest)->toBeInstanceOf(EngineRequest::class);
    expect($engineRequest->version)->toBe('1.0');
    expect($engineRequest->action)->toBe('chat');
    expect($engineRequest->query)->toBe('¿Cuándo aterrizó la sonda Insight en Marte?');
    expect($engineRequest->selection)->toBe(['ep237@300-480']);
    expect($engineRequest->options)->toBe([]);
});

it('produces an EngineRequest that satisfies the engine request contract', function () {
    $request = ChatRequest::create('/api/chat', 'POST', [
        'query' => 'marte',
        'selection' => ['ep1@0-60', 'ep2@120-180'],
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
