export type PageContent = MockPageContent | CheckPageContent;

export type MockPageContent = {
	type: 'mock';
	header: string;
	sections: MockSection[];
};

export type MockSection = {
	documentName: string;
	description: string;
};

export type CheckPageContent = {
	type: 'check';
	checks: {
		checkName: string;
	}[];
};
