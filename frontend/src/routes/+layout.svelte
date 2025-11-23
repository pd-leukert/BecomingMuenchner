<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { AppBar, SegmentedControl } from '@skeletonlabs/skeleton-svelte';
	import { Building2, MenuIcon, UserRound } from 'lucide-svelte';
	import { mockPages } from '$lib/mockPages';
	import { resolve } from '$app/paths';
	import { getApplicationId, setApplicationId } from '$lib/applicationId.svelte';
	import { goto } from '$app/navigation';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#snippet link(name: string, url: string)}
	<SegmentedControl.Item value={url}>
		<SegmentedControl.ItemText>{name}</SegmentedControl.ItemText>
		<SegmentedControl.ItemHiddenInput />
	</SegmentedControl.Item>
{/snippet}

{#snippet navigation()}
	<SegmentedControl.Control>
		<SegmentedControl.Indicator />
		{@render link('Home', '/')}
		{#each mockPages as mockPage, i (i)}
			{@render link(mockPage.header, `/naturalization/${i}`)}
		{/each}
		{@render link('Überprüfung', '/naturalization/check')}
	</SegmentedControl.Control>
{/snippet}

<div id="nav__popover" popover="auto" class="top-24 left-auto right-2">
	<SegmentedControl
		orientation="vertical"
		value={getApplicationId()}
		onValueChange={({ value }) => goto(value ?? '/')}
		class="min-w-36"
	>
		{@render navigation()}
	</SegmentedControl>
</div>

<div id="id-popover" popover="auto" class="top-24 left-auto right-2">
	<SegmentedControl
		orientation="vertical"
		value={getApplicationId()}
		onValueChange={({ value }) => setApplicationId(value ?? getApplicationId())}
		class="min-w-36"
	>
		<SegmentedControl.Control>
			<SegmentedControl.Indicator />
			<SegmentedControl.Item value="1">
				<SegmentedControl.ItemText>1</SegmentedControl.ItemText>
				<SegmentedControl.ItemHiddenInput />
			</SegmentedControl.Item>
			<SegmentedControl.Item value="2">
				<SegmentedControl.ItemText>2</SegmentedControl.ItemText>
				<SegmentedControl.ItemHiddenInput />
			</SegmentedControl.Item>
			<SegmentedControl.Item value="3">
				<SegmentedControl.ItemText>3</SegmentedControl.ItemText>
				<SegmentedControl.ItemHiddenInput />
			</SegmentedControl.Item>
		</SegmentedControl.Control>
	</SegmentedControl>
</div>

<AppBar>
	<AppBar.Toolbar class="flex flex-row">
		<AppBar.Lead>
			<a href={resolve('/')} class="btn-icon btn-icon-lg hover:preset-tonal"><Building2 /></a>
		</AppBar.Lead>
		<AppBar.Headline class="h3 mr-auto">BecomingMünchner</AppBar.Headline>
		<AppBar.Trail>
			<button type="button" class="btn-icon btn-icon-lg" id="nav-toggle" popovertarget="id-popover">
				<UserRound />
			</button>
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
	<SegmentedControl
		orientation="vertical"
		value={getApplicationId()}
		onValueChange={({ value }) => goto(value ?? '/')}
		class="min-w-36"
	>
		{@render navigation()}
	</SegmentedControl>
</aside>

<div class="max-w-xl mx-auto">
	<div class="p-4">
		{@render children()}
	</div>
</div>
