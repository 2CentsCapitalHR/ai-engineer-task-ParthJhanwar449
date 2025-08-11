# src/processor/type_detector.py
import re
from typing import List, Dict, Tuple

# Document type patterns with confidence scoring
DOCUMENT_PATTERNS = {
    "Articles of Association": {
        "primary_keywords": ["articles of association", "articles of incorporation"],
        "secondary_keywords": ["share capital", "directors", "shareholders", "company constitution"],
        "exclusion_keywords": ["memorandum"],
        "structure_indicators": ["article 1", "article 2", "clause"],
        "confidence_threshold": 0.6
    },
    "Memorandum of Association": {
        "primary_keywords": ["memorandum of association", "memorandum of incorporation"],
        "secondary_keywords": ["company name", "registered office", "objects", "liability"],
        "exclusion_keywords": ["articles"],
        "structure_indicators": ["whereas", "now therefore"],
        "confidence_threshold": 0.6
    },
    "UBO Declaration": {
        "primary_keywords": ["ultimate beneficial owner", "ubo declaration", "beneficial ownership"],
        "secondary_keywords": ["25%", "twenty-five percent", "ownership", "control"],
        "exclusion_keywords": [],
        "structure_indicators": ["declare", "confirm", "certify"],
        "confidence_threshold": 0.5
    },
    "Register of Members and Directors": {
        "primary_keywords": ["register of members", "register of directors", "members register"],
        "secondary_keywords": ["shareholder", "director", "appointment", "resignation"],
        "exclusion_keywords": [],
        "structure_indicators": ["name", "address", "shares held", "date of appointment"],
        "confidence_threshold": 0.5
    },
    "Incorporation Application": {
        "primary_keywords": ["incorporation application", "application for incorporation", "company formation"],
        "secondary_keywords": ["proposed name", "business activity", "applicant"],
        "exclusion_keywords": [],
        "structure_indicators": ["applicant details", "proposed activities"],
        "confidence_threshold": 0.5
    },
    "Board Resolution": {
        "primary_keywords": ["board resolution", "directors' resolution", "board meeting"],
        "secondary_keywords": ["resolved", "directors", "meeting", "unanimous"],
        "exclusion_keywords": ["shareholder"],
        "structure_indicators": ["it was resolved", "resolved that", "meeting held"],
        "confidence_threshold": 0.5
    },
    "Shareholder Resolution": {
        "primary_keywords": ["shareholder resolution", "shareholders' resolution", "general meeting"],
        "secondary_keywords": ["resolved", "shareholders", "meeting", "ordinary resolution"],
        "exclusion_keywords": ["board", "directors"],
        "structure_indicators": ["it was resolved", "resolved that", "meeting held"],
        "confidence_threshold": 0.5
    },
    "Employment Contract": {
        "primary_keywords": ["employment contract", "employment agreement", "service agreement"],
        "secondary_keywords": ["employee", "employer", "salary", "termination", "duties"],
        "exclusion_keywords": [],
        "structure_indicators": ["terms of employment", "job description", "remuneration"],
        "confidence_threshold": 0.5
    },
    "Commercial License Application": {
        "primary_keywords": ["commercial license", "license application", "business license"],
        "secondary_keywords": ["trade name", "business activity", "premises"],
        "exclusion_keywords": [],
        "structure_indicators": ["license details", "business activities"],
        "confidence_threshold": 0.5
    },
    "Power of Attorney": {
        "primary_keywords": ["power of attorney", "poa", "attorney"],
        "secondary_keywords": ["appoint", "attorney", "behalf", "authorize"],
        "exclusion_keywords": [],
        "structure_indicators": ["hereby appoint", "full power", "in witness whereof"],
        "confidence_threshold": 0.5
    },
    "Lease Agreement": {
        "primary_keywords": ["lease agreement", "tenancy agreement", "rental agreement"],
        "secondary_keywords": ["landlord", "tenant", "premises", "rent", "lease term"],
        "exclusion_keywords": [],
        "structure_indicators": ["lease term", "rental amount", "premises description"],
        "confidence_threshold": 0.5
    },
    "Non-Disclosure Agreement": {
        "primary_keywords": ["non-disclosure agreement", "nda", "confidentiality agreement"],
        "secondary_keywords": ["confidential", "proprietary", "disclosure", "information"],
        "exclusion_keywords": [],
        "structure_indicators": ["confidential information", "non-disclosure"],
        "confidence_threshold": 0.5
    }
}

