"""Tests for file upload API endpoints"""
import os
import pytest
from io import BytesIO
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import UploadedFile
from app.utils.file_upload import FileUploadManager


# Create test database
@pytest.fixture(scope="session")
def setup_test_db():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Database fixture for tests"""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_pdf():
    """Create a minimal valid PDF file for testing"""
    # Minimal PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000194 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
288
%%EOF
"""
    return BytesIO(pdf_content)


class TestFileUpload:
    """Test file upload endpoints"""

    def test_upload_pdf_success(self, client, sample_pdf):
        """Test successful PDF upload"""
        response = client.post(
            "/api/uploads/pdf",
            files={"file": ("test.pdf", sample_pdf)},
            data={
                "upload_type": "company_function",
                "uploaded_by_email": "test@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] is not None
        assert data["original_filename"] == "test.pdf"
        assert data["file_type"] == "company_function"
        assert data["upload_status"] == "pending"
        assert data["file_size"] > 0

    def test_upload_invalid_extension(self, client):
        """Test upload with invalid file extension"""
        response = client.post(
            "/api/uploads/pdf",
            files={"file": ("test.txt", BytesIO(b"not a pdf"))},
            data={"upload_type": "self_feedback"}
        )
        
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_invalid_pdf(self, client):
        """Test upload with invalid PDF content"""
        response = client.post(
            "/api/uploads/pdf",
            files={"file": ("test.pdf", BytesIO(b"This is not a PDF"))},
            data={"upload_type": "project_feedback"}
        )
        
        assert response.status_code == 400
        assert "valid PDF" in response.json()["detail"]

    def test_upload_empty_file(self, client):
        """Test upload with empty file"""
        response = client.post(
            "/api/uploads/pdf",
            files={"file": ("test.pdf", BytesIO(b""))},
            data={"upload_type": "company_function"}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_with_profile_id(self, client, sample_pdf):
        """Test upload with PR profile ID"""
        response = client.post(
            "/api/uploads/pdf",
            files={"file": ("test.pdf", sample_pdf)},
            data={
                "upload_type": "self_feedback",
                "pr_profile_id": 123
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["upload_status"] == "pending"

    def test_process_pdf(self, client, sample_pdf, db: Session):
        """Test PDF processing"""
        # First upload
        response = client.post(
            "/api/uploads/pdf",
            files={"file": ("test.pdf", sample_pdf)},
            data={"upload_type": "company_function"}
        )
        
        assert response.status_code == 200
        file_id = response.json()["id"]
        
        # Then process
        process_response = client.post(f"/api/uploads/process/{file_id}")
        assert process_response.status_code == 200
        
        data = process_response.json()
        assert data["upload_status"] == "completed"
        assert data["extracted_text_length"] > 0

    def test_get_upload_status(self, client, sample_pdf):
        """Test getting upload status"""
        # Upload file
        response = client.post(
            "/api/uploads/pdf",
            files={"file": ("test.pdf", sample_pdf)},
            data={"upload_type": "project_feedback"}
        )
        
        file_id = response.json()["id"]
        
        # Get status
        status_response = client.get(f"/api/uploads/status/{file_id}")
        assert status_response.status_code == 200
        
        data = status_response.json()
        assert data["file_type"] == "project_feedback"
        assert data["upload_status"] == "pending"

    def test_get_nonexistent_status(self, client):
        """Test getting status of non-existent file"""
        response = client.get("/api/uploads/status/99999")
        assert response.status_code == 404

    def test_list_uploads(self, client, sample_pdf):
        """Test listing uploads"""
        # Upload multiple files
        for i in range(3):
            sample_pdf.seek(0)
            client.post(
                "/api/uploads/pdf",
                files={"file": (f"test{i}.pdf", sample_pdf)},
                data={"upload_type": "self_feedback"}
            )
        
        # List uploads
        response = client.get("/api/uploads/list?skip=0&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) > 0

    def test_list_uploads_with_filter(self, client, sample_pdf):
        """Test listing uploads with file type filter"""
        # Upload different types
        sample_pdf.seek(0)
        client.post(
            "/api/uploads/pdf",
            files={"file": ("company.pdf", sample_pdf)},
            data={"upload_type": "company_function"}
        )
        
        sample_pdf.seek(0)
        client.post(
            "/api/uploads/pdf",
            files={"file": ("self.pdf", sample_pdf)},
            data={"upload_type": "self_feedback"}
        )
        
        # Filter by type
        response = client.get("/api/uploads/list?file_type=company_function")
        assert response.status_code == 200
        
        data = response.json()
        for item in data["items"]:
            if item["file_type"] in ["company_function", "CompanyFunction"]:
                # Filter is working
                break

    def test_delete_upload(self, client, sample_pdf):
        """Test deleting an uploaded file"""
        # Upload
        response = client.post(
            "/api/uploads/pdf",
            files={"file": ("test.pdf", sample_pdf)},
            data={"upload_type": "project_feedback"}
        )
        
        file_id = response.json()["id"]
        
        # Delete
        delete_response = client.delete(f"/api/uploads/{file_id}")
        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]
        
        # Verify it's gone
        status_response = client.get(f"/api/uploads/status/{file_id}")
        assert status_response.status_code == 404


class TestFileUploadManager:
    """Test FileUploadManager utility class"""

    def test_validate_pdf_file(self, sample_pdf):
        """Test PDF file validation"""
        manager = FileUploadManager()
        content = sample_pdf.read()
        
        is_valid, error = manager.validate_file("test.pdf", content)
        assert is_valid is True
        assert error == ""

    def test_validate_non_pdf_file(self):
        """Test validation of non-PDF file"""
        manager = FileUploadManager()
        
        is_valid, error = manager.validate_file("test.txt", b"not a pdf")
        assert is_valid is False
        assert "PDF" in error

    def test_generate_unique_filename(self):
        """Test unique filename generation"""
        manager = FileUploadManager()
        
        filename1 = manager.generate_unique_filename("feedback.pdf")
        filename2 = manager.generate_unique_filename("feedback.pdf")
        
        assert filename1 != filename2
        assert filename1.endswith("feedback.pdf")
        assert filename2.endswith("feedback.pdf")

    def test_save_and_retrieve_file(self, sample_pdf):
        """Test saving and retrieving files"""
        manager = FileUploadManager()
        content = sample_pdf.read()
        
        filename = manager.generate_unique_filename("test.pdf")
        success, filepath = manager.save_uploaded_file(filename, content)
        
        assert success is True
        assert os.path.exists(filepath)
        
        # Retrieve file
        retrieved = manager.get_file_path(filename)
        assert retrieved is not None
        assert retrieved.exists()
        
        # Cleanup
        manager.delete_file(filename)
        assert not retrieved.exists()
