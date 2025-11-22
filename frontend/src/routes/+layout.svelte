<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { AppBar, Navigation } from '@skeletonlabs/skeleton-svelte';
	import { Building2, MenuIcon, CircleSmall } from 'lucide-svelte';
	import { page } from '$app/state';
	import { mockPages } from '$lib/mockPages';
	import { resolve } from '$app/paths';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#snippet link(name: string, url: string)}
	<Navigation.Menu>
		<a class="flex flex-row hover:*:first:visible w-full py-2" href={url}>
			{#if url === page.url.pathname}
				<CircleSmall />
			{:else}
				<CircleSmall class="invisible" />
			{/if}
			{name}
		</a>
	</Navigation.Menu>
{/snippet}

{#snippet navigation()}
	<Navigation.Content>
		<Navigation.Group>
			{@render link('Home', '/')}
		</Navigation.Group>
		{#if page.url.pathname !== '/'}
			<Navigation.Group>
				{#each mockPages as mockPage, i (i)}
					{@render link(mockPage.header, `/naturalization/${i}`)}
				{/each}
				{@render link('Überprüfung', '/naturalization/check')}
			</Navigation.Group>
		{/if}
	</Navigation.Content>
{/snippet}

<div id="nav__popover" popover="auto" class="top-24 left-auto right-2">
	<Navigation>
		{@render navigation()}
	</Navigation>
</div>

<AppBar>
	<AppBar.Toolbar class="flex flex-row">
		<AppBar.Lead>
			<a href={resolve('/')} class="btn-icon btn-icon-lg hover:preset-tonal"><Building2 /></a>
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

<aside class="not-md:hidden left-4 right-2 top-24 fixed w-100">
	<Navigation layout="sidebar">
		{@render navigation()}
	</Navigation>
</aside>

<div class="max-w-xl mx-auto">
	<div class="px-2 py-4">
		{@render children()}
	</div>
</div>