def detect_doc_type(text: str, return_confidence: bool = False) -> List[str]:
    """
    Detect document type(s) from text with confidence scoring
    
    Args:
        text: Document text to analyze
        return_confidence: If True, returns (type, confidence) tuples
    
    Returns:
        List of detected document types or (type, confidence) tuples
    """
    if not text or not text.strip():
        return ["Unknown"] if not return_confidence else [("Unknown", 0.0)]
    
    text_lower = text.lower()
    text_normalized = re.sub(r'\s+', ' ', text_lower)
    
    detected_types = []
    
    for doc_type, patterns in DOCUMENT_PATTERNS.items():
        confidence = _calculate_confidence(text_normalized, patterns)
        
        if confidence >= patterns["confidence_threshold"]:
            if return_confidence:
                detected_types.append((doc_type, confidence))
            else:
                detected_types.append(doc_type)
    
    # Sort by confidence if returning confidence scores
    if return_confidence and detected_types:
        detected_types.sort(key=lambda x: x[1], reverse=True)
    
    # If no types detected, try fallback detection
    if not detected_types:
        fallback_type = _fallback_detection(text_normalized)
        if return_confidence:
            detected_types.append((fallback_type, 0.3))
        else:
            detected_types.append(fallback_type)
    
    return detected_types

def _calculate_confidence(text: str, patterns: Dict) -> float:
    """Calculate confidence score for a document type"""
    score = 0.0
    total_possible = 0
    
    # Primary keywords (highest weight)
    primary_weight = 0.5
    primary_found = 0
    for keyword in patterns["primary_keywords"]:
        total_possible += primary_weight
        if keyword in text:
            primary_found += 1
            score += primary_weight
    
    # Bonus if multiple primary keywords found
    if primary_found > 1:
        score += 0.1
    
    # Secondary keywords (medium weight)
    secondary_weight = 0.1
    secondary_found = 0
    for keyword in patterns["secondary_keywords"]:
        total_possible += secondary_weight
        if keyword in text:
            secondary_found += 1
            score += secondary_weight
    
    # Structure indicators (medium weight)
    structure_weight = 0.15
    structure_found = 0
    for indicator in patterns["structure_indicators"]:
        total_possible += structure_weight
        if indicator in text:
            structure_found += 1
            score += structure_weight
    
    # Penalty for exclusion keywords
    exclusion_penalty = 0.2
    for exclusion in patterns["exclusion_keywords"]:
        if exclusion in text:
            score -= exclusion_penalty
    
    # Normalize score
    if total_possible > 0:
        confidence = min(score / total_possible, 1.0)
    else:
        confidence = 0.0
    
    return max(confidence, 0.0)

def _fallback_detection(text: str) -> str:
    """Fallback detection for unrecognized documents"""
    
    # Check for common legal document indicators
    legal_indicators = [
        ("contract", "Contract"),
        ("agreement", "Agreement"), 
        ("resolution", "Resolution"),
        ("application", "Application"),
        ("declaration", "Declaration"),
        ("certificate", "Certificate"),
        ("notice", "Notice"),
        ("policy", "Policy"),
        ("procedure", "Procedure"),
        ("form", "Form")
    ]
    
    for indicator, doc_type in legal_indicators:
        if indicator in text:
            return f"General {doc_type}"
    
    # Check document length to guess type
    word_count = len(text.split())
    if word_count < 100:
        return "Short Form/Notice"
    elif word_count > 2000:
        return "Complex Legal Document"
    else:
        return "Standard Business Document"

