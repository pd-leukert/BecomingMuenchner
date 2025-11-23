import express from 'express';
import type { Request, Response } from 'express';
import cors from 'cors';

// 1. IMPORT: Import the huge 'components' object from your generated file
import type { components } from './src/types.ts';

// 2. TYPE MAPPING: Extract relevant schemas into handy variables
type ApplicationState = components['schemas']['ApplicationState'];
type ValidationReport = components['schemas']['ValidationReport'];
type ApplicantDetails = components['schemas']['ApplicantDetails'];
type ApplicationData = components['schemas']['ApplicationData'];
type CheckResult = components['schemas']['CheckResult'];
type DocumentMetadata = components['schemas']['DocumentMetadata'];

const app = express();
app.use(cors());
app.use(express.json());

const PORT_NUMBER = parseInt(process.env.PORT || '8080', 10);
const API_BASE_URL = 'https://hackatum-db-api-254788991896.europe-west3.run.app';
const CLOUD_FUNCTION_URL = 'http://35.184.144.165:8001';

const DOC_FIELD_MAPPING = [
    { key: 'Einkommensnachweise', type: 'salary_slip' },
    { key: 'Mietvertrag', type: 'rent_contract' },
    { key: 'Aufenthaltstitel1', type: 'residence_permit_1' },
    { key: 'Aufenthaltstitel2', type: 'residence_permit_2' },
    { key: 'Aufenthaltstitel3', type: 'residence_permit_3' },
    { key: 'Pass', type: 'passport' },
    { key: 'sprachzertifikat', type: 'language_certificate' },
    { key: 'einbürgerungstest', type: 'naturalization_test' }
];

// Helper to fetch application from Python API
async function fetchApplication(id: string) {
    try {
        const res = await fetch(`${API_BASE_URL}/getApplications/${id}`);
        if (!res.ok) {
            console.error(`Failed to fetch application ${id}: ${res.status} ${res.statusText}`);
            return null;
        }
        return await res.json();
    } catch (error) {
        console.error(`Error fetching application ${id}:`, error);
        return null;
    }
}

// Helper to fetch documents from Python API
async function fetchDocuments(id: string) {
    try {
        const res = await fetch(`${API_BASE_URL}/get_documents_by_application/${id}`);
        if (!res.ok) {
            // It might return 404 if no documents exist yet, which is fine
            return [];
        }
        return await res.json();
    } catch (error) {
        console.error(`Error fetching documents for ${id}:`, error);
        return [];
    }
}

// Helper to map Python API data to ApplicationState
async function mapToApplicationState(appData: any, docs: any[]): Promise<ApplicationState> {
    const uploadedDocuments: DocumentMetadata[] = [];
    DOC_FIELD_MAPPING.forEach(field => {
        if (appData[field.key]) {
            uploadedDocuments.push({
                docId: field.key, // Use field key as ID for simplicity
                type: field.type,
                filename: appData[field.key].split('/').pop() || field.key,
                url: appData[field.key]
            });
        }
    });

    const titleMapping: Record<string, string> = {
        'salary_slip': 'Salary Slip',
        'rent_contract': 'Rent Contract',
        'residence_permit_1': 'Residence Permit 1',
        'residence_permit_2': 'Residence Permit 2',
        'residence_permit_3': 'Residence Permit 3',
        'passport': 'Passport',
        'language_certificate': 'Language Certificate',
        'naturalization_test': 'Naturalization Test'
    };

    const checks: CheckResult[] = docs.map((d: any) => ({
        documentTitle: titleMapping[d.document_kind] || d.document_kind,
        type: d.document_kind,
        checkDisplayTitle: d.criteria,
        status: d.result ? 'PASS' : 'FAIL',
        message: d.message
    }));

    // Map status string to Enum
    let status: ApplicationState['status'] = 'DRAFT';
    if (['DRAFT', 'VALIDATING', 'READY_TO_SUBMIT', 'READY_TO_SUBMIT_WITH_PROBLEMS', 'SUBMITTED'].includes(appData.status)) {
        status = appData.status as ApplicationState['status'];
    } else {
        // Fallback mapping if Python API uses different strings
        if (appData.status === 'PENDING') status = 'VALIDATING';
        // Add more mappings if needed
    }

    // Determine overallResult based on status and result
    let overallResult: ValidationReport['overallResult'] = 'PENDING';
    if (status === 'DRAFT' || status === 'VALIDATING') {
        overallResult = 'PENDING';
    } else if (status === 'READY_TO_SUBMIT_WITH_PROBLEMS') {
        overallResult = 'WARNING';
    } else if (!appData.result) {
        overallResult = 'CRITICAL_ERROR';
    } else {
        overallResult = 'SUCCESS';
    }

    return {
        id: appData.id.toString(),
        applicantName: `${appData.vorname} ${appData.nachname}`,
        applicant: {
            firstName: appData.vorname,
            lastName: appData.nachname,
            email: 'unknown@example.com', // Not in Python API
            address: appData.addresse,
            nationality: appData.staatsangehoerigkeit
        },
        status: status,
        submittedData: {
            uploadedDocuments
        },
        validationReport: {
            isComplete: status !== 'DRAFT' && status !== 'VALIDATING',
            overallResult: overallResult,
            checkedAt: new Date().toISOString(), // Not in API
            checks
        }
    };
}

