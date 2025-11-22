import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
	input: '../openapi.yaml', // sign up at app.heyapi.dev
	output: 'src/lib/client'
});
