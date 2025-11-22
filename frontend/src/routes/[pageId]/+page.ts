import type { PageLoad } from '../../../.svelte-kit/types/src/routes/[pageId]/$types';
import { checkPage, mockPages } from '$lib/pages';
import { error } from '@sveltejs/kit';

export const load: PageLoad = ({ params: { pageId } }) => {
	const pageIdStr = Number.parseInt(pageId);
	if (pageIdStr > mockPages.length) {
		error(404);
	}
	if (pageIdStr === mockPages.length) {
		return { pageContent: checkPage };
	}

	return { pageContent: mockPages[pageIdStr] };
};
