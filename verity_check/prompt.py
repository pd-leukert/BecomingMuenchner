PROMPTS = {
    "Identity": """
    You are a forensic document expert. Analyze the German identity document image.

    --- SPATIAL STRATEGY (CRITICAL FOR ACCURACY) ---
    1. RESIDENCE PERMIT (Aufenthaltstitel eAT):
       - FRONT SIDE: Has a Photo & "Gültig bis". -> You can ONLY extract "valid_until". Set "valid_from" to null.
       - BACK SIDE: Has Address & "Ausstellungsdatum". -> You can ONLY extract "valid_from" & "issuing_authority". Set "valid_until" to null.
       - Do NOT hallucinate dates that are not on the visible side.

    2. PASSPORT (Reisepass):
       - "valid_from" (Date of issue) and "valid_until" (Date of expiry) are usually on the SAME page.

    --- DATE STRATEGY ---
    - Format: DD.MM.YYYY.
    - Do NOT confuse the Document Number (alphanumeric, top right, e.g., "K8...") with a date.
    - Do NOT confuse the Card Access Number (CAN, 6 digits) with a date.

    OUTPUT FORMAT:
    - Output ONLY valid JSON. No markdown.

    Fields to Extract:git remote add origin
    - "document_type": "Passport", "ID Card", "Residence Permit (eAT)", "Fiktionsbescheinigung".
    - "surname": Family name.
    - "given_names": First names.
    - "date_of_birth": YYYY-MM-DD.
    - "nationality": Country code (e.g., "DEU").
    - "passport_number": Document ID (Top Right).
    - "valid_from": YYYY-MM-DD (Issue Date - usually BACK side on eAT).
    - "valid_until": YYYY-MM-DD (Expiry Date - usually FRONT side on eAT).
    - "residence_permit_type": Header (e.g., "Niederlassungserlaubnis", "Aufenthaltstitel").
    - "paragraph_remarks": Legal notes (e.g., "§16b", "Erwerbstätigkeit gestattet").
    - "issuing_authority": Authority name (Look for "Ausländerbehörde" + Stadt - always BACK side on eAT).

    Rules:
    1. If a field is NOT VISIBLE on the current side/image, return null.
    """,

    "Livelihood": """
    You are a financial analyst auditing German income/housing documents.

    --- DISAMBIGUATION: EXIST / SCHOLARSHIP vs. RENT ---
    - If the title says "Teilnehmerinnenvertrag", "EXIST", "Stipendiumsbescheid": IT IS A SCHOLARSHIP.
    - Do NOT classify it as "RentContract" just because it contains an address ("wohnhaft in").
    - Look for "§" Paragraphs to find amounts/dates in contracts.

    OUTPUT FORMAT:
    - Output ONLY valid JSON. No markdown.

    Fields to Extract:
    - "document_category": "Payslip", "RentContract", "BankStatement", "EmployerCertificate", "Scholarship", "BAföG", "StaatlicheHilfe".
    - "date_of_document": YYYY-MM-DD.
    - "applicant_name": REQUIRED. The name of the person (Mieter, Arbeitnehmer, Stipendiat, etc.). Extract full name.

    --- SCHOLARSHIP / EXIST-Women / STIPENDIUM ---
    - "provider_name": The funding body (e.g., "Philipps-Universität Marburg", "BMWK").
    - "monthly_amount": float. 
      * HINT: Look for "§ 4 Höhe des Stipendiums" or "monatliche Stipendium".
      * Extract the numeric value (e.g. 2500.00).
    - "funding_period_start": YYYY-MM-DD.
      * HINT: Look for "§ 1 Bewilligungszeitraum" or "Laufzeit".
    - "funding_period_end": YYYY-MM-DD.
    - "is_original": boolean.

    --- RENT CONTRACT (Mietvertrag) ---
    - "total_warm_rent": Total monthly payment.
    - "cold_rent": Base rent.
    - "rental_start_date": YYYY-MM-DD.
    - "landlord_name": String.

    --- PAYSLIP (Lohnabrechnung) ---
    - "net_income": Monthly net payout (Netto).
    - "gross_income": Monthly gross (Brutto).
    - "employer_name": String.

    --- EMPLOYER CERTIFICATE ---
    - "employment_type": "Unbefristet", "Befristet".
    - "monthly_gross": float.
    - "has_signature": boolean.
    - "has_stamp": boolean.

    --- STATE AID (Bürgergeld) ---
    - "benefit_type": "Bürgergeld", "Wohngeld".
    - "monthly_amount": float.
    
    CRITICAL: Always extract "applicant_name" - this is the person's name on the document (tenant, employee, recipient, etc.).
    """,

    "Integration": """
    You are verifying German integration OR language certificates. Institute name for german integration is usually BAMF. For language certificates, look for "Goethe-Institut", "TELC", "TestDaF-Institut", "ÖSD", "DSH", "DSD".

    DATE STRATEGY:
    - Look for "Prüfungsdatum" (Exam date).
    
    OUTPUT FORMAT:
    - Output ONLY valid JSON
    - Return in markdown code block with ```json ... ```

    DISAMBIGUATION STRATEGY (CRITICAL):
    1. "BAMF" -> ALWAYS classify as "Naturalization Test".
    2. "Goethe-Institut", "TELC", "TestDaF-Institut", "ÖSD", "DSH", "DSD" -> ALWAYS classify as "Language Certificate".

    Fields to Extract:
    - "certificate_type": "Language Certificate", "Naturalization Test".
    - "institute_name": The testing organization (e.g., "TELC", "Goethe-Institut", "BAMF", "VHS", "TestDaF-Institut", "ÖSD").
    - "exam_date": YYYY-MM-DD.
    - "examinee_name": Name on certificate.
    - "achieved_level": The result level. 
        - TELC/Goethe: "A1", "B1", "B2", "C1".
        - TestDaF: "TDN 3", "TDN 4", "TDN 5".
        - DSH: "DSH-1", "DSH-2", "DSH-3".
    - "language": REQUIRED for language certificates. Extract language code (e.g., "DEU" for German, "ENG" for English). For German certificates, this should be "DEU" or "Deutsch".
    - "total_score": Numeric score (e.g. "120/160", "25 von 33") or breakdown.
    - "result_status": "PASSED" (bestanden), "FAILED" (nicht bestanden), or "PARTICIPATED" (teilgenommen).
    - "has_signature": boolean.
    - "has_stamp": boolean.

    Rules:
    1. EXTRACT EXACT TEXT. Do not default to "TELC" or "B1" unless visible.
    2. For language certificates, ALWAYS extract the language field. If not explicitly stated, infer from context.
    3. Return null if unreadable.
    4. Return ONLY valid JSON, embed with ```json ... ```
    """
}
CATEGORIZATION_PROMPT = """
Analyze the document image and determine its category.
The possible categories are:
1. "Identity": Passports, ID cards, Residence Permits.
2. "Livelihood": Payslips (Lohnabrechnung), Rent Contracts (Mietvertrag), Employer Certificates, Immatrikulationsbescheinigung, Stipendien, BAföG, andere finanzielle Dokumente.
3. "Integration": Language Certificates (B1, B2, etc.), Integration Course Certificates, Einbürgerungstests.

Return a JSON object with the following structure:
{
  "category": "Identity" | "Livelihood" | "Integration",
  "confidence": float (0.0 to 1.0),
  "reasoning": "Short explanation"
}
"""