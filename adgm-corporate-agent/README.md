# 🏢 ADGM Corporate Agent - AI-Powered Legal Document Review

An intelligent AI-powered legal assistant for reviewing, validating, and preparing documentation for business incorporation and compliance within the Abu Dhabi Global Market (ADGM) jurisdiction.

![ADGM Agent Demo](https://img.shields.io/badge/Status-Production%20Ready-brightgreen) ![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## 🌟 Features

### ✨ Core Capabilities
- **Document Type Detection**: Automatically identifies 12+ legal document types
- **ADGM Compliance Checking**: Validates documents against ADGM regulations
- **RAG-Powered Citations**: Provides legal citations from official ADGM documents
- **Red Flag Detection**: Identifies legal issues and inconsistencies
- **Inline Comments**: Inserts XML comments directly into DOCX files
- **Process Recognition**: Detects legal processes (incorporation, licensing, etc.)
- **Completeness Validation**: Checks for missing required documents

### 📋 Supported Document Types
- Articles of Association (AoA)
- Memorandum of Association (MoA)
- UBO Declaration Forms
- Incorporation Applications
- Board/Shareholder Resolutions
- Employment Contracts
- Commercial License Applications
- Register of Members and Directors
- Power of Attorney
- Lease Agreements
- Non-Disclosure Agreements
- General Business Documents

### 🎯 What It Checks
- **Jurisdiction Issues**: UAE Federal Courts vs ADGM Courts
- **Missing Clauses**: Share capital, signature blocks, etc.
- **Legal Language**: Ambiguous terms, proper obligations
- **Document Structure**: Required sections and formatting
- **ADGM Compliance**: Cross-references with official regulations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Official ADGM PDF documents

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd adgm-corporate-agent

# Run automatic setup
python setup.py --install

# Check setup status
python setup.py --check
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API key
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Add ADGM Documents

Download official ADGM documents and place them in `resources/adgm/`:

**Required Documents:**
- ADGM_Companies_Regulations_2020.pdf
- ADGM_Rulebook_2023.pdf
- ADGM_Employment_Regulations_2020.pdf
- ADGM_Commercial_Licensing_Regulations_2020.pdf

**Download Sources:**
- [ADGM Regulations](https://www.adgm.com/doing-business/regulations/)
- [ADGM Legal Framework](https://www.adgm.com/legal-framework/)

### 4. Build RAG Index

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Build ADGM knowledge index
python scripts/build_adgm_index.py
```

### 5. Launch Application

```bash
python src/app.py
```

Open your browser to `http://localhost:7860`

## 📖 Usage Guide

### Single Document Review
1. Upload a DOCX file
2. Click "Review Document"
3. Download reviewed document with comments
4. Review JSON report for detailed findings

### Multiple Documents Review
1. Upload multiple DOCX files
2. Click "Review All Documents"
3. System detects legal process automatically
4. Identifies missing required documents
5. Download consolidated results

### Example Output

```json
{
  "process": "Company Incorporation",
  "documents_uploaded": 4,
  "required_documents": 5,
  "missing_document": ["Register of Members and Directors"],
  "issues_found": [
    {
      "document": "Articles of Association.docx",
      "section": "Clause 3.1",
      "issue": "Jurisdiction clause does not specify ADGM",
      "severity": "High",
      "suggestion": "Update jurisdiction to ADGM Courts",
      "citation": {
        "citation": "ADGM Companies Regulations 2020, Article 15",
        "excerpt": "All companies must specify ADGM jurisdiction..."
      }
    }
  ]
}
```

## 🏗️ Architecture

### System Components
```
📥 Input Layer          ⚙️ Core Processing       📤 Output Layer
├── Gradio UI          ├── Document Parser      ├── Report Generator
├── File Validator     ├── Type Detector        ├── DOCX Annotator
└── Multi-file Upload  ├── Process Inference    └── File Manager
                       ├── Red Flag Engine      
                       ├── RAG System           
                       └── Comment Injector     
```

### Technology Stack
- **Backend**: Python 3.8+
- **UI Framework**: Gradio
- **Document Processing**: python-docx
- **AI/ML**: OpenAI API (GPT-4, Embeddings)
- **Vector Database**: FAISS
- **PDF Processing**: PDFPlumber

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_processor.py::TestTypeDetector -v
pytest tests/test_processor.py::TestRedFlagRules -v

# Run with coverage
pytest --cov=src tests/
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end pipeline testing
- **Performance Tests**: Large document handling
- **Error Handling**: Edge cases and malformed inputs

## 📁 Project Structure

```
adgm-corporate-agent/
├── src/
│   ├── app.py                 # Main Gradio application
│   ├── processor/
│   │   ├── docx_processor.py  # Document processing pipeline
│   │   ├── type_detector.py   # Document type detection
│   │   ├── redflag_rules.py   # Legal issue detection
│   │   └── rag.py            # ADGM knowledge retrieval
│   └── utils/
│       ├── docx_comment_helper.py  # XML comment insertion
│       └── reporter.py            # Report generation
├── scripts/
│   └── build_adgm_index.py   # RAG index builder
├── tests/
│   └── test_processor.py     # Comprehensive tests
├── resources/
│   ├── adgm/                 # ADGM PDF documents
│   ├── adgm_index.faiss     # Vector index
│   └── adgm_meta.json       # Document metadata
├── examples/
│   └── sample_before.docx    # Sample documents
├── requirements.txt          # Dependencies
├── setup.py                  # Environment setup
└── README.md                 # This file
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-your-api-key-here

# Optional
OPENAI_EMBED_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
APP_HOST=0.0.0.0
APP_PORT=7860
```

### Document Processing Settings
```python
# Modify in docx_processor.py
PROCESS_CHECKLISTS = {
    "Company Incorporation": [
        "Articles of Association",
        "Memorandum of Association", 
        "UBO Declaration",
        # Add more as needed
    ]
}
```

## 🔧 Development

### Adding New Document Types

1. **Update type_detector.py:**
```python
DOCUMENT_PATTERNS["New Document Type"] = {
    "primary_keywords": ["keyword1", "keyword2"],
    "secondary_keywords": ["related1", "related2"],
    "confidence_threshold": 0.6
}
```

2. **Add Red Flag Rules:**
```python
def _check_new_document_type(text: str, text_lower: str):
    issues = []
    # Add specific checks
    return issues
```

3. **Update Process Checklists:**
```python
PROCESS_CHECKLISTS["New Process"] = [
    "Required Document 1",
    "Required Document 2"
]
```

### Extending Red Flag Rules

Add new rules in `redflag_rules.py`:
```python
def _check_custom_compliance(text: str, text_lower: str):
    issues = []
    if "problematic_pattern" in text_lower:
        issues.append({
            'issue': 'Description of issue',
            'severity': 'High|Medium|Low',
            'suggestion': 'How to fix it'
        })
    return issues
```

## 🚦 API Reference

### Core Functions

#### `process_docx(input_path, output_path, rag_retriever=None)`
Process a single DOCX document.

**Parameters:**
- `input_path` (str): Path to input document
- `output_path` (str): Path for output document
- `rag_retriever` (RAGRetriever): Optional RAG system

**Returns:** Dict with analysis results

#### `detect_doc_type(text, return_confidence=False)`
Detect document type from text.

**Parameters:**
- `text` (str): Document text
- `return_confidence` (bool): Include confidence scores

**Returns:** List of document types

#### `run_redflag_checks(text, doc_type=None)`
Run legal compliance checks.

**Parameters:**
- `text` (str): Document text
- `doc_type` (str): Optional document type

**Returns:** List of issues found

## 📊 Performance

### Benchmarks
- **Single Document**: ~2-5 seconds
- **Multiple Documents (5)**: ~10-15 seconds
- **Large Document (10K words)**: ~8-12 seconds
- **RAG Citation Lookup**: ~1-3 seconds

### Optimization Tips
- Use RAG system for better citations
- Process documents in batches
- Cache frequent document patterns
- Optimize red flag rule patterns

## 🛠️ Troubleshooting

### Common Issues

**1. RAG System Not Available**
```
⚠️ ADGM RAG system not available
```
**Solution:** Add ADGM PDFs to `resources/adgm/` and run `build_adgm_index.py`

**2. OpenAI API Errors**
```
Error: OpenAI API key not set
```
**Solution:** Set `OPENAI_API_KEY` environment variable

**3. Document Processing Fails**
```
Error processing document: [Errno 2] No such file or directory
```
**Solution:** Ensure document exists and is valid DOCX format

**4. Empty Citations**
```
Citation: None
```
**Solution:** Build RAG index with official ADGM documents

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run tests before committing
pytest tests/ -v
```
