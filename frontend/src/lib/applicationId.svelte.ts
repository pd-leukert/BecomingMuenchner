let applicationId = $state('1');

export function setApplicationId(id: string) {
	applicationId = id;
}

export function getApplicationId() {
	return applicationId;
}
