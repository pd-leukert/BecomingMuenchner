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

// --- HACKATHON DATABASE (In-Memory) ---
// Now the map is type-safe! TypeScript will complain if mock data is wrong.
const db = new Map<string, ApplicationState>();
const applicantsDb = new Map<string, ApplicantDetails>();

// Initialize mock data
db.set("0", {
    id: "0",
    applicantName: 'Erika Musterfrau',
    applicant: {
        firstName: 'Erika',
        lastName: 'Musterfrau',
        email: 'erika.musterfrau@example.com',
        address: 'Musterstraße 1, 80331 München',
        nationality: 'Germany'
    },
    status: 'DRAFT', // Must be one of the enum values from the YAML!
    submittedData: {
        uploadedDocuments: [
            { docId: 'doc_1', type: 'passport', filename: 'pass.pdf', url: '/files/pass.pdf' },
            { docId: 'doc_2', type: 'salary_slip', filename: 'gehalt.pdf', url: '/files/gehalt.pdf' }
        ]
    },
    validationReport: {
        isComplete: false,
        checks: [] // Initially empty array
    }
});

applicantsDb.set('applicant_1', {
    firstName: 'Erika',
    lastName: 'Musterfrau',
    email: 'erika.musterfrau@example.com',
    address: 'Musterstraße 1, 80331 München'
});

// ------------------------------------------------------
// 1. GET /applications/{id} - Get status (Polling)
// ------------------------------------------------------
app.get('/api/v1/applications/:id', (req: Request, res: Response) => {
    const appData = db.get(req.params.id);

    if (!appData) {
        return res.status(404).json({ error: 'Application not found' });
    }

    res.json(appData);
});

// ------------------------------------------------------
// 2. POST /applications/{id}/start-validation - Explicitly start process
// ------------------------------------------------------
app.post('/api/v1/applications/:id/start-validation', async (req: Request, res: Response) => {
    const id = req.params.id;
    const appData = db.get(id);

    if (!appData) {
        return res.status(404).json({ error: 'Not found' });
    }

    // 1. Update status
    appData.status = 'VALIDATING';
    appData.validationReport = {
        isComplete: false,
        overallResult: 'PENDING',
        checks: []
    };
    db.set(id, appData);

    // 2. Asynchronously trigger the "Cloud Function"
    simulateCloudFunction(id);

    res.status(202).json({ message: 'Validation started' });
});

// ------------------------------------------------------
// 3. POST /internal/... - Callback from FaaS
// ------------------------------------------------------
app.post('/api/v1/internal/applications/:id/validation-result', (req: Request, res: Response) => {
    const id = req.params.id;

    // IMPORTANT: Express doesn't know what's in the body. We must "cast" it.
    const result = req.body as ValidationReport;

    const appData = db.get(id);
    if (!appData) return res.status(404).send();

    // Save result
    appData.validationReport = result;

    // Derive global status
    if (result.overallResult === 'CRITICAL_ERROR') {
        // Logic: On error it stays visible, or status changes
        // We leave it on VALIDATING here or set it to an error status,
        // but according to Enum there is no explicit ERROR status for the application, only in the report.
        // Maybe reset to DRAFT?
    } else if (result.overallResult === 'WARNING') {
        appData.status = 'READY_TO_SUBMIT_WITH_PROBLEMS';
    } else {
        appData.status = 'READY_TO_SUBMIT';
    }

    db.set(id, appData);
    console.log(`[Broker] Result received for ${id}.`);

    res.sendStatus(200);
});

// ------------------------------------------------------
// 4. Submit / Reject
// ------------------------------------------------------
app.post('/api/v1/applications/:id/submit', (req: Request, res: Response) => {
    const appData = db.get(req.params.id);
    if (appData) {
        appData.status = 'SUBMITTED';
        res.json({ status: 'SUBMITTED', submissionId: 'sub_999' });
    } else {
        res.status(404).send();
    }
});

// ------------------------------------------------------
// 5. Internal: Get data for validation
// ------------------------------------------------------
app.get('/api/v1/internal/applications/:applicationId/data', (req: Request, res: Response) => {
    const appId = req.params.applicationId;
    const appData = db.get(appId);

    if (!appData) {
        return res.status(404).json({ error: 'Application not found' });
    }

    // We assemble the ApplicationData object
    // In a real app we would find the Applicant based on an ID in the ApplicationState
    // const applicant = applicantsDb.get('applicant_1'); // Hardcoded for Demo
    
    // If we have the Applicant in the state, we take it from there, otherwise fallback
    const applicant = appData.applicant || applicantsDb.get('applicant_1');

    const internalData: ApplicationData = {
        applicationId: appId,
        applicant: applicant,
        submittedDocuments: appData.submittedData?.uploadedDocuments
    };

    res.json(internalData);
});

// ------------------------------------------------------
// 7. Internal: Get document
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
function simulateCloudFunction(appId: string) {
    console.log(`[MockFaaS] Starting check for ${appId}...`);

    setTimeout(() => {
        // Create type-safe mock object
        const mockResult: ValidationReport = {
            isComplete: true,
            checkedAt: new Date().toISOString(),
            overallResult: 'WARNING',
            checks: [
                {
                    checkId: 'salary',
                    title: 'Salary Check',
                    status: 'PASS',
                    message: 'Salary is sufficient.'
                },
                {
                    checkId: 'language',
                    title: 'Language Certificate B2',
                    status: 'WARNING',
                    message: 'Certificate is older than 2 years, please check manually.',
                    affectedField: 'documents.cert_b2'
                }
            ]
        };

        // Direct DB Update for Demo purposes:
        const appData = db.get(appId);
        if (appData) {
            appData.validationReport = mockResult;
            if (mockResult.overallResult === 'WARNING') {
                appData.status = 'READY_TO_SUBMIT_WITH_PROBLEMS';
            } else {
                appData.status = 'READY_TO_SUBMIT';
            }
            console.log(`[MockFaaS] Finished. Data saved.`);
        }
    }, 3000);
}

app.listen(PORT_NUMBER, '0.0.0.0', () => {
    console.log(`Broker running on port ${PORT_NUMBER}`);
    console.log(`Test-ID: 0`);
});