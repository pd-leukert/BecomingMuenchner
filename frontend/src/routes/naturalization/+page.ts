import type { PageLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { resolve } from '$app/paths';
export const load: PageLoad = () => redirect(308, resolve('/naturalization/0'));
