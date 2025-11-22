import express from 'express';
import type { Request, Response } from 'express';
import cors from 'cors';
import axios from 'axios';

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
const PYTHON_API_URL = 'https://hackatum-db-api-254788991896.europe-west3.run.app';

// Helper to map Python Application to Broker ApplicationState
async function mapPythonAppToBrokerApp(pyApp: any): Promise<ApplicationState> {
    // Fetch documents
    let pyDocs: any[] = [];
    try {
        const docsRes = await axios.get(`${PYTHON_API_URL}/get_documents_by_application/${pyApp.id}`);
        pyDocs = docsRes.data;
    } catch (e) {
        console.warn(`Could not fetch documents for app ${pyApp.id}`, e);
    }

    const uploadedDocuments: DocumentMetadata[] = pyDocs.map((doc: any) => ({
        docId: doc.id ? doc.id.toString() : 'unknown',
        type: doc.document_kind,
        filename: doc.url.split('/').pop() || 'document.pdf',
        url: doc.url
    }));

    const checks: CheckResult[] = pyDocs.map((doc: any) => ({
        checkId: `${doc.document_kind}`,
        title: `${doc.document_kind} Check`,
        status: doc.result === true ? 'PASS' : (doc.result === false ? 'FAIL' : 'PENDING'),
        message: doc.message || '',
        affectedField: doc.document_kind
    }));

    // Determine overall result
    let overallResult: ValidationReport['overallResult'] = 'PENDING';
    if (pyApp.status === 'VALIDATING') {
        overallResult = 'PENDING';
    } else if (checks.some(c => c.status === 'FAIL')) {
        overallResult = 'CRITICAL_ERROR';
    } else if (checks.some(c => c.status === 'WARNING')) {
         overallResult = 'WARNING';
    } else if (checks.length > 0 && checks.every(c => c.status === 'PASS')) {
        overallResult = 'SUCCESS';
    }

    // Map status
    let status: ApplicationState['status'] = 'DRAFT';
    const s = pyApp.status;
    if (s === 'VALIDATING') status = 'VALIDATING';
    else if (s === 'READY_TO_SUBMIT') status = 'READY_TO_SUBMIT';
    else if (s === 'READY_TO_SUBMIT_WITH_PROBLEMS') status = 'READY_TO_SUBMIT_WITH_PROBLEMS';
    else if (s === 'SUBMITTED') status = 'SUBMITTED';
    else status = 'DRAFT';

    return {
        id: pyApp.id.toString(),
        applicantName: `${pyApp.vorname} ${pyApp.nachname}`,
        applicant: {
            firstName: pyApp.vorname,
            lastName: pyApp.nachname,
            email: 'unknown@example.com',
            address: pyApp.adresse,
            nationality: pyApp.staatsangehoerigkeit
        },
        status: status,
        submittedData: {
            uploadedDocuments
        },
        validationReport: {
            isComplete: status !== 'VALIDATING' && status !== 'DRAFT',
            overallResult: overallResult,
            checkedAt: new Date().toISOString(),
            checks: checks
        }
    };
}

// ------------------------------------------------------
// 1. GET /applications/{id} - Get status (Polling)
// ------------------------------------------------------
app.get('/api/v1/applications/:id', async (req: Request, res: Response) => {
    try {
        const id = req.params.id;
        const response = await axios.get(`${PYTHON_API_URL}/getApplications/${id}`);
        const appData = await mapPythonAppToBrokerApp(response.data);
        res.json(appData);
    } catch (error) {
        console.error('Error fetching application:', error);
        res.status(404).json({ error: 'Application not found' });
    }
});

// ------------------------------------------------------
// 2. POST /applications/{id}/start-validation - Explicitly start process
// ------------------------------------------------------
app.post('/api/v1/applications/:id/start-validation', async (req: Request, res: Response) => {
    const id = req.params.id;
    try {
        // 1. Update status in Python API
        await axios.post(`${PYTHON_API_URL}/update_status_application/${id}?status=VALIDATING`);

        // 2. Asynchronously trigger the "Cloud Function"
        simulateCloudFunction(id);

        res.status(202).json({ message: 'Validation started' });
    } catch (error) {
        console.error('Error starting validation:', error);
        res.status(500).json({ error: 'Could not start validation' });
    }
});

