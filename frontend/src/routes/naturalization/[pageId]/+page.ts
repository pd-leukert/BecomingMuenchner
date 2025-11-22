import type { PageLoad } from '../../../../.svelte-kit/types/src/routes/[pageId]/$types';
import { mockPages } from '$lib/mockPages';
import { error } from '@sveltejs/kit';

export const load: PageLoad = ({ params: { pageId } }) => {
	const pageIdNum = Number.parseInt(pageId);
	if (pageIdNum >= mockPages.length || pageIdNum < 0) {
		error(404);
	}

	return { pageContent: mockPages[pageIdNum], pageId: pageIdNum };
};
