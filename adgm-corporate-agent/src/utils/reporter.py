# src/utils/reporter.py
import json
def build_report(process, documents_uploaded, required_documents, missing_document, issues_found):
    return {
        "process": process,
        "documents_uploaded": documents_uploaded,
        "required_documents": required_documents,
        "missing_document": missing_document,
        "issues_found": issues_found
    }
def save_report_json(report, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)