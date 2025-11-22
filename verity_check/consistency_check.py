import networkx as nx
from typing import List, Dict, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import re

def fuzzy_match(str1: str, str2: str) -> float:
    """Returns similarity score between 0 and 1."""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def parse_date(date_str: str) -> datetime:
    """Parses date string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d")
    except:
        try:
            return datetime.strptime(str(date_str), "%d.%m.%Y")
        except:
            return None

def extract_paragraph_number(paragraph_str: str) -> str:
    """Extracts paragraph number from string like '§16b' or '16B ABS.1'."""
    if not paragraph_str:
        return None
    cleaned = paragraph_str.replace("§", "").strip().lower()
    match = re.match(r'(\d+[a-z]?)', cleaned)
    if match:
        return match.group(1)
    return None

def get_documents_by_category(G: nx.DiGraph) -> Dict[str, List[str]]:
    """Returns documents grouped by category."""
    doc_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'Document']
    return {
        'identity': [n for n in doc_nodes if G.nodes[n].get('category') == 'Identity'],
        'livelihood': [n for n in doc_nodes if G.nodes[n].get('category') == 'Livelihood'],
        'integration': [n for n in doc_nodes if G.nodes[n].get('category') == 'Integration']
    }

# ========== CHECK 1: NAME CONSISTENCY ==========
def check_name_consistency(G: nx.DiGraph, identity_docs: List[str], integration_docs: List[str]) -> List[Dict[str, Any]]:
    """Check 1.1: Name consistency across documents."""
    alerts = []
    person_names = []
    
    # Collect person names from Identity docs (surname + given_names)
    for doc in identity_docs:
        filename = G.nodes[doc].get('filename', '')
        surname = None
        given_names = None
        
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            field = node_data.get('field')
            if field == 'surname':
                surname = node_data.get('value', '')
            elif field == 'given_names':
                given_names = node_data.get('value', '')
        
        if surname and given_names:
            full_name = f"{given_names} {surname}".strip()
            person_names.append({'name': full_name, 'filename': filename})
    
    # Collect examinee_name from Integration docs
    for doc in integration_docs:
        filename = G.nodes[doc].get('filename', '')
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            if node_data.get('field') == 'examinee_name':
                name = node_data.get('value', '')
                name = name.replace('Frau ', '').replace('Herr ', '').replace('frau ', '').replace('herr ', '').strip()
                person_names.append({'name': name, 'filename': filename})
    
    # Collect applicant_name from Livelihood docs (tenant, employee, etc.)
    livelihood_docs = [n for n, d in G.nodes(data=True) if d.get('type') == 'Document' and d.get('category') == 'Livelihood']
    for doc in livelihood_docs:
        filename = G.nodes[doc].get('filename', '')
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            if node_data.get('field') == 'applicant_name':
                name = node_data.get('value', '')
                name = name.replace('Frau ', '').replace('Herr ', '').replace('frau ', '').replace('herr ', '').strip()
                person_names.append({'name': name, 'filename': filename})
    
    # Compare all person names pairwise
    for i, name1 in enumerate(person_names):
        for name2 in person_names[i+1:]:
            similarity = fuzzy_match(name1['name'], name2['name'])
            if similarity < 0.9:
                alerts.append({
                    'severity': 'HIGH',
                    'check': 'Name Consistency',
                    'message': f"Namensabweichung erkannt: '{name1['name']}' vs '{name2['name']}' (Similarity: {similarity:.0%})",
                    'filenames': [name1['filename'], name2['filename']]
                })
    
    return alerts

# ========== CHECK 2: DATE OF BIRTH CONSISTENCY ==========
def check_dob_consistency(G: nx.DiGraph, identity_docs: List[str]) -> List[Dict[str, Any]]:
    """Check 1.2: Date of birth consistency."""
    alerts = []
    all_dobs = []
    
    for doc in identity_docs:
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            if node_data.get('field') == 'date_of_birth':
                all_dobs.append({
                    'dob': node_data.get('value', ''),
                    'filename': G.nodes[doc].get('filename', '')
                })
    
    if len(all_dobs) > 1:
        first_dob = all_dobs[0]['dob']
        for dob_entry in all_dobs[1:]:
            if dob_entry['dob'] != first_dob:
                alerts.append({
                    'severity': 'HIGH',
                    'check': 'Date of Birth Consistency',
                    'message': f"Geburtsdatum-Abweichung: '{first_dob}' vs '{dob_entry['dob']}'",
                    'filenames': [all_dobs[0]['filename'], dob_entry['filename']]
                })
    
    return alerts

# ========== CHECK 3: PASSPORT VALIDITY ==========
def check_passport_validity(G: nx.DiGraph, identity_docs: List[str]) -> List[Dict[str, Any]]:
    """Check 1.3: Passport validity (must be valid for 2+ months)."""
    alerts = []
    
    for doc in identity_docs:
        filename = G.nodes[doc].get('filename', '')
        is_passport = False
        valid_until = None
        
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            if node_data.get('field') == 'document_type' and 'Passport' in str(node_data.get('value', '')):
                is_passport = True
            elif node_data.get('field') == 'valid_until':
                valid_until = parse_date(node_data.get('value'))
        
        if is_passport and valid_until:
            two_months_from_now = datetime.now() + timedelta(days=60)
            if valid_until < two_months_from_now:
                alerts.append({
                    'severity': 'HIGH',
                    'check': 'Passport Validity',
                    'message': f"Pass läuft bald ab oder ist abgelaufen: {valid_until.date()}",
                    'filenames': [filename]
                })
    
    return alerts

# ========== CHECK 4: NATIONALITY ==========
def check_nationality(G: nx.DiGraph, identity_docs: List[str]) -> List[Dict[str, Any]]:
    """Check 1.4: Nationality must not be null/ungeklärt/staatenlos."""
    alerts = []
    
    for doc in identity_docs:
        filename = G.nodes[doc].get('filename', '')
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            if node_data.get('field') == 'nationality':
                nationality = str(node_data.get('value', '')).lower()
                if nationality in ['null', 'none', '', 'ungeklärt', 'staatenlos']:
                    alerts.append({
                        'severity': 'HIGH',
                        'check': 'Nationality',
                        'message': f"Nationalität ist ungültig oder fehlt: '{nationality}'",
                        'filenames': [filename]
                    })
    
    return alerts

# ========== CHECK 5: RESIDENCE PERMIT EXISTENCE ==========
def check_permit_existence(G: nx.DiGraph, identity_docs: List[str]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Check 2.1: Residence permit must exist. Returns (alerts, permits)."""
    alerts = []
    residence_permits = []
    
    for doc in identity_docs:
        filename = G.nodes[doc].get('filename', '')
        is_permit = False
        permit_data = {'filename': filename}
        
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            field = node_data.get('field')
            
            if field == 'document_type' and 'Residence Permit' in str(node_data.get('value', '')):
                is_permit = True
            elif field == 'valid_until':
                permit_data['valid_until'] = parse_date(node_data.get('value'))
            elif field == 'valid_from':
                permit_data['valid_from'] = parse_date(node_data.get('value'))
            elif field == 'paragraph_remarks':
                permit_data['paragraph'] = node_data.get('value')
        
        if is_permit:
            residence_permits.append(permit_data)
    
    if not residence_permits:
        alerts.append({
            'severity': 'HIGH',
            'check': 'Residence Permit Existence',
            'message': 'Kein Aufenthaltstitel gefunden!',
            'filenames': []
        })
    
    return alerts, residence_permits

