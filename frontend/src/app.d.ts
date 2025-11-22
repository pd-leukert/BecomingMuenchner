// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
import type { PageContent } from '$lib/types';

declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		interface PageData {
			pageContent: PageContent;
		}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
