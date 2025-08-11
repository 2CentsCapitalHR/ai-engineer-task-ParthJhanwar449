# src/app.py
import gradio as gr
from processor.docx_processor import process_docx, process_multiple_docx, RAGRetriever
import uuid
import os
import json
import tempfile
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize RAG retriever
rag_retriever = RAGRetriever()

def format_report_for_display(report_dict):
    """Format the JSON report for better display in the UI"""
    try:
        # Create a nicely formatted summary
        process = report_dict.get('process', 'Unknown')
        uploaded = report_dict.get('documents_uploaded', 0)
        required = report_dict.get('required_documents', 0)
        missing = report_dict.get('missing_document', [])
        issues = report_dict.get('issues_found', [])
        
        summary = f"""
## 📋 Analysis Summary

**Process Detected:** {process}
**Documents Uploaded:** {uploaded}
**Required Documents:** {required}

"""
        
        if missing:
            if isinstance(missing, list) and missing:
                summary += f"**⚠️ Missing Documents:** {', '.join(missing)}\n\n"
            elif isinstance(missing, str):
                summary += f"**⚠️ Missing Documents:** {missing}\n\n"
        else:
            summary += "**✅ All required documents appear to be present**\n\n"
        
        if issues:
            summary += f"**🚨 Issues Found:** {len(issues)}\n\n"
            summary += "### Detailed Issues:\n\n"
            for i, issue in enumerate(issues, 1):
                severity = issue.get('severity', 'Medium')
                emoji = "🔴" if severity == "High" else "🟡" if severity == "Medium" else "🟢"
                doc_name = issue.get('document', 'Unknown')
                issue_desc = issue.get('issue', 'No description')
                suggestion = issue.get('suggestion', 'No suggestion provided')
                
                summary += f"{emoji} **Issue {i}** ({severity})\n"
                summary += f"   - **Document:** {doc_name}\n"
                summary += f"   - **Problem:** {issue_desc}\n"
                summary += f"   - **Suggestion:** {suggestion}\n\n"
        else:
            summary += "**✅ No issues detected**\n"
        
        return summary
        
    except Exception as e:
        logger.error(f"Error formatting report: {str(e)}")
        return f"Error formatting report: {str(e)}\n\nRaw JSON:\n{json.dumps(report_dict, indent=2)}"

def review_single_document(file):
    """Review a single document"""
    if not file:
        return "Please upload a document first.", None, None
    
    if not file.name.endswith(".docx"):
        return "❌ Only .docx files are supported.", None, None
    
    try:
        # Create temp directory for output
        temp_dir = tempfile.mkdtemp()
        original_name = Path(file.name).stem
        output_name = f"reviewed_{original_name}.docx"
        output_path = os.path.join(temp_dir, output_name)
        
        logger.info(f"Processing single document: {file.name}")
        
        # Process the document
        report = process_docx(file.name, output_path, rag_retriever)
        
        # Format report for display
        formatted_report = format_report_for_display(report)
        
        # Create JSON report file
        json_report_path = os.path.join(temp_dir, f"report_{original_name}.json")
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return formatted_report, output_path, json_report_path
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return f"❌ Error processing document: {str(e)}", None, None

def review_multiple_documents(files):
    """Review multiple documents"""
    if not files:
        return "Please upload at least one document.", None, None
    
    try:
        # Validate all files
        valid_files = []
        for file in files:
            if file.name.endswith(".docx"):
                valid_files.append(file.name)
            else:
                logger.warning(f"Skipping non-DOCX file: {file.name}")
        
        if not valid_files:
            return "❌ No valid .docx files found in upload.", None, None
        
        # Create temp directory for output
        temp_dir = tempfile.mkdtemp()
        
        logger.info(f"Processing {len(valid_files)} documents")
        
        # Process all documents
        report, output_files = process_multiple_docx(valid_files, temp_dir, rag_retriever)
        
        # Format report for display
        formatted_report = format_report_for_display(report)
        
        # Create JSON report
        json_report_path = os.path.join(temp_dir, "consolidated_report.json")
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Create a ZIP file with all outputs if multiple files
        if len(output_files) > 1:
            zip_path = os.path.join(temp_dir, "reviewed_documents.zip")
            import zipfile
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_path in output_files:
                    if os.path.exists(file_path):
                        zipf.write(file_path, os.path.basename(file_path))
                zipf.write(json_report_path, "consolidated_report.json")
            return formatted_report, zip_path, json_report_path
        elif output_files:
            return formatted_report, output_files[0], json_report_path
        else:
            return formatted_report, None, json_report_path
            
    except Exception as e:
        logger.error(f"Error processing multiple documents: {str(e)}")
        return f"❌ Error processing documents: {str(e)}", None, None

