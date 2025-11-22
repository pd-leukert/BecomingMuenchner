<script lang="ts">
	import { page } from '$app/state';
	import { CircleCheck, Upload } from 'lucide-svelte';

	const pageContent = $derived(page.data.pageContent);
</script>

<h1 class="h1">{pageContent.header}</h1>

{#each pageContent.sections as section, i (i)}
	<section>
		<h2 class="h2">{section.documentName}</h2>
		<p>{section.description}</p>
		<span class="flex gap-4 my-4">
			<button class="btn preset-tonal-secondary font-semibold" onclick={() => void {}}>
				Hochladen <Upload />
			</button>
			<span class="flex items-center gap-2">
				<CircleCheck class="inline" />
				Dokument hochgeladen
			</span>
		</span>
	</section>
{/each}
