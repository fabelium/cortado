<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Http\Requests\IssueTokenRequest;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

/**
 * Issues a Sanctum personal access token for API clients (curl, Postman, native
 * apps) that authenticate with a Bearer token rather than the SPA cookie flow.
 */
class TokenController extends Controller
{
    public function __invoke(IssueTokenRequest $request): JsonResponse
    {
        $user = User::where('email', $request->validated('email'))->first();

        if (! $user || ! Hash::check($request->validated('password'), $user->password)) {
            throw ValidationException::withMessages([
                'email' => [__('auth.failed')],
            ]);
        }

        return response()->json([
            'token' => $user->createToken($request->validated('device_name'))->plainTextToken,
        ]);
    }
}
