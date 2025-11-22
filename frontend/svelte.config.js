// svelte.config.js
import adapter from '@sveltejs/adapter-node'; // Oder adapter-auto / adapter-static
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
    // ... deine settings
    preprocess: vitePreprocess(),
    kit: {
        adapter: adapter()
    }
};

export default config;