// ------------------------------------------------------
// 3. POST /internal/... - Callback from FaaS
// ------------------------------------------------------
app.post('/api/v1/internal/applications/:id/validation-result', async (req: Request, res: Response) => {
    const id = req.params.id;
    const result = req.body as ValidationReport;

    try {
        // Update documents based on checks
        for (const check of result.checks) {
             const docsRes = await axios.get(`${PYTHON_API_URL}/get_documents_by_application/${id}`);
             const docs = docsRes.data;
             const doc = docs.find((d: any) => d.document_kind === check.checkId || d.document_kind === check.title);

             if (doc) {
                 await axios.post(`${PYTHON_API_URL}/update_result_message_document/${id}/${doc.document_kind}/${doc.criteria}?result=${check.status === 'PASS'}&message=${encodeURIComponent(check.message)}`);
             }
        }

        // Update status
        let status = 'READY_TO_SUBMIT';
        if (result.overallResult === 'WARNING') {
            status = 'READY_TO_SUBMIT_WITH_PROBLEMS';
        } else if (result.overallResult === 'CRITICAL_ERROR') {
            // status = 'DRAFT'; // ?
        }
        
        await axios.post(`${PYTHON_API_URL}/update_status_application/${id}?status=${status}`);
        
        console.log(`[Broker] Result received for ${id}.`);
        res.sendStatus(200);
    } catch (error) {
        console.error('Error processing validation result:', error);
        res.status(500).send();
    }
});

// ------------------------------------------------------
// 4. Submit / Reject
// ------------------------------------------------------
app.post('/api/v1/applications/:id/submit', async (req: Request, res: Response) => {
    const id = req.params.id;
    try {
        await axios.post(`${PYTHON_API_URL}/update_status_application/${id}?status=SUBMITTED`);
        res.json({ status: 'SUBMITTED', submissionId: 'sub_999' });
    } catch (error) {
        console.error('Error submitting application:', error);
        res.status(500).send();
    }
});

// ------------------------------------------------------
// 5. Internal: Get data for validation
// ------------------------------------------------------
app.get('/api/v1/internal/applications/:applicationId/data', async (req: Request, res: Response) => {
    const appId = req.params.applicationId;
    try {
        const response = await axios.get(`${PYTHON_API_URL}/getApplications/${appId}`);
        const appState = await mapPythonAppToBrokerApp(response.data);

        const internalData: ApplicationData = {
            applicationId: appId,
            applicant: appState.applicant,
            submittedDocuments: appState.submittedData.uploadedDocuments
        };

        res.json(internalData);
    } catch (error) {
        res.status(404).json({ error: 'Application not found' });
    }
});

// ------------------------------------------------------
// 7. Internal: Get document.
// ------------------------------------------------------
app.get('/api/v1/internal/documents/:documentId', (req: Request, res: Response) => {
    const docId = req.params.documentId;
    // Mock: We simply always return success, content doesn't matter for the broker here
    // In reality one would pipe the file stream from S3/Disk.
    console.log(`[Broker] Serving document ${docId}`);
    res.setHeader('Content-Type', 'application/pdf');
    res.send('PDF-CONTENT-MOCK'); 
});


// --- SIMULATION OF CLOUD FUNCTION (Mock) ---
async function simulateCloudFunction(appId: string) {
    console.log(`[MockFaaS] Starting check for ${appId}...`);

    setTimeout(async () => {
        try {
            // Fetch documents to validate
            const docsRes = await axios.get(`${PYTHON_API_URL}/get_documents_by_application/${appId}`);
            const docs = docsRes.data;

            let hasWarning = false;

            for (const doc of docs) {
                // Mock logic: Randomly pass or warn
                const isPass = Math.random() > 0.3;
                const message = isPass ? 'Document looks good.' : 'Document needs review.';
                
                if (!isPass) hasWarning = true;

                await axios.post(`${PYTHON_API_URL}/update_result_message_document/${appId}/${doc.document_kind}/${doc.criteria}?result=${isPass}&message=${encodeURIComponent(message)}`);
            }

            const newStatus = hasWarning ? 'READY_TO_SUBMIT_WITH_PROBLEMS' : 'READY_TO_SUBMIT';
            await axios.post(`${PYTHON_API_URL}/update_status_application/${appId}?status=${newStatus}`);

            console.log(`[MockFaaS] Finished. Data saved.`);
        } catch (e) {
            console.error('[MockFaaS] Error during simulation:', e);
        }
    }, 3000);
}

app.listen(PORT_NUMBER, '0.0.0.0', () => {
    console.log(`Broker running on port ${PORT_NUMBER}`);
});