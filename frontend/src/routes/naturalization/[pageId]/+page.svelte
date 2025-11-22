<script lang="ts">
	import { page } from '$app/state';

	const pageContent = $derived(page.data.pageContent);
</script>

<h1 class="h1">{pageContent.header}</h1>

{#each pageContent.sections as section, i (i)}
	<section>
		<h2 class="h2">{section.documentName}</h2>
		<p>{section.description}</p>
		<button class="btn" onclick={() => void {}}>Hochladen</button>
	</section>
{/each}
