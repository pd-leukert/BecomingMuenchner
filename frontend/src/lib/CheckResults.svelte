<script lang="ts">
	import type { CheckResult, DocumentMetadata } from '$lib/client';
	import { Accordion } from '@skeletonlabs/skeleton-svelte';
	import { ChevronDownIcon } from 'lucide-svelte';
	import { parseStatus } from '$lib/statusParser';
	import CheckDocumentResults from '$lib/CheckDocumentResults.svelte';

	type Props = {
		checkResults: CheckResult[];
		documentMetadata: DocumentMetadata[];
	};

	const { checkResults, documentMetadata }: Props = $props();

	type ProcessedCheckResult = {
		documentUrl?: string;
		checks: Omit<CheckResult, 'documentTitle'>[];
	};

	const sortedChecks = $derived(sortChecks(checkResults, documentMetadata));

	function sortChecks(
		checkResults: CheckResult[],
		documentMetadata: DocumentMetadata[]
	): Record<string, ProcessedCheckResult> {
		const intermediateRes = checkResults.reduce(
			(acc, { documentTitle, ...rest }) => {
				if (documentTitle in acc) {
					acc[documentTitle].checks.push(rest);
				} else {
					acc[documentTitle] = {
						checks: [rest]
					};
				}
				return acc;
			},
			{} as Record<string, ProcessedCheckResult>
		);

		checkResults = checkResults.toSorted((res) => (res.status === 'FAIL' ? 0 : 1));

		return documentMetadata.reduce(
			(acc, { url, type }) => {
				if (type in acc) {
					acc[type].documentUrl = url;
				}
				return acc;
			},
			intermediateRes as Record<string, ProcessedCheckResult>
		);
	}

	function computeAllFine(documentResults: Omit<CheckResult, 'documentTitle'>[]) {
		return documentResults.every(({ status }) => status === 'PASS');
	}

	// preset-tonal-error preset-tonal-warning preset-tonal-success preset-tonal-secondary
</script>

<Accordion multiple={true} collapsible={true} class="gap-4">
	{#each Object.entries(sortedChecks) as [documentTitle, { checks, documentUrl }] (documentTitle)}
		{@const allFine = computeAllFine(checks)}
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
				<CheckDocumentResults {checks} {documentUrl} />
			</Accordion.ItemContent>
		</Accordion.Item>
	{/each}
</Accordion>