// ------------------------------------------------------
// 1. GET /applications/{id} - Get status (Polling)
// ------------------------------------------------------
app.get('/api/v1/applications/:id', async (req: Request, res: Response) => {
    const id = req.params.id;
    const appData = await fetchApplication(id);

    if (!appData) {
        return res.status(404).json({ error: 'Application not found' });
    }

    const docs = await fetchDocuments(id);
    const state = await mapToApplicationState(appData, docs);

    res.json(state);
});

// ------------------------------------------------------
// 2. POST /applications/{id}/start-validation - Explicitly start process
// ------------------------------------------------------
app.post('/api/v1/applications/:id/start-validation', async (req: Request, res: Response) => {
    const id = req.params.id;
    const appData = await fetchApplication(id);

    if (!appData) {
        return res.status(404).json({ error: 'Not found' });
    }

    // 1. Update status in Python API
    await fetch(`${API_BASE_URL}/update_status_application/${id}?status=VALIDATING`, {
        method: 'POST'
    });

    // 2. Asynchronously trigger the "Cloud Function"
    // 2. Trigger the Cloud Function
    try {
        /* const cloudRes = await fetch(`${CLOUD_FUNCTION_URL}/check/${id}`, {
            method: 'POST'
        }); */
        const cloudRes = await fetch(`${CLOUD_FUNCTION_URL}/check`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ applicationId: id }) // Or simply { id } if using ES6 shorthand
        });
        if (!cloudRes.ok) {
            console.error(`Failed to trigger cloud function: ${cloudRes.status}`);
            // We might want to return an error here, or just log it. 
            // For now, we'll log it but still return 202 as the process "started" (or tried to).
        } else {
            console.log(`Triggered cloud function for app ${id}`);
        }
    } catch (error) {
        console.error(`Error triggering cloud function for ${id}:`, error);
    }

    res.status(202).json({ message: 'Validation started' });
});

