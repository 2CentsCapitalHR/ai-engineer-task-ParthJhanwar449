# src/processor/redflag_rules.py
import re
from typing import List, Dict

def run_redflag_checks(text: str, doc_type: str = None) -> List[Dict]:
    """
    Run comprehensive red flag checks on document text
    Returns list of issues with severity levels and suggestions
    """
    issues = []
    text_lower = text.lower()
    
    # General jurisdiction and legal framework checks
    issues.extend(_check_jurisdiction(text, text_lower))
    
    # Signature and execution checks
    issues.extend(_check_signatures(text, text_lower))
    
    # Document-specific checks
    if doc_type:
        issues.extend(_check_document_specific_issues(text, text_lower, doc_type))
    else:
        # Run all document type checks if type unknown
        issues.extend(_check_articles_of_association(text, text_lower))
        issues.extend(_check_memorandum_of_association(text, text_lower))
        issues.extend(_check_ubo_declaration(text, text_lower))
        issues.extend(_check_incorporation_application(text, text_lower))
    
    # General ADGM compliance checks
    issues.extend(_check_adgm_compliance(text, text_lower))
    
    # Language and formatting checks
    issues.extend(_check_language_and_formatting(text, text_lower))
    
    return issues

def _check_jurisdiction(text: str, text_lower: str) -> List[Dict]:
    """Check jurisdiction-related issues"""
    issues = []
    
    # Check for incorrect jurisdiction references
    if re.search(r'\buae federal court\b', text_lower):
        issues.append({
            'issue': 'References UAE Federal Courts instead of ADGM Courts',
            'severity': 'High',
            'suggestion': 'Replace with "ADGM Courts" for proper jurisdiction',
            'section': _find_section_with_text(text, 'uae federal court')
        })
    
    if re.search(r'\bdubai court\b', text_lower):
        issues.append({
            'issue': 'References Dubai Courts instead of ADGM Courts',
            'severity': 'High',
            'suggestion': 'Update jurisdiction to ADGM Courts',
            'section': _find_section_with_text(text, 'dubai court')
        })
    
    # Check for proper ADGM jurisdiction clause
    if 'jurisdiction' in text_lower and not re.search(r'\badgm court\b', text_lower):
        issues.append({
            'issue': 'Jurisdiction clause present but does not specify ADGM Courts',
            'severity': 'High',
            'suggestion': 'Specify ADGM Courts as the governing jurisdiction',
            'section': _find_section_with_text(text, 'jurisdiction')
        })
    
    # Check for UAE mainland law references
    if re.search(r'\buae civil code\b', text_lower) and not re.search(r'\badgm\b', text_lower):
        issues.append({
            'issue': 'References UAE Civil Code without ADGM context',
            'severity': 'Medium',
            'suggestion': 'Specify ADGM laws take precedence where applicable',
            'section': _find_section_with_text(text, 'uae civil code')
        })
    
    return issues

def _check_signatures(text: str, text_lower: str) -> List[Dict]:
    """Check signature and execution requirements"""
    issues = []
    
    # Check for signature blocks
    signature_patterns = [
        r'\bsignature\b', r'\bsigned by\b', r'\bfor and on behalf\b',
        r'\bexecuted\b', r'\bin witness whereof\b'
    ]
    
    has_signature = any(re.search(pattern, text_lower) for pattern in signature_patterns)
    
    if not has_signature:
        issues.append({
            'issue': 'Missing signature block or execution clause',
            'severity': 'High',
            'suggestion': 'Add proper signature block with name, title, and date fields',
            'section': 'End of document'
        })
    
    # Check for witness requirements in certain documents
    if ('deed' in text_lower or 'power of attorney' in text_lower) and 'witness' not in text_lower:
        issues.append({
            'issue': 'Document may require witness signature',
            'severity': 'Medium',
            'suggestion': 'Consider adding witness signature requirements',
            'section': _find_section_with_text(text, 'signature')
        })
    
    return issues

def _check_articles_of_association(text: str, text_lower: str) -> List[Dict]:
    """Check Articles of Association specific requirements"""
    issues = []
    
    if 'articles of association' not in text_lower:
        return issues
    
    # Share capital requirements
    if 'share capital' not in text_lower and 'shares' not in text_lower:
        issues.append({
            'issue': 'Missing share capital provisions in Articles of Association',
            'severity': 'High',
            'suggestion': 'Add clause specifying authorized share capital and classes of shares',
            'section': 'Share Capital'
        })
    
    # Directors provisions
    if 'director' not in text_lower:
        issues.append({
            'issue': 'Missing directors provisions',
            'severity': 'High',
            'suggestion': 'Add provisions for appointment and powers of directors',
            'section': 'Directors'
        })
    
    # Company objects/purpose
    if 'objects' not in text_lower and 'purpose' not in text_lower:
        issues.append({
            'issue': 'Missing company objects or purpose clause',
            'severity': 'Medium',
            'suggestion': 'Include clause defining company objects and permitted activities',
            'section': 'Company Objects'
        })
    
    return issues

