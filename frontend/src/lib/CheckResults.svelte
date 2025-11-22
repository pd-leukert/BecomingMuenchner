<script lang="ts">
	import type { CheckResult } from '$lib/client';
	import { Accordion } from '@skeletonlabs/skeleton-svelte';
	import { ChevronDownIcon } from 'lucide-svelte';
	import { parseStatus } from '$lib/statusParser';
	import CheckDocumentResults from '$lib/CheckDocumentResults.svelte';

	type Props = {
		checkResults: CheckResult[];
	};

	const { checkResults }: Props = $props();

	const sortedChecks = $derived(sortChecks(checkResults));

	function sortChecks(checkResults: CheckResult[]) {
		return checkResults.reduce(
			(acc, { documentTitle, ...rest }) => {
				if (documentTitle in acc) {
					acc[documentTitle].push(rest);
				} else {
					acc[documentTitle] = [rest];
				}
				return acc;
			},
			{} as Record<string, Omit<CheckResult, 'documentTitle'>[]>
		);
	}

	function computeAllFine(documentResults: Omit<CheckResult, 'documentTitle'>[]) {
		return documentResults.every(({ status }) => status === 'PASS');
	}

	// preset-tonal-error preset-tonal-warning preset-tonal-success preset-tonal-secondary
</script>

<Accordion multiple={true} collapsible={true} class="gap-4">
	{#each Object.entries(sortedChecks) as [documentTitle, checkResults] (documentTitle)}
		{@const allFine = computeAllFine(checkResults)}
		{@const { tailwindString, Icon } = parseStatus(allFine ? 'PASS' : 'FAIL')}
		<Accordion.Item value={documentTitle}>
			<h3>
				<Accordion.ItemTrigger
					class="font-bold m-0 h3 flex items-center gap-2 preset-tonal-{tailwindString} py-4"
				>
					<Icon />
					{documentTitle}
					<Accordion.ItemIndicator class="group ml-auto">
						<ChevronDownIcon class="h-5 w-5 group-data-[state=open]:rotate-180" />
					</Accordion.ItemIndicator>
				</Accordion.ItemTrigger>
			</h3>
			<Accordion.ItemContent class="p-0">
				<CheckDocumentResults {checkResults} />
			</Accordion.ItemContent>
		</Accordion.Item>
	{/each}
</Accordion>
