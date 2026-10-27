<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Http\Requests\LoginRequest;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Auth;
use Illuminate\Validation\ValidationException;

/**
 * SPA cookie/session login. Pair with GET /sanctum/csrf-cookie: the SPA fetches
 * the CSRF cookie, posts here, and the session cookie authenticates subsequent
 * stateful requests. Token clients use POST /api/tokens instead.
 */
class LoginController extends Controller
{
    public function __invoke(LoginRequest $request): Response
    {
        if (! Auth::attempt($request->validated())) {
            throw ValidationException::withMessages([
                'email' => [__('auth.failed')],
            ]);
        }

        $request->session()->regenerate();

        return response()->noContent();
    }
}