// ------------------------------------------------------
// 3. POST /internal/... - Callback from FaaS
// ------------------------------------------------------
app.post('/api/v1/internal/applications/:id/validation-result', async (req: Request, res: Response) => {
    const id = req.params.id;

    // IMPORTANT: Express doesn't know what's in the body. We must "cast" it.
    const result = req.body as ValidationReport;

    // Update Python API with results
    // 1. Update overall result/status
    let newStatus = 'READY_TO_SUBMIT';
    let overallResult = true;

    if (result.overallResult === 'CRITICAL_ERROR') {
        // Handle error
        overallResult = false;
    } else if (result.overallResult === 'WARNING') {
        newStatus = 'READY_TO_SUBMIT_WITH_PROBLEMS';
        overallResult = true; // Or false? "result" in Python API seems to be boolean. Let's assume true means "passed enough to proceed"
    } else {
        newStatus = 'READY_TO_SUBMIT';
        overallResult = true;
    }

    await fetch(`${API_BASE_URL}/update_status_application/${id}?status=${newStatus}`, { method: 'POST' });
    await fetch(`${API_BASE_URL}/update_result_application/${id}?result=${overallResult}`, { method: 'POST' });

    // 2. Update documents
    for (const check of result.checks) {
        // We need to map check to document criteria
        // Python API: update_result_message_document/{application_id}/{document_kind}/{criteria}
        // check.type -> document_kind
        // check.checkDisplayTitle -> criteria

        // Note: Python API might expect specific strings.
        // If the document doesn't exist, we might need to create it first?
        // The Python API has create_document.
        // Let's try to update, if it fails (404), create it.

        const kind = check.type || 'unknown';
        const criteria = check.checkDisplayTitle;
        const checkResult = check.status === 'PASS';
        const message = check.message;

        const updateUrl = `${API_BASE_URL}/update_result_message_document/${id}/${kind}/${criteria}?result=${checkResult}&message=${encodeURIComponent(message)}`;
        const updateRes = await fetch(updateUrl, { method: 'POST' });

        if (!updateRes.ok) {
            // Try creating it
            await fetch(`${API_BASE_URL}/Documents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    application_id: parseInt(id),
                    document_kind: kind,
                    criteria: criteria,
                    result: checkResult,
                    message: message
                })
            });
        }
    }

    console.log(`[Broker] Result received and saved for ${id}.`);
    res.sendStatus(200);
});

// ------------------------------------------------------
// 4. Submit / Reject
// ------------------------------------------------------
app.post('/api/v1/applications/:id/submit', async (req: Request, res: Response) => {
    const id = req.params.id;
    const appData = await fetchApplication(id);

    if (appData) {
        await fetch(`${API_BASE_URL}/update_status_application/${id}?status=SUBMITTED`, { method: 'POST' });
        res.json({ status: 'SUBMITTED', submissionId: 'sub_999' });
    } else {
        res.status(404).send();
    }
});

// ------------------------------------------------------
// 5. Internal: Get data for validation
// ------------------------------------------------------
app.get('/api/v1/internal/applications/:applicationId/data', async (req: Request, res: Response) => {
    const appId = req.params.applicationId;
    const appData = await fetchApplication(appId);

    if (!appData) {
        return res.status(404).json({ error: 'Application not found' });
    }

    const docs = await fetchDocuments(appId);
    const state = await mapToApplicationState(appData, docs);

    const internalData: ApplicationData = {
        applicationId: appId,
        applicant: state.applicant,
        submittedDocuments: state.submittedData.uploadedDocuments
    };

    res.json(internalData);
});

// ------------------------------------------------------
// 7. Internal: Get document
// ------------------------------------------------------
app.get('/api/v1/internal/documents/:applicationId/:type', async (req: Request, res: Response) => {
    const { applicationId, type } = req.params;

    const mapping = DOC_FIELD_MAPPING.find(m => m.type === type);
    if (!mapping) {
        return res.status(400).json({ error: `Unknown document type: ${type}` });
    }

    const appData = await fetchApplication(applicationId);
    if (!appData) {
        return res.status(404).json({ error: 'Application not found' });
    }

    const fileUrl = appData[mapping.key];
    if (!fileUrl) {
        return res.status(404).json({ error: 'Document not found' });
    }

    try {
        const fileRes = await fetch(fileUrl);
        if (!fileRes.ok) {
            return res.status(502).json({ error: 'Failed to fetch document from storage' });
        }

        const contentType = fileRes.headers.get('content-type');
        if (contentType) res.setHeader('Content-Type', contentType);

        const arrayBuffer = await fileRes.arrayBuffer();
        res.send(Buffer.from(arrayBuffer));
        return;
    } catch (error) {
        console.error(`Error fetching document ${applicationId}/${type}:`, error);
        return;
    }

    res.status(202).json({ message: 'Validation started' });
});

// ------------------------------------------------------
// 3. POST /internal/... - Callback from FaaS
// ------------------------------------------------------
app.post('/api/v1/internal/applications/:id/validation-result', async (req: Request, res: Response) => {
    const id = req.params.id;

    // IMPORTANT: Express doesn't know what's in the body. We must "cast" it.
    const result = req.body as ValidationReport;

    // Update Python API with results
    // 1. Update overall result/status
    let newStatus = 'READY_TO_SUBMIT';
    let overallResult = true;

    if (result.overallResult === 'CRITICAL_ERROR') {
        // Handle error
        overallResult = false;
    } else if (result.overallResult === 'WARNING') {
        newStatus = 'READY_TO_SUBMIT_WITH_PROBLEMS';
        overallResult = true; // Or false? "result" in Python API seems to be boolean. Let's assume true means "passed enough to proceed"
    } else {
        newStatus = 'READY_TO_SUBMIT';
        overallResult = true;
    }

    await fetch(`${API_BASE_URL}/update_status_application/${id}?status=${newStatus}`, { method: 'POST' });
    await fetch(`${API_BASE_URL}/update_result_application/${id}?result=${overallResult}`, { method: 'POST' });

    // 2. Update documents
    for (const check of result.checks) {
        // We need to map check to document criteria
        // Python API: update_result_message_document/{application_id}/{document_kind}/{criteria}
        // check.type -> document_kind
        // check.checkDisplayTitle -> criteria

        // Note: Python API might expect specific strings.
        // If the document doesn't exist, we might need to create it first?
        // The Python API has create_document.
        // Let's try to update, if it fails (404), create it.

        const kind = check.type || 'unknown';
        const criteria = check.checkDisplayTitle;
        const checkResult = check.status === 'PASS';
        const message = check.message;

        const updateUrl = `${API_BASE_URL}/update_result_message_document/${id}/${kind}/${criteria}?result=${checkResult}&message=${encodeURIComponent(message)}`;
        const updateRes = await fetch(updateUrl, { method: 'POST' });

        if (!updateRes.ok) {
            // Try creating it
            await fetch(`${API_BASE_URL}/Documents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    application_id: parseInt(id),
                    document_kind: kind,
                    criteria: criteria,
                    result: checkResult,
                    message: message
                })
            });
        }
    }

    console.log(`[Broker] Result received and saved for ${id}.`);
    res.sendStatus(200);
});

