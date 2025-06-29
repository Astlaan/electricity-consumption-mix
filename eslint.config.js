// frontend/eslint.config.js
import js from "@eslint/js";
import svelte from "eslint-plugin-svelte";
import prettier from "eslint-config-prettier";
import tseslint from 'typescript-eslint';

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...svelte.configs["flat/recommended"],
  prettier, // Make sure Prettier is last to override other formatting rules
  {
    files: ["**/*.svelte"],
    languageOptions: {
      globals: {
        browser: true,
        node: true, // Add node globals as well, useful for SvelteKit
      },
      // Svelte files are handled by eslint-plugin-svelte's recommended config
      // which should correctly set up the parser for .svelte files.
    }
  },
  {
    // General TypeScript files (not .svelte)
    files: ["**/*.ts"],
    languageOptions: {
      globals: {
        node: true, // For .ts files that might be server-side
        browser: true, // If some .ts files are client-side utilities
      }
    }
  },
  {
    ignores: [
      "build/",
      ".svelte-kit/",
      "dist/",
      "node_modules/",
      "*.config.js", // Ignores this file itself and vite.config.js, svelte.config.js etc.
      "*.config.cjs"
    ],
  }
];
