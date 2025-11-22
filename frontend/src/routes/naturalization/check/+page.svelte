<script lang="ts">
	import {
		type ApplicationState,
		getApplicationsByApplicationId,
		postApplicationsByApplicationIdStartValidation,
		postApplicationsByApplicationIdSubmit
	} from '$lib/client';
	import { API_BASE } from '$lib/constants';
	import CheckResults from '$lib/CheckResults.svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import LoadingSpinner from '$lib/LoadingSpinner.svelte';
	import { scale } from 'svelte/transition';
	import { RotateCcw, Send, Sparkles, X } from 'lucide-svelte';

	let valRep: ApplicationState['validationReport'] | undefined = $state(undefined);
	let documentMetadata: ApplicationState['submittedData']['uploadedDocuments'] | undefined =
		$state(undefined);

	let timeoutId: undefined | NodeJS.Timeout = $state(undefined);

	let isCheckComplete = $state(false);

	const areAllChecksFine = $derived(computeAreAllChecksFine(valRep));

	function computeAreAllChecksFine(
		validationReport: ApplicationState['validationReport'] | undefined
	) {
		if (validationReport === undefined) {
			return true;
		}
		return validationReport.checks.every(({ status }) => status !== 'FAIL');
	}

	async function submitValidation() {
		await postApplicationsByApplicationIdSubmit({
			path: { applicationId: '0' },
			baseUrl: API_BASE
		});
		goto(resolve('/success'));
	}

	function startValidation() {
		if (timeoutId !== undefined) {
			return;
		}

		postApplicationsByApplicationIdStartValidation({
			path: { applicationId: '1' },
			baseUrl: API_BASE
		});
		timeoutId = setInterval(() => {
			getApplicationsByApplicationId({ path: { applicationId: '1' }, baseUrl: API_BASE }).then(
				({ data }) => {
					if (!data) {
						console.log(':(');
					}
					if (data?.status !== 'VALIDATING') {
						cancelValidation();
						isCheckComplete = true;
					}
					valRep = data?.validationReport;
					documentMetadata = data?.submittedData.uploadedDocuments;
				}
			);
		}, 2000);
	}

	function cancelValidation() {
		clearInterval(timeoutId);
		timeoutId = undefined;
	}
</script>

<h1 class="h1">Pre-check of submission</h1>

<section>
	<p class="p">Check your documents before submitting them.</p>
	<button
		type="button"
		class="btn preset-tonal-primary mx-auto my-4 font-semibold"
		onclick={startValidation}
	>
		{isCheckComplete ? 'Redo' : 'Start'} validation
		{#if isCheckComplete}
			<RotateCcw />
		{:else}
			<Sparkles />
		{/if}
	</button>
	{#if timeoutId !== undefined}
		<button
			transition:scale
			type="button"
			class="btn preset-tonal-error"
			onclick={cancelValidation}
		>
			Cancel
			<X />
		</button>
	{/if}
</section>
<section class="pb-4">
	<div class="mx-auto w-fit">
		{#if timeoutId !== undefined}
			<LoadingSpinner />
		{/if}
	</div>
	{#if timeoutId === undefined}
		<div transition:scale>
			<CheckResults checkResults={valRep?.checks ?? []} documentMetadata={documentMetadata ?? []} />
		</div>
	{/if}
</section>
{#if isCheckComplete && timeoutId === undefined}
	<section transition:scale>
		<form onsubmit={submitValidation} class="flex flex-col">
			<h2 class="h2">Submit application</h2>
			{#if !areAllChecksFine}
				<div class="p-4 preset-tonal-warning my-4">
					Some errors were detected. Please submit if and only if you are sure that this is not
					correct.
				</div>
			{/if}
			<button type="submit" class="btn preset-tonal-primary ml-auto">Submit <Send /></button>
		</form>
	</section>
{/if}
