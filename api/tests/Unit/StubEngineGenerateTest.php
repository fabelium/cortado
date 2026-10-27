<?php

use App\Engine\Dto\EngineRequest;
use App\Engine\StubEngineClient;
use Opis\JsonSchema\Errors\ErrorFormatter;
use Opis\JsonSchema\Validator;

it('returns a contract-valid generate response', function () {
    $client = new StubEngineClient();

    $response = $client->generate(new EngineRequest(
        action: 'generate',
        query: 'agujeros negros',
        options: ['intro' => true, 'disclaimer' => true, 'split' => 30],
    ));

    expect($response->ok)->toBeTrue();
    expect($response->action)->toBe('generate');
    expect($response->version)->toBe('1.0');
    expect($response->artifacts)->not->toBeEmpty();

    $schema = file_get_contents(base_path('../contract/schema/response.generate.schema.json'));
    $data = json_decode(json_encode($response->toArray()));

    $result = (new Validator())->validate($data, $schema);

    $errorMsg = $result->isValid() ? '' : json_encode((new ErrorFormatter())->format($result->error()));
    expect($result->isValid())->toBeTrue($errorMsg);
});
