<?php

use App\Engine\Dto\EngineRequest;
use App\Engine\StubEngineClient;
use Opis\JsonSchema\Errors\ErrorFormatter;
use Opis\JsonSchema\Validator;

it('returns a contract-valid transcribe response', function () {
    $client = new StubEngineClient();

    $response = $client->transcribe(new EngineRequest(
        action: 'transcribe',
        selection: ['output/agujeros_negros_2026-06-20.mp3'],
    ));

    expect($response->ok)->toBeTrue();
    expect($response->action)->toBe('transcribe');
    expect($response->version)->toBe('1.0');
    expect($response->transcripts)->not->toBeEmpty();

    $schema = file_get_contents(base_path('../contract/schema/response.transcribe.schema.json'));
    $data = json_decode(json_encode($response->toArray()));

    $result = (new Validator())->validate($data, $schema);

    $errorMsg = $result->isValid() ? '' : json_encode((new ErrorFormatter())->format($result->error()));
    expect($result->isValid())->toBeTrue($errorMsg);
});
