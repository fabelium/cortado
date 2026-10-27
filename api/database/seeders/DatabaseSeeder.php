<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    use WithoutModelEvents;

    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // The demo password is public (root README), so never create it in production.
        if (app()->isProduction()) {
            return;
        }

        // Demo account for reviewers (credentials documented in the root README).
        // Idempotent and non-destructive: re-seeding neither duplicates the user
        // nor resets a password its owner changed.
        User::firstOrCreate(
            ['email' => 'evaluador@cortado.test'],
            ['name' => 'Evaluador', 'password' => 'Cortado-2026!'],
        );
    }
}
