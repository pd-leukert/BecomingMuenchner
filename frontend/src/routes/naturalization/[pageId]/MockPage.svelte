<script lang="ts">
	import type { MockPageContent } from '$lib/types';

	type Props = {
		pageContent: MockPageContent;
	};

	const { pageContent }: Props = $props();
</script>

<h1 class="h1">{pageContent.header}</h1>

{#each pageContent.sections as section}
	<section>
		<h2 class="h2">{section.documentName}</h2>
		<p>{section.description}</p>
		<button class="btn" onclick={() => void {}}>Hochladen</button>
	</section>
{/each}