def get_document_requirements(doc_type: str) -> Dict:
    """Get typical requirements for a document type"""
    requirements = {
        "Articles of Association": {
            "required_sections": ["Company Name", "Share Capital", "Directors", "Objects"],
            "typical_clauses": ["Liability Limitation", "Share Transfer", "Board Powers"],
            "signatures_required": ["Directors", "Shareholders"],
            "witnesses_required": False
        },
        "Memorandum of Association": {
            "required_sections": ["Company Name", "Registered Office", "Objects", "Liability"],
            "typical_clauses": ["Subscriber Details", "Share Capital"],
            "signatures_required": ["Subscribers"],
            "witnesses_required": True
        },
        "UBO Declaration": {
            "required_sections": ["Personal Details", "Ownership Details", "Declaration"],
            "typical_clauses": ["25% Threshold", "Control Definition"],
            "signatures_required": ["UBO", "Company Officer"],
            "witnesses_required": False
        },
        "Board Resolution": {
            "required_sections": ["Meeting Details", "Resolutions", "Voting"],
            "typical_clauses": ["Meeting Notice", "Quorum", "Unanimous Consent"],
            "signatures_required": ["Directors"],
            "witnesses_required": False
        },
        "Employment Contract": {
            "required_sections": ["Parties", "Job Description", "Remuneration", "Termination"],
            "typical_clauses": ["Confidentiality", "Non-Compete", "Benefits"],
            "signatures_required": ["Employee", "Employer"],
            "witnesses_required": False
        }
    }
    
    return requirements.get(doc_type, {
        "required_sections": [],
        "typical_clauses": [],
        "signatures_required": ["Parties"],
        "witnesses_required": False
    })

def analyze_document_completeness(text: str, doc_types: List[str]) -> Dict:
    """Analyze document completeness based on detected types"""
    analysis = {
        "detected_types": doc_types,
        "completeness_score": 0.0,
        "missing_elements": [],
        "present_elements": []
    }
    
    if not doc_types or doc_types == ["Unknown"]:
        return analysis
    
    # Analyze primary document type
    primary_type = doc_types[0]
    requirements = get_document_requirements(primary_type)
    
    text_lower = text.lower()
    
    # Check required sections
    total_requirements = len(requirements.get("required_sections", []))
    present_count = 0
    
    for section in requirements.get("required_sections", []):
        if section.lower() in text_lower:
            analysis["present_elements"].append(section)
            present_count += 1
        else:
            analysis["missing_elements"].append(section)
    
    # Check signatures
    signature_indicators = ["signature", "signed", "executed", "witness"]
    has_signatures = any(indicator in text_lower for indicator in signature_indicators)
    
    if requirements.get("signatures_required") and not has_signatures:
        analysis["missing_elements"].append("Signature Block")
    elif has_signatures:
        analysis["present_elements"].append("Signature Block")
        present_count += 1
        total_requirements += 1
    
    # Calculate completeness score
    if total_requirements > 0:
        analysis["completeness_score"] = present_count / total_requirements
    
    return analysis

def get_document_type_suggestions(text: str) -> List[str]:
    """Get suggestions for improving document type detection"""
    suggestions = []
    
    # Get all types with confidence scores
    types_with_confidence = detect_doc_type(text, return_confidence=True)
    
    if not types_with_confidence or types_with_confidence[0][1] < 0.5:
        suggestions.append("Document type is unclear - consider adding a clear title")
    
    # Check for multiple high-confidence types
    high_confidence_types = [t for t, c in types_with_confidence if c > 0.7]
    if len(high_confidence_types) > 1:
        suggestions.append(f"Document appears to combine multiple types: {', '.join(high_confidence_types)}")
    
    # Specific improvement suggestions
    primary_type = types_with_confidence[0][0] if types_with_confidence else "Unknown"
    
    if primary_type in DOCUMENT_PATTERNS:
        patterns = DOCUMENT_PATTERNS[primary_type]
        text_lower = text.lower()
        
        missing_primary = [k for k in patterns["primary_keywords"] if k not in text_lower]
        if missing_primary:
            suggestions.append(f"Consider adding key terms: {', '.join(missing_primary[:2])}")
    
    return suggestions