# ========== CHECK 6: RESIDENCE PERMIT VALIDITY ==========
def check_permit_validity(residence_permits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check 2.2: Latest permit must be valid for 2+ months."""
    alerts = []
    
    if residence_permits:
        residence_permits.sort(key=lambda x: x.get('valid_from', datetime.min), reverse=True)
        latest_permit = residence_permits[0]
        
        if 'valid_until' in latest_permit:
            two_months_from_now = datetime.now() + timedelta(days=60)
            if latest_permit['valid_until'] < two_months_from_now:
                alerts.append({
                    'severity': 'HIGH',
                    'check': 'Residence Permit Validity',
                    'message': f"Aufenthaltstitel läuft bald ab: {latest_permit['valid_until'].date()}",
                    'filenames': [latest_permit['filename']]
                })
    
    return alerts

# ========== CHECK 7: RESIDENCE PERMIT PARAGRAPH ==========
def check_permit_paragraph(residence_permits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check 2.3: Permit paragraph must not be in blocked list."""
    alerts = []
    blocked_paragraphs = ['16a', '16b', '16d', '16e', '16f', '17', '18f', '19', '19b', '19e', '20', '22', '23a', '24', '104c']
    
    if residence_permits:
        residence_permits.sort(key=lambda x: x.get('valid_from', datetime.min), reverse=True)
        latest_permit = residence_permits[0]
        
        if 'paragraph' in latest_permit:
            para_num = extract_paragraph_number(latest_permit['paragraph'])
            if para_num and para_num in blocked_paragraphs:
                alerts.append({
                    'severity': 'HIGH',
                    'check': 'Residence Permit Paragraph',
                    'message': f"Aufenthaltstitel mit blockiertem Paragraphen: §{para_num}",
                    'filenames': [latest_permit['filename']]
                })
    
    return alerts

# ========== CHECK 8: RESIDENCE DURATION ==========
def check_residence_duration(residence_permits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check 3.1: Total residence duration must be >= 5 years."""
    alerts = []
    
    if residence_permits:
        total_days = 0
        for permit in residence_permits:
            if 'valid_from' in permit and 'valid_until' in permit:
                duration = (permit['valid_until'] - permit['valid_from']).days
                total_days += duration
        
        total_years = total_days / 365.25
        if total_years < 5:
            alerts.append({
                'severity': 'HIGH',
                'check': 'Residence Duration',
                'message': f"Aufenthaltsdauer zu kurz: {total_years:.1f} Jahre (mindestens 5 Jahre erforderlich)",
                'filenames': [p['filename'] for p in residence_permits]
            })
    
    return alerts

# ========== CHECK 9: RESIDENCE CONTINUITY ==========
def check_residence_continuity(residence_permits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check 3.2: Gaps between permits must be <= 6 months."""
    alerts = []
    
    if len(residence_permits) > 1:
        sorted_permits = sorted(residence_permits, key=lambda x: x.get('valid_from', datetime.min))
        for i in range(len(sorted_permits) - 1):
            end_current = sorted_permits[i].get('valid_until')
            start_next = sorted_permits[i+1].get('valid_from')
            if end_current and start_next:
                gap_days = (start_next - end_current).days
                if gap_days > 180:
                    alerts.append({
                        'severity': 'HIGH',
                        'check': 'Residence Continuity',
                        'message': f"Lücke im Aufenthalt: {gap_days} Tage zwischen Titeln (max. 180 Tage erlaubt)",
                        'filenames': [sorted_permits[i]['filename'], sorted_permits[i+1]['filename']]
                    })
    
    return alerts

# ========== CHECK 10: NO STATE BENEFITS ==========
def check_no_state_benefits(G: nx.DiGraph, livelihood_docs: List[str]) -> List[Dict[str, Any]]:
    """Check 4.1: Must not receive Bürgergeld/SGB II."""
    alerts = []
    
    for doc in livelihood_docs:
        filename = G.nodes[doc].get('filename', '')
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            if node_data.get('field') == 'benefit_type':
                benefit = str(node_data.get('value', '')).lower()
                if 'bürgergeld' in benefit or 'sgb ii' in benefit:
                    alerts.append({
                        'severity': 'HIGH',
                        'check': 'State Benefits',
                        'message': f"Bezug von Bürgergeld/SGB II festgestellt - Einbürgerung blockiert",
                        'filenames': [filename]
                    })
    
    return alerts

# ========== CHECK 11: LIVELIHOOD CALCULATION ==========
def check_livelihood_calculation(G: nx.DiGraph, livelihood_docs: List[str]) -> List[Dict[str, Any]]:
    """Check 4.2: Income - Rent must be > €563 (Regelsatz)."""
    alerts = []
    income = 0
    rent = 0
    income_files = []
    rent_files = []
    
    for doc in livelihood_docs:
        filename = G.nodes[doc].get('filename', '')
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            field = node_data.get('field')
            value = node_data.get('value')
            
            if field == 'monthly_amount' and isinstance(value, (int, float)):
                income += value
                income_files.append(filename)
            elif field == 'net_income' and isinstance(value, (int, float)):
                income += value
                income_files.append(filename)
            elif field == 'total_warm_rent' and isinstance(value, (int, float)):
                rent += value
                rent_files.append(filename)
    
    # Check for missing income
    if income == 0:
        alerts.append({
            'severity': 'HIGH',
            'check': 'Livelihood Calculation',
            'message': 'Kein Einkommen nachgewiesen (Stipendium, Gehalt, etc.)',
            'filenames': []
        })
    
    # Check for missing rent
    if rent == 0:
        alerts.append({
            'severity': 'HIGH',
            'check': 'Livelihood Calculation',
            'message': 'Kein Mietvertrag gefunden',
            'filenames': []
        })
    
    # Calculate if both are present
    if income > 0 and rent > 0:
        remaining = income - rent
        regelsatz = 563
        if remaining < regelsatz:
            alerts.append({
                'severity': 'HIGH',
                'check': 'Livelihood Calculation',
                'message': f"Lebensunterhalt nicht gesichert: €{income:.2f} - €{rent:.2f} = €{remaining:.2f} < €{regelsatz} (Regelsatz)",
                'filenames': list(set(income_files + rent_files))
            })
    
    return alerts

# ========== CHECK 12: LANGUAGE CERTIFICATE ==========
def check_language_certificate(G: nx.DiGraph, integration_docs: List[str]) -> List[Dict[str, Any]]:
    """Check 5: Language certificate B1 or higher from accepted institute for GERMAN language."""
    alerts = []
    accepted_institutes = ['telc', 'goethe', 'testdaf', 'ösd', 'dsh', 'dtz', 'bamf']
    min_levels = ['b1', 'b2', 'c1', 'c2', 'dsh-1', 'dsh-2', 'dsh-3']
    language_cert_found = False
    
    for doc in integration_docs:
        filename = G.nodes[doc].get('filename', '')
        cert_type = None
        institute = None
        level = None
        language = None
        
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            field = node_data.get('field')
            value = str(node_data.get('value', '')).lower()
            
            if field == 'certificate_type' and 'language' in value:
                cert_type = 'language'
            elif field == 'institute_name':
                institute = value
            elif field == 'achieved_level':
                level = value
            elif field == 'language':
                language = value
        
        if cert_type == 'language':
            language_cert_found = True
            
            # Check language is German
            if language and language not in ['deu', 'de', 'german', 'deutsch']:
                alerts.append({
                    'severity': 'HIGH',
                    'check': 'Language Certificate Language',
                    'message': f"Sprachzertifikat nicht für Deutsch: {language} (muss DEU/Deutsch sein)",
                    'filenames': [filename]
                })
            
            # Check institute
            if institute and not any(acc in institute for acc in accepted_institutes):
                alerts.append({
                    'severity': 'HIGH',
                    'check': 'Language Certificate Institute',
                    'message': f"Sprachzertifikat von nicht anerkanntem Institut: {institute}",
                    'filenames': [filename]
                })
            
            # Check level
            if level and not any(ml in level for ml in min_levels):
                alerts.append({
                    'severity': 'HIGH',
                    'check': 'Language Certificate Level',
                    'message': f"Sprachniveau zu niedrig: {level} (mindestens B1 erforderlich)",
                    'filenames': [filename]
                })
    
    if not language_cert_found:
        alerts.append({
            'severity': 'HIGH',
            'check': 'Language Certificate',
            'message': 'Kein Sprachzertifikat gefunden!',
            'filenames': []
        })
    
    return alerts

# ========== CHECK 13: NATURALIZATION TEST ==========
def check_naturalization_test(G: nx.DiGraph, integration_docs: List[str]) -> List[Dict[str, Any]]:
    """Check 6: Naturalization test must be passed."""
    alerts = []
    naturalization_test_found = False
    
    for doc in integration_docs:
        filename = G.nodes[doc].get('filename', '')
        cert_type = None
        result = None
        
        for neighbor in G.neighbors(doc):
            node_data = G.nodes[neighbor]
            field = node_data.get('field')
            value = str(node_data.get('value', '')).lower()
            
            if field == 'certificate_type' and 'naturalization' in value:
                cert_type = 'naturalization'
            elif field == 'result_status':
                result = value
        
        if cert_type == 'naturalization':
            naturalization_test_found = True
            
            if result and 'passed' not in result and 'bestanden' not in result:
                alerts.append({
                    'severity': 'HIGH',
                    'check': 'Naturalization Test Result',
                    'message': f"Einbürgerungstest nicht bestanden: {result}",
                    'filenames': [filename]
                })
    
    if not naturalization_test_found:
        alerts.append({
            'severity': 'HIGH',
            'check': 'Naturalization Test',
            'message': 'Kein Einbürgerungstest-Zertifikat gefunden!',
            'filenames': []
        })
    
    return alerts

# ========== MAIN ORCHESTRATOR ==========
def run_checks(G: nx.DiGraph) -> List[Dict[str, Any]]:
    """
    Runs all consistency checks on the knowledge graph.
    Returns a list of alerts.
    """
    all_alerts = []
    
    # Get documents by category
    docs = get_documents_by_category(G)
    identity_docs = docs['identity']
    livelihood_docs = docs['livelihood']
    integration_docs = docs['integration']
    
    # Run all checks
    all_alerts.extend(check_name_consistency(G, identity_docs, integration_docs))
    all_alerts.extend(check_dob_consistency(G, identity_docs))
    all_alerts.extend(check_passport_validity(G, identity_docs))
    all_alerts.extend(check_nationality(G, identity_docs))
    
    permit_alerts, residence_permits = check_permit_existence(G, identity_docs)
    all_alerts.extend(permit_alerts)
    all_alerts.extend(check_permit_validity(residence_permits))
    all_alerts.extend(check_permit_paragraph(residence_permits))
    all_alerts.extend(check_residence_duration(residence_permits))
    all_alerts.extend(check_residence_continuity(residence_permits))
    
    all_alerts.extend(check_no_state_benefits(G, livelihood_docs))
    all_alerts.extend(check_livelihood_calculation(G, livelihood_docs))
    
    all_alerts.extend(check_language_certificate(G, integration_docs))
    all_alerts.extend(check_naturalization_test(G, integration_docs))
    
    return all_alerts
