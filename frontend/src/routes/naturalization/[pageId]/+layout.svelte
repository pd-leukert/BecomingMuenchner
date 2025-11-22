<script lang="ts">
	import { page } from '$app/state';
	import { ArrowLeft, ArrowRight } from 'lucide-svelte';
	import { mockPages } from '$lib/mockPages';
	import { resolve } from '$app/paths';

	let { children } = $props();
	const pageId = $derived(page.data.pageId);
</script>

{@render children()}
<section class="btn-group w-full">
	{#if pageId > 0}
		<a class="btn flex w-full" href={resolve(`/naturalization/${pageId - 1}/`)}>
			<ArrowLeft />
			<span>Zurück</span>
		</a>
	{/if}
	{#if pageId < mockPages.length - 1}
		<a class="btn flex w-full" href={resolve(`/naturalization/${pageId + 1}/`)}>
			<span>Weiter</span>
			<ArrowRight />
		</a>
	{/if}
	{#if pageId === mockPages.length - 1}
		<a class="btn flex w-full" href={resolve('/naturalization/check/')}>
			<span>Continue with check</span>
			<ArrowRight />
		</a>
	{/if}
</section>
