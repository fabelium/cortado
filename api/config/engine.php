<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Engine driver
    |--------------------------------------------------------------------------
    |
    | Which EngineClient backs the API. `subprocess` (default) runs the real
    | Python engine (engine/engine.py) over stdin/stdout. `stub` returns fixed
    | contract-shaped payloads — set it if you have no Python/engine locally;
    | the test suite forces it via phpunit.xml.
    |
    */

    'driver' => env('ENGINE_DRIVER', 'subprocess'),

    /*
    | Base command for the subprocess driver, plus working directory and a hard
    | timeout (seconds) for a single engine run made while serving a request
    | (search, chat). Queued jobs (generate / transcribe / book) download and
    | transcode audio, so they get their own, much longer `job_timeout`.
    */

    'command' => [
        env('ENGINE_PYTHON', 'python3'),
        env('ENGINE_SCRIPT', base_path('../engine/engine.py')),
    ],

    'cwd' => env('ENGINE_CWD', base_path('../engine')),

    'timeout' => (int) env('ENGINE_TIMEOUT', 120),

    'job_timeout' => (int) env('ENGINE_JOB_TIMEOUT', 1800),

];
