import type { CheckPageContent, MockPageContent } from '$lib/types';

export const mockPages: MockPageContent[] = [
	{
		type: 'mock',
		header: 'Identitätsprüfung',
		sections: [
			{
				documentName: 'Pass',
				description: 'Dein Pass'
			},
			{
				documentName: 'Aufenthaltstitel',
				description: '5 Jahre rechtmäßiger Aufenthalt; 2 Jahre für Ehegatten'
			}
		]
	},
	{
		type: 'mock',
		header: 'Lebensunterhaltssicherung',
		sections: [
			{
				documentName: 'Einkommensnachweise',
				description: 'Kein Geringverdiener?'
			},
			{
				documentName: 'Mietvertrag',
				description: 'Dein Mietvertrag'
			}
		]
	},
	{
		type: 'mock',
		header: 'Integration',
		sections: [
			{
				documentName: 'Sprachzertifikat',
				description: 'Deutsche Sprache schwere Sprache'
			},
			{
				documentName: 'Einbürgerungstest',
				description: 'hmmm.'
			}
		]
	}
] as const;

export const checkPage = checkPageFromMockPages(mockPages);

function checkPageFromMockPages(mockPages: MockPageContent[]): CheckPageContent {
	const checks = mockPages.reduce(
		(acc, mockPage) => [...acc, { checkName: mockPage.header }],
		[] as CheckPageContent['checks']
	);
	return {
		type: 'check',
		checks
	};
}
