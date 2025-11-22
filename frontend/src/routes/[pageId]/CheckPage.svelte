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

	function submitValidation() {
		postApplicationsByApplicationIdSubmit({ path: { applicationId: '0' }, baseUrl: API_BASE });
	}

	function startValidation() {
		postApplicationsByApplicationIdStartValidation({
			path: { applicationId: '0' },
			baseUrl: API_BASE
		});
	}

	function check() {
		getApplicationsByApplicationId({ path: { applicationId: '0' }, baseUrl: API_BASE }).then(
			({ data }) => {
				valRep = data?.validationReport;
			}
		);
	}
</script>

<h1 class="h1">Überprüfung der Angaben</h1>

<section>
	<p class="p">Lasse deine Angaben überprüfen, bevor du sie endgültig einreichst.</p>
	<button class="btn" onclick={startValidation}>Validierung starten</button>
	<button class="btn" onclick={check}>Überprüfen</button>
	<button class="btn" onclick={submitValidation}>Abgeben</button>
</section>
<section>
	{#each valRep?.checks ?? [] as checkResult, i (i)}
		<CheckResult {checkResult} />
	{/each}
</section>
