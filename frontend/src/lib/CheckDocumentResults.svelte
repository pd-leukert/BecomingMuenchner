<script lang="ts">
	import type { CheckResult } from '$lib/client';
	import { parseStatus } from '$lib/statusParser';

	type Props = {
		checks: Omit<CheckResult, 'documentTitle'>[];
		documentUrl?: string;
	};

	const { checks, documentUrl }: Props = $props();

	// preset-tonal-error preset-tonal-warning preset-tonal-success preset-tonal-secondary
</script>

<ul class="ml-2 flex flex-col gap-1">
	{#each checks as checkResult, i (i)}
		{@const { Icon, tailwindString } = parseStatus(checkResult.status)}
		<li
			class="preset-tonal-{tailwindString} color px-4 py-4 gap-2 flex flex-col base-font-color dark:base-font-color-dark"
		>
			<header>
				<span class="items-center flex h4 gap-2 font-bold">
					<Icon class="inline" />
					{checkResult.checkDisplayTitle}
				</span>
			</header>
			<span>{checkResult.message}</span>
		</li>
	{/each}
</ul>

{#if documentUrl !== undefined}
	<a href={documentUrl} class="btn preset-tonal-secondary ml-2 my-2" target="_blank"
		>Review Document</a
	>
{/if}
