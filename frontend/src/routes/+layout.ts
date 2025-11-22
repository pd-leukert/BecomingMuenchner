import type { LayoutLoad } from '../../.svelte-kit/types/src/routes/$types';

export const load: LayoutLoad = () => {
	return {
		pageContent: {
			header: '',
			type: 'mock',
			sections: []
		},
		pageId: 0
	};
};
