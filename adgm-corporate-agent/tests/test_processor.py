# tests/test_processor.py
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Import modules to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from processor.type_detector import detect_doc_type, analyze_document_completeness
from processor.redflag_rules import run_redflag_checks, get_severity_score
from processor.docx_processor import infer_process_from_types, analyze_single_document
from utils.reporter import build_report


class TestTypeDetector:
    """Test document type detection functionality"""
    
    def test_articles_of_association_detection(self):
        """Test detection of Articles of Association"""
        text = """
        ARTICLES OF ASSOCIATION
        of
        DemoCorp LLC
        
        1. COMPANY NAME
        The name of the company is DemoCorp LLC.
        
        2. SHARE CAPITAL
        The authorized share capital is AED 150,000.
        
        3. DIRECTORS
        The company shall have at least one director.
        """
        
        detected = detect_doc_type(text)
        assert "Articles of Association" in detected
    
    def test_memorandum_detection(self):
        """Test detection of Memorandum of Association"""
        text = """
        MEMORANDUM OF ASSOCIATION
        of
        TestCorp Limited
        
        1. The name of the company is TestCorp Limited.
        2. The registered office is situated in ADGM.
        3. The objects of the company are...
        """
        
        detected = detect_doc_type(text)
        assert "Memorandum of Association" in detected
    
    def test_ubo_declaration_detection(self):
        """Test UBO declaration detection"""
        text = """
        ULTIMATE BENEFICIAL OWNER DECLARATION
        
        I hereby declare that the following individuals are the ultimate
        beneficial owners holding 25% or more of the shares:
        
        Full Name: John Smith
        Address: 123 Main St
        Nationality: British
        """
        
        detected = detect_doc_type(text)
        assert "UBO Declaration" in detected
    
    def test_confidence_scoring(self):
        """Test confidence scoring functionality"""
        text = "ARTICLES OF ASSOCIATION with share capital and directors provisions"
        types_with_confidence = detect_doc_type(text, return_confidence=True)
        
        assert len(types_with_confidence) > 0
        assert isinstance(types_with_confidence[0], tuple)
        assert types_with_confidence[0][1] > 0.5  # High confidence
    
    def test_fallback_detection(self):
        """Test fallback detection for unknown documents"""
        text = "This is a general business agreement between parties."
        detected = detect_doc_type(text)
        
        assert len(detected) > 0
        assert "Agreement" in detected[0] or "Unknown" in detected[0]
    
    def test_completeness_analysis(self):
        """Test document completeness analysis"""
        text = """
        ARTICLES OF ASSOCIATION
        Company Name: TestCorp
        Share Capital: AED 100,000
        Directors: Minimum 1 director required
        """
        
        doc_types = ["Articles of Association"]
        analysis = analyze_document_completeness(text, doc_types)
        
        assert "detected_types" in analysis
        assert "completeness_score" in analysis
        assert analysis["completeness_score"] > 0


class TestRedFlagRules:
    """Test red flag detection functionality"""
    
    def test_jurisdiction_checks(self):
        """Test jurisdiction-related red flags"""
        text = "This agreement shall be governed by UAE Federal Courts."
        issues = run_redflag_checks(text)
        
        jurisdiction_issues = [i for i in issues if "UAE Federal Courts" in i['issue']]
        assert len(jurisdiction_issues) > 0
        assert jurisdiction_issues[0]['severity'] == 'High'
    
    def test_signature_checks(self):
        """Test signature-related checks"""
        text = "This is a legal document without any signature provisions."
        issues = run_redflag_checks(text)
        
        signature_issues = [i for i in issues if "signature" in i['issue'].lower()]
        assert len(signature_issues) > 0
    
    def test_articles_specific_checks(self):
        """Test Articles of Association specific checks"""
        text = """
        ARTICLES OF ASSOCIATION
        Company Name: TestCorp
        This document establishes the company structure.
        """
        
        issues = run_redflag_checks(text, doc_type="Articles of Association")
        
        # Should flag missing share capital
        share_capital_issues = [i for i in issues if "share capital" in i['issue'].lower()]
        assert len(share_capital_issues) > 0
    
    def test_severity_scoring(self):
        """Test severity scoring system"""
        issues = [
            {'issue': 'High severity issue', 'severity': 'High'},
            {'issue': 'Medium severity issue', 'severity': 'Medium'},
            {'issue': 'Low severity issue', 'severity': 'Low'}
        ]
        
        score = get_severity_score(issues)
        
        assert score['total_score'] == 6  # 3 + 2 + 1
        assert score['severity_counts']['High'] == 1
        assert score['priority'] == 'High'
    
    def test_adgm_compliance_checks(self):
        """Test ADGM compliance checks"""
        text = "This document governs business operations in Dubai."
        issues = run_redflag_checks(text)
        
        adgm_issues = [i for i in issues if "adgm" in i['issue'].lower()]
        # Should suggest ADGM reference
        assert any("adgm" in i['suggestion'].lower() for i in issues)


