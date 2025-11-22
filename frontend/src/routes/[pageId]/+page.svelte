<script>
	import { page } from '$app/state';
	import MockPage from './MockPage.svelte';
	import CheckPage from './CheckPage.svelte';

	const pageContent = page.data.pageContent;
</script>

{#if pageContent.type === 'mock'}
	<MockPage {pageContent} />
{:else}
	<CheckPage {pageContent} />
{/if}