// ------------------------------------------------------
// 4. Submit / Reject
// ------------------------------------------------------
app.post('/api/v1/applications/:id/submit', async (req: Request, res: Response) => {
    const id = req.params.id;
    const appData = await fetchApplication(id);

    if (appData) {
        await fetch(`${API_BASE_URL}/update_status_application/${id}?status=SUBMITTED`, { method: 'POST' });
        res.json({ status: 'SUBMITTED', submissionId: 'sub_999' });
    } else {
        res.status(404).send();
    }
});

// ------------------------------------------------------
// 5. Internal: Get data for validation
// ------------------------------------------------------
app.get('/api/v1/internal/applications/:applicationId/data', async (req: Request, res: Response) => {
    const appId = req.params.applicationId;
    const appData = await fetchApplication(appId);

    if (!appData) {
        return res.status(404).json({ error: 'Application not found' });
    }

    const docs = await fetchDocuments(appId);
    const state = await mapToApplicationState(appData, docs);

    const internalData: ApplicationData = {
        applicationId: appId,
        applicant: state.applicant,
        submittedDocuments: state.submittedData.uploadedDocuments
    };

    res.json(internalData);
});

// ------------------------------------------------------
// 7. Internal: Get document
// ------------------------------------------------------
app.get('/api/v1/internal/documents/:applicationId/:type', async (req: Request, res: Response) => {
    const { applicationId, type } = req.params;

    const mapping = DOC_FIELD_MAPPING.find(m => m.type === type);
    if (!mapping) {
        return res.status(400).json({ error: `Unknown document type: ${type}` });
    }

    const appData = await fetchApplication(applicationId);
    if (!appData) {
        return res.status(404).json({ error: 'Application not found' });
    }

    const fileUrl = appData[mapping.key];
    if (!fileUrl) {
        return res.status(404).json({ error: 'Document not found' });
    }

    try {
        // Ensure URL is properly encoded (handles spaces etc.)
        const encodedUrl = new URL(fileUrl).href;
        const fileRes = await fetch(encodedUrl);
        if (!fileRes.ok) {
            return res.status(502).json({ error: 'Failed to fetch document from storage' });
        }

        const contentType = fileRes.headers.get('content-type');
        if (contentType) res.setHeader('Content-Type', contentType);

        const arrayBuffer = await fileRes.arrayBuffer();
        res.send(Buffer.from(arrayBuffer));
    } catch (error) {
        console.error(`Error fetching document ${applicationId}/${type} from ${fileUrl}:`, error);
        res.status(500).send();
    }
});


app.listen(PORT_NUMBER, '0.0.0.0', () => {
    console.log(`Broker running on port ${PORT_NUMBER}`);
    console.log(`Connected to Python API at ${API_BASE_URL}`);
});