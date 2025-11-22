// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
import type { MockPageContent } from '$lib/types';

declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		interface PageData {
			pageContent: MockPageContent;
			pageId: number;
		}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
