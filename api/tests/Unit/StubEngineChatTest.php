<?php

use App\Engine\Dto\EngineRequest;
use App\Engine\StubEngineClient;
use Opis\JsonSchema\Errors\ErrorFormatter;
use Opis\JsonSchema\Validator;

it('returns a contract-valid chat response', function () {
    $client = new StubEngineClient();

    $response = $client->chat(new EngineRequest(
        action: 'chat',
        query: '¿Cuándo aterrizó la sonda Insight en Marte?',
        selection: ['ep237@300-480'],
    ));

    expect($response->ok)->toBeTrue();
    expect($response->action)->toBe('chat');
    expect($response->version)->toBe('1.0');
    expect($response->answer)->not->toBeEmpty();
    expect($response->sources)->not->toBeEmpty();

    $schema = file_get_contents(base_path('../contract/schema/response.chat.schema.json'));
    $data = json_decode(json_encode($response->toArray()));

    $result = (new Validator())->validate($data, $schema);

    $errorMsg = $result->isValid() ? '' : json_encode((new ErrorFormatter())->format($result->error()));
    expect($result->isValid())->toBeTrue($errorMsg);
});
