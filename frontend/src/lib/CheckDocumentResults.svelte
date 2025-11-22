<script lang="ts">
	import type { CheckResult } from '$lib/client';
	import { parseStatus } from '$lib/statusParser';

	type Props = {
		checkResults: Omit<CheckResult, 'documentTitle'>[];
	};

	const { checkResults }: Props = $props();

	// preset-tonal-error preset-tonal-warning preset-tonal-success preset-tonal-secondary
</script>

<ul class="ml-2">
	{#each checkResults as checkResult, i (i)}
		{@const { Icon, tailwindString } = parseStatus(checkResult.status)}
		<li class="preset-tonal-{tailwindString} color px-4 py-4 gap-2 flex flex-col base-font-color-dark">
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
