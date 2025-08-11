# src/processor/docx_processor.py
# src/processor/docx_processor.py
from docx import Document
from .type_detector import detect_doc_type
from .redflag_rules import run_redflag_checks
from .rag import get_citation_for_issue
from ..utils.reporter import build_report, save_report_json
from ..utils.docx_comment_helper import annotate_docx_with_comments
import os
import shutil
import logging
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROCESS_CHECKLISTS = {
    "Company Incorporation": [
        "Articles of Association",
        "Memorandum of Association",
        "Incorporation Application",
        "UBO Declaration",
        "Register of Members and Directors"
    ],
    "Commercial Licensing": [
        "Commercial License Application",
        "Business Plan",
        "Lease Agreement",
        "Financial Projections"
    ],
    "Employment Documentation": [
        "Employment Contract",
        "Job Description",
        "Salary Certificate"
    ]
}

class RAGRetriever:
    """RAG retriever wrapper for citation generation"""
    def __init__(self, index_path: str = "resources/adgm_index.faiss", 
                 meta_path: str = "resources/adgm_meta.json"):
        self.index_path = index_path
        self.meta_path = meta_path
        self.available = os.path.exists(index_path) and os.path.exists(meta_path)
        if not self.available:
            logger.warning(f"RAG index not found at {index_path}. Citations will be limited.")
    
    def get_citation_for_issue(self, issue: str) -> Optional[Dict]:
        """Get ADGM citation for a specific issue"""
        if not self.available:
            return None
        try:
            return get_citation_for_issue(issue, self.index_path, self.meta_path, top_k=3)
        except Exception as e:
            logger.error(f"Error getting citation for '{issue}': {str(e)}")
            return None

def infer_process_from_types(detected_types_list: List[str]) -> str:
    """Infer the legal process from detected document types"""
    types_set = set(detected_types_list)
    
    # Check each process checklist
    for process_name, required_docs in PROCESS_CHECKLISTS.items():
        required_set = set(required_docs)
        overlap = len(types_set & required_set)
        # If we have at least 40% of required docs, likely this process
        if overlap >= max(2, len(required_docs) * 0.4):
            return process_name
    
    return "Unknown"

def analyze_single_document(doc_path: str) -> Tuple[List[str], List[Dict]]:
    """Analyze a single document and return types and issues"""
    try:
        doc = Document(doc_path)
        text = "\n".join(par.text for par in doc.paragraphs if par.text.strip())
        
        if not text.strip():
            logger.warning(f"Document {doc_path} appears to be empty")
            return ["Unknown"], [{"issue": "Document appears to be empty", "severity": "High"}]
        
        # Detect document types
        doc_types = detect_doc_type(text)
        
        # Run red flag checks
        issues = run_redflag_checks(text)
        
        # Add document name to issues
        doc_name = os.path.basename(doc_path)
        for issue in issues:
            issue['document'] = doc_name
            issue['section'] = issue.get('section', 'General')
        
        return doc_types, issues
        
    except Exception as e:
        logger.error(f"Error analyzing document {doc_path}: {str(e)}")
        return ["Unknown"], [{"issue": f"Error reading document: {str(e)}", "severity": "High", "document": os.path.basename(doc_path)}]

def process_multiple_docx(paths: List[str], output_dir: str, rag_retriever: Optional[RAGRetriever] = None) -> Tuple[Dict, List[str]]:
    """Process multiple DOCX files and return consolidated report and output files"""
    os.makedirs(output_dir, exist_ok=True)
    
    all_detected_types = []
    all_issues = []
    saved_files = []
    
    logger.info(f"Processing {len(paths)} documents")
    
    # Analyze each document
    for doc_path in paths:
        logger.info(f"Analyzing: {os.path.basename(doc_path)}")
        doc_types, doc_issues = analyze_single_document(doc_path)
        all_detected_types.extend(doc_types)
        all_issues.extend(doc_issues)
    
    # Infer the legal process
    process = infer_process_from_types(all_detected_types)
    logger.info(f"Inferred process: {process}")
    
    # Check for missing documents
    missing_docs = []
    required_count = 0
    if process in PROCESS_CHECKLISTS:
        required = PROCESS_CHECKLISTS[process]
        required_count = len(required)
        present_types = set(all_detected_types)
        missing_docs = [doc for doc in required if doc not in present_types]
    
    # Enhance issues with citations if RAG is available
    if rag_retriever and rag_retriever.available:
        logger.info("Adding ADGM citations to issues...")
        for issue in all_issues:
            try:
                citation = rag_retriever.get_citation_for_issue(issue['issue'])
                if citation:
                    issue['citation'] = citation
            except Exception as e:
                logger.error(f"Error getting citation for issue '{issue['issue']}': {str(e)}")
                issue['citation'] = None
    
    # Create annotated documents
    for doc_path in paths:
        doc_name = os.path.basename(doc_path)
        output_path = os.path.join(output_dir, f"reviewed_{doc_name}")
        
        # Get issues for this specific document
        doc_issues = [issue for issue in all_issues if issue.get('document') == doc_name]
        
        try:
            annotate_docx_with_comments(doc_path, output_path, doc_issues)
            saved_files.append(output_path)
            logger.info(f"Created annotated document: {output_path}")
        except Exception as e:
            logger.error(f"Error annotating document {doc_path}: {str(e)}")
            # Still add to list but with error info
            saved_files.append(None)
    
    # Build consolidated report
    report = build_report(
        process=process,
        documents_uploaded=len(paths),
        required_documents=required_count,
        missing_document=missing_docs if missing_docs else None,
        issues_found=all_issues
    )
    
    # Save JSON report
    report_path = os.path.join(output_dir, "consolidated_report.json")
    save_report_json(report, report_path)
    
    return report, [f for f in saved_files if f is not None]

def process_docx(input_path: str, output_path: str, rag_retriever: Optional[RAGRetriever] = None) -> Dict:
    """
    Process a single DOCX file - wrapper for the multi-file processor
    Required for compatibility with the Gradio app
    """
    try:
        # Create temporary output directory
        temp_dir = os.path.dirname(output_path)
        if not temp_dir:
            temp_dir = "/tmp"
        
        # Process using multi-file processor
        report, files = process_multiple_docx([input_path], temp_dir, rag_retriever)
        
        # Move the processed file to expected location
        if files:
            shutil.move(files[0], output_path)
        else:
            # Create a placeholder if processing failed
            logger.warning(f"No output file created for {input_path}")
            shutil.copy2(input_path, output_path)
        
        return report
        
    except Exception as e:
        logger.error(f"Error processing single document {input_path}: {str(e)}")
        return {
            "process": "Error",
            "documents_uploaded": 1,
            "required_documents": 0,
            "missing_document": None,
            "issues_found": [{
                "document": os.path.basename(input_path),
                "issue": f"Processing error: {str(e)}",
                "severity": "High"
            }],
            "error": str(e)
        }

# Backwards compatibility for existing imports
def process_documents(input_paths: List[str], output_dir: str) -> Tuple[Dict, List[str]]:
    """Legacy function name for backwards compatibility"""
    rag_retriever = RAGRetriever()
    return process_multiple_docx(input_paths, output_dir, rag_retriever)