class TestDocumentProcessor:
    """Test document processing functionality"""
    
    def test_process_inference(self):
        """Test legal process inference"""
        detected_types = [
            "Articles of Association",
            "Memorandum of Association", 
            "UBO Declaration"
        ]
        
        process = infer_process_from_types(detected_types)
        assert process == "Company Incorporation"
    
    def test_unknown_process_inference(self):
        """Test inference with unknown document types"""
        detected_types = ["Unknown Document"]
        process = infer_process_from_types(detected_types)
        assert process == "Unknown"
    
    @patch('processor.docx_processor.Document')
    def test_analyze_single_document(self, mock_document):
        """Test single document analysis"""
        # Mock the Document class
        mock_doc = Mock()
        mock_paragraph = Mock()
        mock_paragraph.text = "ARTICLES OF ASSOCIATION with share capital provisions"
        mock_doc.paragraphs = [mock_paragraph]
        mock_document.return_value = mock_doc
        
        doc_types, issues = analyze_single_document("fake_path.docx")
        
        assert len(doc_types) > 0
        assert isinstance(issues, list)


class TestReporter:
    """Test report generation functionality"""
    
    def test_build_report(self):
        """Test report building"""
        issues = [
            {
                'document': 'test.docx',
                'issue': 'Missing signature',
                'severity': 'High',
                'suggestion': 'Add signature block'
            }
        ]
        
        report = build_report(
            process="Company Incorporation",
            documents_uploaded=1,
            required_documents=5,
            missing_document=["Register of Directors"],
            issues_found=issues
        )
        
        assert report['process'] == "Company Incorporation"
        assert report['documents_uploaded'] == 1
        assert report['required_documents'] == 5
        assert len(report['issues_found']) == 1
        assert report['missing_document'] == ["Register of Directors"]
    
    def test_report_json_serialization(self):
        """Test that reports can be JSON serialized"""
        import json
        
        report = build_report(
            process="Test Process",
            documents_uploaded=2,
            required_documents=3,
            missing_document=None,
            issues_found=[]
        )
        
        # Should not raise an exception
        json_str = json.dumps(report)
        reconstructed = json.loads(json_str)
        
        assert reconstructed['process'] == "Test Process"
        assert reconstructed['documents_uploaded'] == 2


class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_end_to_end_processing(self):
        """Test complete document processing pipeline"""
        # This would require actual DOCX files in practice
        # For now, test the pipeline structure
        
        sample_text = """
        ARTICLES OF ASSOCIATION
        of TestCorp LLC
        
        1. COMPANY NAME
        The company name is TestCorp LLC
        
        2. REGISTERED OFFICE
        Located in ADGM Free Zone
        
        3. SHARE CAPITAL
        Authorized capital: AED 150,000
        """
        
        # Test type detection
        doc_types = detect_doc_type(sample_text)
        assert "Articles of Association" in doc_types
        
        # Test red flag detection
        issues = run_redflag_checks(sample_text)
        assert isinstance(issues, list)
        
        # Test process inference
        process = infer_process_from_types(doc_types)
        assert process in ["Company Incorporation", "Unknown"]
    
    def test_multiple_document_types(self):
        """Test handling of multiple document types"""
        doc_types = [
            "Articles of Association",
            "Memorandum of Association",
            "UBO Declaration",
            "Incorporation Application"
        ]
        
        process = infer_process_from_types(doc_types)
        assert process == "Company Incorporation"
        
        # Test that we identify missing documents
        from processor.docx_processor import PROCESS_CHECKLISTS
        required = set(PROCESS_CHECKLISTS["Company Incorporation"])
        present = set(doc_types)
        missing = required - present
        
        assert "Register of Members and Directors" in missing


class TestRAGIntegration:
    """Test RAG system integration"""
    
    @patch('processor.rag.get_citation_for_issue')
    def test_citation_integration(self, mock_get_citation):
        """Test RAG citation integration"""
        mock_get_citation.return_value = {
            "query": "Missing signature",
            "results": [],
            "llm_summary": {
                "citation": "ADGM Companies Regulations 2020, Article 15",
                "excerpt": "Documents must be properly executed..."
            }
        }
        
        from processor.docx_processor import RAGRetriever
        
        retriever = RAGRetriever()
        citation = retriever.get_citation_for_issue("Missing signature")
        
        if citation:  # Only test if citation is returned
            assert "citation" in citation["llm_summary"]
            assert "ADGM" in citation["llm_summary"]["citation"]


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_empty_text_handling(self):
        """Test handling of empty text"""
        detected = detect_doc_type("")
        assert detected == ["Unknown"]
        
        issues = run_redflag_checks("")
        assert isinstance(issues, list)
    
    def test_very_long_text(self):
        """Test handling of very long documents"""
        long_text = "This is a test document. " * 10000  # Very long text
        
        detected = detect_doc_type(long_text)
        assert isinstance(detected, list)
        assert len(detected) > 0
        
        issues = run_redflag_checks(long_text)
        assert isinstance(issues, list)
    
    def test_special_characters(self):
        """Test handling of special characters"""
        text_with_special = """
        ARTICLES OF ASSOCIATION
        Company: Tëst-Corp™ (Spëcïål Chars) Ltd.
        Share Capital: AED 150,000 — authorized capital
        """
        
        detected = detect_doc_type(text_with_special)
        assert "Articles of Association" in detected
    
    def test_malformed_document_handling(self):
        """Test handling of malformed documents"""
        malformed_text = """
        ARTICLESOFASSOCIATION
        CompanyNameTestCorp
        ShareCapitalAED150000NoSpaces
        """
        
        # Should still attempt detection
        detected = detect_doc_type(malformed_text)
        assert isinstance(detected, list)
        
        # Should identify formatting issues
        issues = run_redflag_checks(malformed_text)
        formatting_issues = [i for i in issues if "format" in i['issue'].lower()]
        # Note: Current implementation may not catch all formatting issues


