<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Http\Requests\RegisterRequest;
use App\Models\User;
use Illuminate\Http\JsonResponse;

/**
 * Registers a user and returns a ready-to-use Bearer token, so a fresh client
 * can authenticate immediately without a separate login round-trip.
 */
class RegisterController extends Controller
{
    public function __invoke(RegisterRequest $request): JsonResponse
    {
        $user = User::create([
            'name' => $request->validated('name'),
            'email' => $request->validated('email'),
            'password' => $request->validated('password'), // hashed by the model cast
        ]);

        $device = $request->validated('device_name') ?? 'default';

        return response()->json([
            'token' => $user->createToken($device)->plainTextToken,
        ], 201);
    }
}
