import type { MockPageContent } from '$lib/types';

export const mockPages: MockPageContent[] = [
	{
		type: 'mock',
		header: 'Identity Check',
		sections: [
			{
				documentName: 'Passport',
				description: 'Submit your passport here'
			},
			{
				documentName: 'Residence permit',
				description: '5 years of residency; 2 years for spouses'
			}
		]
	},
	{
		type: 'mock',
		header: 'Subsidence',
		sections: [
			{
				documentName: 'Proof of income',
				description: 'U make money'
			},
			{
				documentName: 'Rental agreement',
				description: ''
			}
		]
	},
	{
		type: 'mock',
		header: 'Integration',
		sections: [
			{
				documentName: 'Language certificate',
				description: 'Deutsche Sprache schwere Sprache'
			},
			{
				documentName: 'Naturalization test',
				description: '?'
			}
		]
	}
] as const;
