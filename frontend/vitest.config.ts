import { defineConfig } from 'vitest/config'
import { fileURLToPath, URL } from 'node:url'

// Config de test isolée : les mappers sont des fonctions pures (aucun runtime Vue),
// donc environnement `node` suffit. L'alias `@` est rejoué pour les imports de types.
export default defineConfig({
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
