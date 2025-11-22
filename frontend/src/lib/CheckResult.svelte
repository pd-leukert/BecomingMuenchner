<script lang="ts">
	import type { CheckResult } from '$lib/client';
	import { parseStatus } from '$lib/statusParser';

	type Props = {
		checkResult: CheckResult;
	};

	const { checkResult }: Props = $props();

	const { tailwindString, Icon } = $derived(parseStatus(checkResult.status));

	// preset-tonal-error preset-tonal-warning preset-tonal-success preset-tonal-secondary
</script>

<div class="preset-tonal-{tailwindString} gap-4 my-6 p-4">
	<header>
		<span class="h5">
			<Icon class="inline" />
			{checkResult.title}
		</span>
	</header>
	{#if checkResult.affectedField}
		<p>
			Fehlerhaftes Feld: {checkResult.affectedField}
		</p>
	{/if}
	<p>
		{checkResult.message}
	</p>
</div>
