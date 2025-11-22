<script lang="ts">
	import {
		type ApplicationState,
		getApplicationsByApplicationId,
		postApplicationsByApplicationIdStartValidation,
		postApplicationsByApplicationIdSubmit
	} from '$lib/client';
	import { API_BASE } from '$lib/constants';
	import CheckResult from '$lib/CheckResult.svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import LoadingSpinner from '$lib/LoadingSpinner.svelte';

	let valRep: ApplicationState['validationReport'] | undefined = $state(undefined);

	let timeoutId: undefined | NodeJS.Timeout = $state(undefined);

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
			path: { applicationId: '0' },
			baseUrl: API_BASE
		});
		timeoutId = setInterval(() => {
			getApplicationsByApplicationId({ path: { applicationId: '0' }, baseUrl: API_BASE }).then(
				({ data }) => {
					if (!data) {
						console.log(':(');
					}
					if (data?.status !== 'VALIDATING') {
						clearInterval(timeoutId);
						timeoutId = undefined;
					}
					valRep = data?.validationReport;
				}
			);
		}, 2000);
	}
</script>

<h1 class="h1">Überprüfung der Angaben</h1>

<section>
	<p class="p">Lasse deine Angaben überprüfen, bevor du sie endgültig einreichst.</p>
	<button type="button" class="btn" onclick={startValidation}>Validierung starten</button>
</section>
<section>
    <div class="mx-auto w-fit">
        {#if timeoutId !== undefined}
            <LoadingSpinner />
        {/if}
    </div>
	{#each valRep?.checks ?? [] as checkResult, i (i)}
		<CheckResult {checkResult} />
	{/each}
</section>
<section>
	<form onsubmit={submitValidation}>
		<h2 class="h2">Submit application</h2>
		<button type="submit" class="btn preset-tonal-primary">Submit</button>
	</form>
</section>
