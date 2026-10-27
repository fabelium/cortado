<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

/**
 * One queued engine run (generate / transcribe / book). `payload` holds the
 * contract EngineRequest; `result` the contract success response once done.
 * Status: queued → running → done | failed.
 */
class EngineJob extends Model
{
    use HasUuids;

    protected $fillable = [
        'user_id',
        'action',
        'status',
        'payload',
        'result',
        'error',
        'code',
    ];

    protected function casts(): array
    {
        return [
            'payload' => 'array',
            'result' => 'array',
        ];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