def _check_memorandum_of_association(text: str, text_lower: str) -> List[Dict]:
    """Check Memorandum of Association specific requirements"""
    issues = []
    
    if 'memorandum of association' not in text_lower:
        return issues
    
    # Company name check
    if not re.search(r'\bllc\b|\blimited\b|\bltd\b', text_lower):
        issues.append({
            'issue': 'Company name may not include proper legal designation',
            'severity': 'Medium',
            'suggestion': 'Ensure company name includes LLC, Limited, or Ltd as appropriate',
            'section': 'Company Name'
        })
    
    # Registered office
    if 'registered office' not in text_lower and 'registered address' not in text_lower:
        issues.append({
            'issue': 'Missing registered office clause',
            'severity': 'High',
            'suggestion': 'Include registered office address in ADGM',
            'section': 'Registered Office'
        })
    
    return issues

def _check_ubo_declaration(text: str, text_lower: str) -> List[Dict]:
    """Check UBO Declaration specific requirements"""
    issues = []
    
    if 'ultimate beneficial owner' not in text_lower and 'ubo' not in text_lower:
        return issues
    
    # Ownership threshold
    if not re.search(r'\b25%\b|\btwenty[- ]five percent\b', text_lower):
        issues.append({
            'issue': 'Missing 25% ownership threshold reference',
            'severity': 'Medium',
            'suggestion': 'Specify 25% ownership threshold for UBO determination',
            'section': 'Ownership Threshold'
        })
    
    # Personal information requirements
    required_fields = ['full name', 'address', 'nationality', 'date of birth']
    for field in required_fields:
        if field not in text_lower:
            issues.append({
                'issue': f'May be missing {field} field for UBO',
                'severity': 'Medium',
                'suggestion': f'Ensure {field} is included for each UBO',
                'section': 'UBO Information'
            })
    
    return issues

def _check_incorporation_application(text: str, text_lower: str) -> List[Dict]:
    """Check Incorporation Application specific requirements"""
    issues = []
    
    if 'incorporation' not in text_lower and 'application' not in text_lower:
        return issues
    
    # Required application elements
    required_elements = [
        ('proposed company name', 'Company Name'),
        ('business activity', 'Business Activity'),
        ('share capital', 'Share Capital'),
        ('registered office', 'Registered Office')
    ]
    
    for element, section in required_elements:
        if element not in text_lower:
            issues.append({
                'issue': f'Missing {element} in incorporation application',
                'severity': 'High',
                'suggestion': f'Include {element} details in the application',
                'section': section
            })
    
    return issues

def _check_document_specific_issues(text: str, text_lower: str, doc_type: str) -> List[Dict]:
    """Run checks specific to the identified document type"""
    if 'articles of association' in doc_type.lower():
        return _check_articles_of_association(text, text_lower)
    elif 'memorandum of association' in doc_type.lower():
        return _check_memorandum_of_association(text, text_lower)
    elif 'ubo' in doc_type.lower():
        return _check_ubo_declaration(text, text_lower)
    elif 'incorporation' in doc_type.lower():
        return _check_incorporation_application(text, text_lower)
    else:
        return []

def _check_adgm_compliance(text: str, text_lower: str) -> List[Dict]:
    """Check general ADGM compliance issues"""
    issues = []
    
    # Check for ADGM reference
    if 'adgm' not in text_lower and 'abu dhabi global market' not in text_lower:
        issues.append({
            'issue': 'Document does not reference ADGM jurisdiction',
            'severity': 'Medium',
            'suggestion': 'Include reference to ADGM (Abu Dhabi Global Market) jurisdiction',
            'section': 'General'
        })
    
    # Check for proper currency references
    if re.search(r'\busd\b|\bus dollar\b', text_lower) and 'aed' not in text_lower:
        issues.append({
            'issue': 'References USD without AED alternative',
            'severity': 'Low',
            'suggestion': 'Consider including AED (UAE Dirham) as alternative currency',
            'section': _find_section_with_text(text, 'USD')
        })
    
    # Check for compliance statements
    compliance_terms = ['compliant', 'compliance', 'regulatory', 'regulation']
    has_compliance_ref = any(term in text_lower for term in compliance_terms)
    
    if len(text.split()) > 200 and not has_compliance_ref:  # Only for substantial documents
        issues.append({
            'issue': 'Document lacks compliance or regulatory references',
            'severity': 'Low',
            'suggestion': 'Consider adding compliance statements relevant to ADGM regulations',
            'section': 'General'
        })
    
    return issues

