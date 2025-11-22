<script lang="ts">
	import { page } from '$app/state';
	import { ArrowLeft, ArrowRight } from 'lucide-svelte';
	import { mockPages } from '$lib/pages';

	let { children } = $props();
	const pageId = $derived(page.data.pageId);
</script>

{@render children()}
<section class="btn-group w-full">
	{#if pageId > 0}
		<a class="btn btn-icon flex w-full" href="/{pageId - 1}">
			<ArrowLeft />
			<span>Zurück</span>
		</a>
	{/if}
	{#if pageId < mockPages.length}
		<a class="btn btn-icon flex w-full" href="/{pageId + 1}">
			<span class="btn-icon">Weiter</span>
			<ArrowRight />
		</a>
	{/if}
</section>
