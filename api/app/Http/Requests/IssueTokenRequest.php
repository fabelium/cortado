<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class IssueTokenRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true; // issuing a token is the entry point; creds are checked in the controller
    }

    public function rules(): array
    {
        return [
            'email' => ['required', 'email'],
            'password' => ['required', 'string'],
            'device_name' => ['required', 'string', 'max:255'],
        ];
    }
}
