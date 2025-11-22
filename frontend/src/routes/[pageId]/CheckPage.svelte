<script lang="ts">
	import type { CheckPageContent, MockPageContent } from '$lib/types';

	type Props = {
		pageContent: CheckPageContent;
	};

	const { pageContent }: Props = $props();
</script>

<h1>Überprüfung der Angaben</h1>

<p>Lasse deine Angaben überprüfen, bevor du sie endgültig einreichst.</p>

<button class="btn">Überprüfen</button>
