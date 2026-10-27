<?php

use App\Engine\Dto\EngineRequest;
use App\Engine\StubEngineClient;
use Opis\JsonSchema\Validator;
use Opis\JsonSchema\Errors\ErrorFormatter;

it('returns a contract-valid search response', function () {
    $client = new StubEngineClient();

    $response = $client->search(new EngineRequest(action: 'search', query: 'marte'));

    expect($response->ok)->toBeTrue();
    expect($response->action)->toBe('search');
    expect($response->version)->toBe('1.0');
    expect($response->fragments)->not->toBeEmpty();

    // Validate the serialised response against the frozen contract schema.
    $schema = file_get_contents(base_path('../contract/schema/response.search.schema.json'));
    $data = json_decode(json_encode($response->toArray()));

    $result = (new Validator())->validate($data, $schema);

    $errorMsg = $result->isValid() ? '' : json_encode((new ErrorFormatter())->format($result->error()));
    expect($result->isValid())->toBeTrue($errorMsg);
});
