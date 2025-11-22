<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { AppBar } from '@skeletonlabs/skeleton-svelte';
	import { Building2, MenuIcon, CircleSmall } from 'lucide-svelte';
	import { page } from '$app/state';
	import { mockPages } from '$lib/pages';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#snippet link(name: string, url: string)}
	<li>
		<a class="flex flex-row hover:*:first:block" href={url}>
			{#if url === page.url.href}
				<CircleSmall />
			{:else}
				<CircleSmall class="hidden" />
			{/if}
		</a>
	</li>
{/snippet}

{#snippet navigation()}
	<ol>
		{@render link('Home', '/')}
	</ol>
	<hr class="hr" />
	<ol>
		{#each mockPages as mockPage, i}
			{@render link(mockPage.header, `/${i}`)}
		{/each}
	</ol>
{/snippet}

<div id="nav__popover" popover="auto" class="top-10 w-fit">
	{@render navigation()}
</div>

<AppBar>
	<AppBar.Toolbar class="flex flex-row">
		<AppBar.Lead>
			<a href="/" class="btn-icon btn-icon-lg hover:preset-tonal"><Building2 /></a>
		</AppBar.Lead>
		<AppBar.Headline class="h3 mr-auto">BecomingMünchner</AppBar.Headline>
		<AppBar.Trail>
			<button
				type="button"
				class="btn-icon btn-icon-lg md:hidden"
				id="nav-toggle"
				popovertarget="nav__popover"
			>
				<MenuIcon />
			</button>
		</AppBar.Trail>
	</AppBar.Toolbar>
</AppBar>

<div class="max-w-xl mx-auto">
	<div class="px-2 py-4">
		{@render children()}
	</div>
</div>
