import type { PageLoad } from '../../../.svelte-kit/types/src/routes/[pageId]/$types';
import { checkPage, mockPages } from '$lib/pages';
import { error } from '@sveltejs/kit';

export const load: PageLoad = ({ params: { pageId } }) => {
	const pageIdNum = Number.parseInt(pageId);
	if (pageIdNum > mockPages.length) {
		error(404);
	}
	if (pageIdNum === mockPages.length) {
		return { pageContent: checkPage, pageId: pageIdNum };
	}

	return { pageContent: mockPages[pageIdNum], pageId: pageIdNum };
};
