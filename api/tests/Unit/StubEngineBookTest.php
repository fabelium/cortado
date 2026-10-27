<?php

use App\Engine\Dto\EngineRequest;
use App\Engine\StubEngineClient;
use Opis\JsonSchema\Errors\ErrorFormatter;
use Opis\JsonSchema\Validator;

it('returns a contract-valid book response', function () {
    $client = new StubEngineClient();

    $response = $client->book(new EngineRequest(
        action: 'book',
        query: 'Marte',
        options: ['formats' => ['pdf', 'epub']],
        selection: ['ep237@300-480'],
    ));

    expect($response->ok)->toBeTrue();
    expect($response->action)->toBe('book');
    expect($response->version)->toBe('1.0');
    expect($response->artifacts)->not->toBeEmpty();
    // Markdown is always produced; requested formats ride along.
    $formats = array_column($response->artifacts, 'format');
    expect($formats)->toContain('markdown');
    expect($formats)->toContain('pdf');
    expect($formats)->toContain('epub');

    $schema = file_get_contents(base_path('../contract/schema/response.book.schema.json'));
    $data = json_decode(json_encode($response->toArray()));

    $result = (new Validator())->validate($data, $schema);

    $errorMsg = $result->isValid() ? '' : json_encode((new ErrorFormatter())->format($result->error()));
    expect($result->isValid())->toBeTrue($errorMsg);
});