def _check_language_and_formatting(text: str, text_lower: str) -> List[Dict]:
    """Check language clarity and formatting issues"""
    issues = []
    
    # Check for ambiguous language
    ambiguous_phrases = [
        ('may or may not', 'Use definitive language instead of ambiguous terms'),
        ('as appropriate', 'Specify exact conditions or requirements'),
        ('if necessary', 'Define when such necessity arises'),
        ('reasonable', 'Define what constitutes reasonable in this context')
    ]
    
    for phrase, suggestion in ambiguous_phrases:
        if phrase in text_lower:
            issues.append({
                'issue': f'Ambiguous language detected: "{phrase}"',
                'severity': 'Low',
                'suggestion': suggestion,
                'section': _find_section_with_text(text, phrase)
            })
    
    # Check for proper legal language
    if 'shall' not in text_lower and 'will' in text_lower:
        issues.append({
            'issue': 'Uses "will" instead of "shall" for obligations',
            'severity': 'Low',
            'suggestion': 'Use "shall" for legal obligations and "will" for future actions',
            'section': 'General'
        })
    
    # Check for missing defined terms section
    if ('definition' not in text_lower and 'means' not in text_lower and 
        len(text.split()) > 500):  # Only for longer documents
        issues.append({
            'issue': 'Long document may benefit from definitions section',
            'severity': 'Low',
            'suggestion': 'Consider adding a definitions section for key terms',
            'section': 'Structure'
        })
    
    # Check for date formatting
    date_patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
        r'\b\d{1,2}-\d{1,2}-\d{2,4}\b'   # MM-DD-YYYY or DD-MM-YYYY
    ]
    
    for pattern in date_patterns:
        if re.search(pattern, text):
            issues.append({
                'issue': 'Date format may be ambiguous',
                'severity': 'Low',
                'suggestion': 'Use unambiguous date format (e.g., "1st January 2024")',
                'section': _find_section_with_text(text, pattern)
            })
            break
    
    return issues

def _find_section_with_text(text: str, search_term: str) -> str:
    """Find the section/paragraph containing the search term"""
    try:
        if isinstance(search_term, str):
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if search_term.lower() in line.lower():
                    # Look for section headers above this line
                    for j in range(max(0, i-5), i):
                        if lines[j].strip() and (
                            lines[j].isupper() or 
                            lines[j].startswith('Section') or
                            lines[j].startswith('Article') or
                            lines[j].endswith(':')
                        ):
                            return lines[j].strip()
                    return f"Line {i+1}"
        return "General"
    except:
        return "General"

def get_severity_score(issues: List[Dict]) -> Dict:
    """Calculate severity scores for prioritization"""
    severity_weights = {'High': 3, 'Medium': 2, 'Low': 1}
    
    total_score = 0
    severity_counts = {'High': 0, 'Medium': 0, 'Low': 0}
    
    for issue in issues:
        severity = issue.get('severity', 'Medium')
        severity_counts[severity] += 1
        total_score += severity_weights.get(severity, 2)
    
    return {
        'total_score': total_score,
        'severity_counts': severity_counts,
        'priority': 'High' if severity_counts['High'] > 0 else 'Medium' if severity_counts['Medium'] > 0 else 'Low'
    }

# Additional helper functions for document analysis
def validate_document_completeness(text: str, required_sections: List[str]) -> List[Dict]:
    """Check if document contains all required sections"""
    issues = []
    text_lower = text.lower()
    
    for section in required_sections:
        if section.lower() not in text_lower:
            issues.append({
                'issue': f'Missing required section: {section}',
                'severity': 'High',
                'suggestion': f'Add {section} section to the document',
                'section': section
            })
    
    return issues

def check_cross_references(text: str) -> List[Dict]:
    """Check for broken or unclear cross-references"""
    issues = []
    
    # Look for reference patterns that might be broken
    ref_patterns = [
        r'clause \d+\.\d+',
        r'section \d+',
        r'article \d+',
        r'paragraph \([a-z]\)',
        r'schedule \d+'
    ]
    
    for pattern in ref_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            ref = match.group()
            # This is a simplified check - in practice, you'd verify the reference exists
            if 'clause' in ref.lower() and ref.lower() not in text.lower().replace(match.group().lower(), '', 1):
                issues.append({
                    'issue': f'Potential broken cross-reference: {ref}',
                    'severity': 'Medium',
                    'suggestion': f'Verify that {ref} exists in the document',
                    'section': _find_section_with_text(text, ref)
                })
    
    return issues