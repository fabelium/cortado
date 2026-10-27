<?php

use App\Engine\Dto\EngineRequest;
use App\Http\Requests\TranscribeRequest;
use Opis\JsonSchema\Errors\ErrorFormatter;
use Opis\JsonSchema\Validator;

it('maps validated input to a v1.0 transcribe EngineRequest', function () {
    $request = TranscribeRequest::create('/api/transcribe', 'POST', [
        'selection' => ['output/agujeros_negros_2026-06-20.mp3'],
    ]);
    $request->setContainer(app())->validateResolved();

    $engineRequest = $request->toEngineRequest();

    expect($engineRequest)->toBeInstanceOf(EngineRequest::class);
    expect($engineRequest->version)->toBe('1.0');
    expect($engineRequest->action)->toBe('transcribe');
    expect($engineRequest->query)->toBeNull();
    expect($engineRequest->selection)->toBe(['output/agujeros_negros_2026-06-20.mp3']);
    expect($engineRequest->options)->toBe([]);
});

it('produces an EngineRequest that satisfies the engine request contract', function () {
    $request = TranscribeRequest::create('/api/transcribe', 'POST', [
        'selection' => ['output/a.mp3', 'output/b.mp3'],
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
