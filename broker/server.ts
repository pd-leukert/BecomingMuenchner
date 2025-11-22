import express from 'express';
import type { Request, Response } from 'express';
import cors from 'cors';

// 1. IMPORT: Wir importieren das riesige 'components' Objekt aus deiner generierten Datei
import type { components } from './src/types.ts';

// 2. TYPEN MAPPING: Wir ziehen uns die relevanten Schemas in handliche Variablen
type ApplicationState = components['schemas']['ApplicationState'];
type ValidationReport = components['schemas']['ValidationReport'];
type ApplicantDetails = components['schemas']['ApplicantDetails'];
type ApplicationData = components['schemas']['ApplicationData'];
// Optional: Falls du tiefer liegende Typen brauchst:
// type CheckResult = components['schemas']['CheckResult'];

const app = express();
app.use(cors());
app.use(express.json());

const PORT_NUMBER = parseInt(process.env.PORT || '8080', 10);

// --- HACKATHON DATABASE (In-Memory) ---
// Jetzt ist die Map typsicher! TypeScript wird meckern, wenn Mock-Daten falsch sind.
const db = new Map<string, ApplicationState>();
const applicantsDb = new Map<string, ApplicantDetails>();

// Mock-Daten initialisieren
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
    status: 'DRAFT', // Muss einer der Enum-Werte aus der YAML sein!
    submittedData: {
        uploadedDocuments: [
            { docId: 'doc_1', type: 'passport', filename: 'pass.pdf', url: '/files/pass.pdf' },
            { docId: 'doc_2', type: 'salary_slip', filename: 'gehalt.pdf', url: '/files/gehalt.pdf' }
        ]
    },
    validationReport: {
        isComplete: false,
        checks: [] // Initial leeres Array
    }
});

applicantsDb.set('applicant_1', {
    firstName: 'Erika',
    lastName: 'Musterfrau',
    email: 'erika.musterfrau@example.com',
    address: 'Musterstraße 1, 80331 München'
});

// ------------------------------------------------------
// 1. GET /applications/{id} - Status abfragen (Polling)
// ------------------------------------------------------
app.get('/api/v1/applications/:id', (req: Request, res: Response) => {
    const appData = db.get(req.params.id);

    if (!appData) {
        return res.status(404).json({ error: 'Antrag nicht gefunden' });
    }

    res.json(appData);
});

// ------------------------------------------------------
// 2. POST /applications/{id}/start-validation - Prozess explizit starten
// ------------------------------------------------------
app.post('/api/v1/applications/:id/start-validation', async (req: Request, res: Response) => {
    const id = req.params.id;
    const appData = db.get(id);

    if (!appData) {
        return res.status(404).json({ error: 'Not found' });
    }

    // 1. Status updaten
    appData.status = 'VALIDATING';
    appData.validationReport = {
        isComplete: false,
        overallResult: 'PENDING',
        checks: []
    };
    db.set(id, appData);

    // 2. Asynchron die "Cloud Function" triggern
    simulateCloudFunction(id);

    res.status(202).json({ message: 'Validation started.' });
});

// ------------------------------------------------------
// 3. POST /internal/... - Callback von der FaaS
// ------------------------------------------------------
app.post('/api/v1/internal/applications/:id/validation-result', (req: Request, res: Response) => {
    const id = req.params.id;

    // WICHTIG: Express weiß nicht, was im Body ist. Wir müssen es "casten".
    const result = req.body as ValidationReport;

    const appData = db.get(id);
    if (!appData) return res.status(404).send();

    // Ergebnis speichern
    appData.validationReport = result;

    // Globalen Status ableiten
    if (result.overallResult === 'CRITICAL_ERROR') {
        // Logik: Bei Fehler bleibt es sichtbar, oder Status ändert sich
        // Wir lassen es hier mal auf VALIDATING oder setzen es auf einen Fehlerstatus, 
        // aber laut Enum gibt es keinen expliziten ERROR Status für den Antrag, nur im Report.
        // Eventuell könnte man es auf DRAFT zurücksetzen?
    } else if (result.overallResult === 'WARNING') {
        appData.status = 'READY_TO_SUBMIT_WITH_PROBLEMS';
    } else {
        appData.status = 'READY_TO_SUBMIT';
    }

    db.set(id, appData);
    console.log(`[Broker] Ergebnis für ${id} empfangen.`);

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
// 5. Internal: Daten für Validierung abrufen
// ------------------------------------------------------
app.get('/api/v1/internal/applications/:applicationId/data', (req: Request, res: Response) => {
    const appId = req.params.applicationId;
    const appData = db.get(appId);

    if (!appData) {
        return res.status(404).json({ error: 'Application not found' });
    }

    // Wir bauen das ApplicationData Objekt zusammen
    // In einer echten App würden wir den Applicant anhand einer ID im ApplicationState finden
    // const applicant = applicantsDb.get('applicant_1'); // Hardcoded für Demo
    
    // Falls wir den Applicant im State haben, nehmen wir ihn von dort, sonst Fallback
    const applicant = appData.applicant || applicantsDb.get('applicant_1');

    const internalData: ApplicationData = {
        applicationId: appId,
        applicant: applicant,
        submittedDocuments: appData.submittedData?.uploadedDocuments
    };

    res.json(internalData);
});

// ------------------------------------------------------
// 7. Internal: Dokument abrufen
// ------------------------------------------------------
app.get('/api/v1/internal/documents/:documentId', (req: Request, res: Response) => {
    const docId = req.params.documentId;
    // Mock: Wir geben einfach immer Erfolg zurück, Inhalt ist hier egal für den Broker
    // In echt würde man den File Stream aus S3/Disk pipen.
    console.log(`[Broker] Serving document ${docId}`);
    res.setHeader('Content-Type', 'application/pdf');
    res.send('PDF-CONTENT-MOCK'); 
});


// --- SIMULATION DER CLOUD FUNCTION (Mock) ---
function simulateCloudFunction(appId: string) {
    console.log(`[MockFaaS] Starte Prüfung für ${appId}...`);

    setTimeout(() => {
        // Typsicheres Mock-Objekt erstellen
        const mockResult: ValidationReport = {
            isComplete: true,
            checkedAt: new Date().toISOString(),
            overallResult: 'WARNING',
            checks: [
                {
                    checkId: 'salary',
                    title: 'Gehaltscheck',
                    status: 'PASS',
                    message: 'Gehalt ist ausreichend.'
                },
                {
                    checkId: 'language',
                    title: 'Sprachzertifikat B2',
                    status: 'WARNING',
                    message: 'Zertifikat ist älter als 2 Jahre, bitte manuell prüfen.',
                    affectedField: 'documents.cert_b2'
                }
            ]
        };

        // Hier direkt DB Update für Demo-Zwecke:
        const appData = db.get(appId);
        if (appData) {
            appData.validationReport = mockResult;
            if (mockResult.overallResult === 'WARNING') {
                appData.status = 'READY_TO_SUBMIT_WITH_PROBLEMS';
            } else {
                appData.status = 'READY_TO_SUBMIT';
            }
            console.log(`[MockFaaS] Fertig. Daten gespeichert.`);
        }
    }, 3000);
}

app.listen(PORT_NUMBER, '0.0.0.0', () => {
    console.log(`Broker läuft auf Port ${PORT_NUMBER}`);
    console.log(`Test-ID: 12345-abcde`);
});