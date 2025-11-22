import { CircleAlert, CircleCheck, CircleDot, CircleX } from 'lucide-svelte';
import type { CheckResult } from '$lib/client';

type ParsedStatus = {
	tailwindString: 'error' | 'success' | 'warning' | 'secondary';
	Icon: typeof CircleX;
};

const mapping = {
	PASS: {
		Icon: CircleCheck,
		tailwindString: 'success'
	},
	WARNING: {
		Icon: CircleAlert,
		tailwindString: 'warning'
	},
	FAIL: {
		Icon: CircleX,
		tailwindString: 'error'
	},
	PENDING: {
		Icon: CircleDot,
		tailwindString: 'secondary'
	}
} as const satisfies Record<CheckResult['status'], ParsedStatus>;

export function parseStatus(status: CheckResult['status']): ParsedStatus {
	return mapping[status];
}
