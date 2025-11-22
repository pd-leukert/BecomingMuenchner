import type { LayoutLoad } from '../../.svelte-kit/types/src/routes/$types';

const load: LayoutLoad = () => {
	return {
		pageContent: {
			header: '',
			type: 'mock',
			sections: []
		},
		pageId: 0
	};
};