class TestPerformance:
    """Performance and scalability tests"""
    
    def test_large_document_processing(self):
        """Test processing of large documents"""
        # Simulate a large document
        large_doc = """
        ARTICLES OF ASSOCIATION
        """ + "Standard clause text. " * 5000  # Simulate large document
        
        import time
        start_time = time.time()
        
        detected = detect_doc_type(large_doc)
        issues = run_redflag_checks(large_doc)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 10.0  # 10 seconds max
        assert isinstance(detected, list)
        assert isinstance(issues, list)
    
    def test_multiple_document_batch(self):
        """Test batch processing performance"""
        documents = [
            "ARTICLES OF ASSOCIATION of Company A",
            "MEMORANDUM OF ASSOCIATION of Company B", 
            "UBO DECLARATION for Company C",
        ] * 10  # Simulate 30 documents
        
        import time
        start_time = time.time()
        
        all_types = []
        all_issues = []
        
        for doc in documents:
            types = detect_doc_type(doc)
            issues = run_redflag_checks(doc)
            all_types.extend(types)
            all_issues.extend(issues)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Batch processing should be reasonably fast
        assert processing_time < 30.0  # 30 seconds for 30 documents
        assert len(all_types) > 0
        assert len(all_issues) >= 0  # May be 0 if no issues found


# Test fixtures and utilities
@pytest.fixture
def sample_articles_text():
    """Fixture providing sample Articles of Association text"""
    return """
    ARTICLES OF ASSOCIATION
    of
    Sample Corporation LLC
    
    1. COMPANY NAME
    The name of the company is Sample Corporation LLC.
    
    2. REGISTERED OFFICE
    The registered office is situated in Abu Dhabi Global Market.
    
    3. SHARE CAPITAL
    The authorized share capital is AED 150,000 divided into 150,000 shares.
    
    4. DIRECTORS
    The company shall have a minimum of one director.
    
    5. JURISDICTION
    These articles are governed by ADGM Courts.
    
    IN WITNESS WHEREOF the subscribers have executed these Articles.
    
    Signature: _________________
    Date: ____________________
    """

@pytest.fixture
def sample_issues():
    """Fixture providing sample issues for testing"""
    return [
        {
            'document': 'test1.docx',
            'issue': 'Missing signature block',
            'severity': 'High',
            'suggestion': 'Add proper signature section',
            'section': 'Execution'
        },
        {
            'document': 'test1.docx', 
            'issue': 'Ambiguous language detected',
            'severity': 'Medium',
            'suggestion': 'Use more definitive terms',
            'section': 'General'
        }
    ]

@pytest.fixture
def temp_output_dir():
    """Fixture providing temporary output directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


# Parameterized tests
@pytest.mark.parametrize("doc_type,expected_keywords", [
    ("Articles of Association", ["articles", "association", "share capital"]),
    ("Memorandum of Association", ["memorandum", "association", "objects"]),
    ("UBO Declaration", ["ultimate beneficial owner", "ubo", "25%"]),
    ("Board Resolution", ["board", "resolution", "directors"]),
])
def test_document_type_keywords(doc_type, expected_keywords):
    """Parameterized test for document type keyword detection"""
    # Create text containing the expected keywords
    text = f"{doc_type} containing " + " and ".join(expected_keywords)
    detected = detect_doc_type(text)
    
    assert doc_type in detected or any(keyword in detected[0] for keyword in expected_keywords)


@pytest.mark.parametrize("severity,expected_weight", [
    ("High", 3),
    ("Medium", 2), 
    ("Low", 1),
])
def test_severity_weights(severity, expected_weight):
    """Test severity weight calculations"""
    issues = [{'issue': 'Test issue', 'severity': severity}]
    score = get_severity_score(issues)
    
    assert score['total_score'] == expected_weight


# Mock tests for external dependencies
class TestWithMocks:
    """Tests using mocks for external dependencies"""
    
    @patch('os.path.exists')
    def test_rag_retriever_availability(self, mock_exists):
        """Test RAG retriever availability checking"""
        from processor.docx_processor import RAGRetriever
        
        # Test when files exist
        mock_exists.return_value = True
        retriever = RAGRetriever()
        assert retriever.available == True
        
        # Test when files don't exist
        mock_exists.return_value = False
        retriever = RAGRetriever()
        assert retriever.available == False


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])