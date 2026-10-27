<?php

use App\Engine\Dto\EngineRequest;
use App\Http\Requests\BookRequest;
use Opis\JsonSchema\Errors\ErrorFormatter;
use Opis\JsonSchema\Validator;

it('maps validated input to a v1.0 book EngineRequest', function () {
    $request = BookRequest::create('/api/book', 'POST', [
        'query' => 'Marte',
        'selection' => ['ep237@300-480', 'ep305@120-300'],
        'options' => ['formats' => ['pdf', 'epub']],
    ]);
    $request->setContainer(app())->validateResolved();

    $engineRequest = $request->toEngineRequest();

    expect($engineRequest)->toBeInstanceOf(EngineRequest::class);
    expect($engineRequest->version)->toBe('1.0');
    expect($engineRequest->action)->toBe('book');
    expect($engineRequest->query)->toBe('Marte');
    expect($engineRequest->selection)->toBe(['ep237@300-480', 'ep305@120-300']);
    expect($engineRequest->options)->toBe(['formats' => ['pdf', 'epub']]);
});

it('omits options when no formats are requested', function () {
    $request = BookRequest::create('/api/book', 'POST', [
        'query' => 'marte',
        'selection' => ['ep1@0-60'],
    ]);
    $request->setContainer(app())->validateResolved();

    expect($request->toEngineRequest()->options)->toBe([]);
});

it('produces an EngineRequest that satisfies the engine request contract', function () {
    $request = BookRequest::create('/api/book', 'POST', [
        'query' => 'marte',
        'selection' => ['ep1@0-60'],
        'options' => ['formats' => ['pdf']],
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
