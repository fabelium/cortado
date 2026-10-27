<?php

use App\Http\Controllers\Auth\LoginController;
use App\Http\Controllers\Auth\LogoutController;
use App\Http\Controllers\Auth\RegisterController;
use App\Http\Controllers\Auth\TokenController;
use App\Http\Controllers\BookController;
use App\Http\Controllers\ChatController;
use App\Http\Controllers\GenerateController;
use App\Http\Controllers\JobController;
use App\Http\Controllers\SearchController;
use App\Http\Controllers\TranscribeController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

// Auth. SPA cookie flow: GET /sanctum/csrf-cookie then POST /login (session).
// Programmatic clients: POST /register or POST /tokens for a Bearer token.
// Unauthenticated credential endpoints are throttled against brute force.
Route::post('/register', RegisterController::class)->middleware('throttle:5,1');
Route::post('/login', LoginController::class)->middleware('throttle:5,1');
Route::post('/tokens', TokenController::class)->middleware('throttle:5,1');
Route::post('/logout', LogoutController::class)->middleware('auth:sanctum');

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');

Route::post('/search', SearchController::class)->middleware('auth:sanctum');
Route::post('/generate', GenerateController::class)->middleware('auth:sanctum');
Route::post('/transcribe', TranscribeController::class)->middleware('auth:sanctum');
Route::post('/chat', ChatController::class)->middleware('auth:sanctum');
Route::post('/book', BookController::class)->middleware('auth:sanctum');
Route::get('/jobs/{id}', JobController::class)->middleware('auth:sanctum');