def check_rag_status():
    """Check if RAG system is properly configured"""
    if rag_retriever.available:
        return "✅ ADGM RAG system is active - Legal citations will be included"
    else:
        return "⚠️ ADGM RAG system not available - Install ADGM documents and run build_adgm_index.py"

# Custom CSS for better styling
css = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.warning-box {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
}
.success-box {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
}
"""

# Create the Gradio interface
with gr.Blocks(css=css, title="ADGM Corporate Agent", theme=gr.themes.Soft()) as demo:
    gr.HTML("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2d3748; margin-bottom: 10px;">🏢 ADGM Corporate Agent</h1>
        <p style="color: #4a5568; font-size: 1.1em;">AI-Powered Legal Document Review for Abu Dhabi Global Market</p>
    </div>
    """)
    
    # System status
    with gr.Row():
        rag_status = gr.HTML(f'<div class="{"success-box" if rag_retriever.available else "warning-box"}">{check_rag_status()}</div>')
    
    with gr.Tabs() as tabs:
        # Single Document Tab
        with gr.TabItem("📄 Single Document Review"):
            gr.Markdown("""
            Upload a single DOCX document for ADGM compliance review. 
            The system will detect document type, check for red flags, and provide legal citations.
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    single_file_input = gr.File(
                        label="Upload DOCX Document", 
                        file_types=['.docx'],
                        file_count="single"
                    )
                    single_review_btn = gr.Button("🔍 Review Document", variant="primary", size="lg")
                
                with gr.Column(scale=2):
                    single_report_output = gr.Markdown(label="Analysis Report")
            
            with gr.Row():
                single_docx_output = gr.File(label="📝 Reviewed Document (with comments)")
                single_json_output = gr.File(label="📊 JSON Report")
        
        # Multiple Documents Tab
        with gr.TabItem("📚 Multiple Documents Review"):
            gr.Markdown("""
            Upload multiple DOCX documents for comprehensive ADGM compliance review. 
            The system will identify the legal process and check for missing required documents.
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    multi_files_input = gr.File(
                        label="Upload Multiple DOCX Documents", 
                        file_types=['.docx'],
                        file_count="multiple"
                    )
                    multi_review_btn = gr.Button("🔍 Review All Documents", variant="primary", size="lg")
                
                with gr.Column(scale=2):
                    multi_report_output = gr.Markdown(label="Consolidated Analysis Report")
            
            with gr.Row():
                multi_output_file = gr.File(label="📦 Reviewed Documents")
                multi_json_output = gr.File(label="📊 Consolidated JSON Report")
    
    # Help section
    with gr.Accordion("ℹ️ Help & Information", open=False):
        gr.Markdown("""
        ### Supported Document Types:
        - Articles of Association (AoA)
        - Memorandum of Association (MoA)  
        - Board/Shareholder Resolutions
        - Incorporation Applications
        - UBO Declaration Forms
        - Register of Members and Directors
        - Commercial License Applications
        - Employment Contracts
        
        ### What the System Checks:
        - **Document Completeness**: Verifies all required documents for the detected legal process
        - **Legal Red Flags**: Identifies jurisdiction errors, missing clauses, formatting issues
        - **ADGM Compliance**: Cross-references with official ADGM regulations and provides citations
        - **Clause Suggestions**: Recommends improvements for common legal issues
        
        ### Output Format:
        - **Reviewed DOCX**: Original document with inline comments highlighting issues
        - **JSON Report**: Structured analysis with all findings, suggestions, and citations
        
        **Disclaimer**: This tool is for assistance only and does not constitute legal advice.
        """)
    
    # Event handlers
    single_review_btn.click(
        fn=review_single_document,
        inputs=[single_file_input],
        outputs=[single_report_output, single_docx_output, single_json_output]
    )
    
    multi_review_btn.click(
        fn=review_multiple_documents,
        inputs=[multi_files_input],
        outputs=[multi_report_output, multi_output_file, multi_json_output]
    )

# Launch configuration
if __name__ == '__main__':
    # Print startup info
    print("\n" + "="*50)
    print("🏢 ADGM Corporate Agent Starting...")
    print(f"📊 RAG System: {'✅ Active' if rag_retriever.available else '⚠️  Not Available'}")
    print("🌐 Open your browser to interact with the system")
    print("="*50 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )