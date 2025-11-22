<script lang="ts">
	import type { CheckPageContent } from '$lib/types';
	import {
		type ApplicationState,
		getApplicationsByApplicationId,
		postApplicationsByApplicationIdStartValidation,
		postApplicationsByApplicationIdSubmit
	} from '$lib/client';
	import { API_BASE } from '$lib/constants';
	import CheckResult from '$lib/CheckResult.svelte';

	type Props = {
		pageContent: CheckPageContent;
	};

	const { pageContent }: Props = $props();

	let valRep: ApplicationState['validationReport'] | undefined = $state(undefined);

	let timeoutId: undefined | NodeJS.Timeout = undefined;

	function submitValidation() {
		postApplicationsByApplicationIdSubmit({ path: { applicationId: '0' }, baseUrl: API_BASE });
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
	<button class="btn" onclick={startValidation}>Validierung starten</button>
	<button class="btn" onclick={submitValidation}>Abgeben</button>
</section>
<section>
	{#each valRep?.checks ?? [] as checkResult, i (i)}
		<CheckResult {checkResult} />
	{/each}
</section>
