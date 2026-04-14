import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User, UserRole, Project, ProjectStatus, Document


class TestListDocuments:
    def test_list_documents_as_admin(self, client: TestClient, admin_auth_headers: dict, db: Session, test_project: Project, test_user: User):
        doc = Document(
            project_id=test_project.id,
            name="Test Document.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.get("/api/v1/documents", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_documents_with_project_filter(self, client: TestClient, admin_auth_headers: dict, db: Session, test_project: Project, test_user: User):
        doc = Document(
            project_id=test_project.id,
            name="Project Document.pdf",
            file_path="/uploads/project.pdf",
            file_size=2048,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.get(
            "/api/v1/documents",
            params={"project_id": test_project.id},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for doc in data:
            assert doc["project_id"] == test_project.id

    def test_list_documents_with_search(self, client: TestClient, admin_auth_headers: dict, db: Session, test_project: Project, test_user: User):
        doc = Document(
            project_id=test_project.id,
            name="Searchable Document.pdf",
            file_path="/uploads/searchable.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.get(
            "/api/v1/documents",
            params={"search": "Searchable"},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for doc in data:
            assert "Searchable" in doc["name"]

    def test_list_documents_pagination(self, client: TestClient, admin_auth_headers: dict, db: Session, test_project: Project, test_user: User):
        for i in range(5):
            doc = Document(
                project_id=test_project.id,
                name=f"Document {i}.pdf",
                file_path=f"/uploads/doc{i}.pdf",
                file_size=1024,
                mime_type="application/pdf",
                uploaded_by=test_user.id,
                version=1,
            )
            db.add(doc)
        db.commit()

        response = client.get(
            "/api/v1/documents",
            params={"skip": 0, "limit": 2},
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_documents_unauthorized(self, client: TestClient):
        response = client.get("/api/v1/documents")
        assert response.status_code == 403


class TestGetDocument:
    def test_get_document_success(self, client: TestClient, auth_headers: dict, db: Session, test_project: Project, test_user: User):
        doc = Document(
            project_id=test_project.id,
            name="Test Doc.pdf",
            file_path="/uploads/testdoc.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.get(f"/api/v1/documents/{doc.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc.id
        assert data["name"] == "Test Doc.pdf"

    def test_get_document_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.get("/api/v1/documents/9999", headers=admin_auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_document_unauthorized(self, client: TestClient, db: Session, test_project: Project, test_user: User):
        doc = Document(
            project_id=test_project.id,
            name="Unauthorized Doc.pdf",
            file_path="/uploads/unauth.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.get(f"/api/v1/documents/{doc.id}")
        assert response.status_code == 403

    def test_get_document_non_member_denied(self, client: TestClient, db: Session, test_project: Project, test_user: User):
        doc = Document(
            project_id=test_project.id,
            name="Member Doc.pdf",
            file_path="/uploads/member.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        
        from app.auth import create_access_token
        token = create_access_token(subject=other_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/v1/documents/{doc.id}", headers=headers)
        assert response.status_code == 403


class TestUploadDocument:
    def test_upload_document_success(self, client: TestClient, auth_headers: dict, test_project: Project):
        file_content = b"Test file content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = client.post(
            f"/api/v1/documents/upload?project_id={test_project.id}",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test.pdf"
        assert data["mime_type"] == "application/pdf"
        assert data["file_size"] == len(file_content)

    def test_upload_document_txt(self, client: TestClient, auth_headers: dict, test_project: Project):
        file_content = b"Text file content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post(
            f"/api/v1/documents/upload?project_id={test_project.id}",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test.txt"

    def test_upload_document_project_not_found(self, client: TestClient, auth_headers: dict):
        file_content = b"Test file content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = client.post(
            "/api/v1/documents/upload?project_id=9999",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_upload_document_invalid_type(self, client: TestClient, auth_headers: dict, test_project: Project):
        file_content = b"Test file content"
        files = {"file": ("test.exe", io.BytesIO(file_content), "application/octet-stream")}
        
        response = client.post(
            f"/api/v1/documents/upload?project_id={test_project.id}",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()

    def test_upload_document_non_member_denied(self, client: TestClient, db: Session, test_project: Project):
        other_user = User(
            email="nonmember@example.com",
            username="nonmember",
            hashed_password="hashed",
            first_name="Non",
            last_name="Member",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        
        from app.auth import create_access_token
        token = create_access_token(subject=other_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        file_content = b"Test file content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = client.post(
            f"/api/v1/documents/upload?project_id={test_project.id}",
            files=files,
            headers=headers
        )
        assert response.status_code == 403

    def test_upload_document_unauthorized(self, client: TestClient, test_project: Project):
        file_content = b"Test file content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = client.post(
            f"/api/v1/documents/upload?project_id={test_project.id}",
            files=files
        )
        assert response.status_code == 403


class TestDeleteDocument:
    def test_delete_document_as_uploader(self, client: TestClient, auth_headers: dict, db: Session, test_project: Project, test_user: User):
        doc = Document(
            project_id=test_project.id,
            name="To Delete.pdf",
            file_path="/uploads/todelete.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.delete(f"/api/v1/documents/{doc.id}", headers=auth_headers)
        assert response.status_code == 204

        response = client.get(f"/api/v1/documents/{doc.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_document_as_admin(self, client: TestClient, admin_auth_headers: dict, db: Session, test_project: Project, test_user: User):
        doc = Document(
            project_id=test_project.id,
            name="Admin Delete.pdf",
            file_path="/uploads/admindelete.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.delete(f"/api/v1/documents/{doc.id}", headers=admin_auth_headers)
        assert response.status_code == 204

    def test_delete_document_not_found(self, client: TestClient, admin_auth_headers: dict):
        response = client.delete("/api/v1/documents/9999", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_document_other_user_denied(self, client: TestClient, db: Session, test_project: Project, test_user: User):
        doc = Document(
            project_id=test_project.id,
            name="Other User Doc.pdf",
            file_path="/uploads/otheruser.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        other_user = User(
            email="other2@example.com",
            username="otheruser2",
            hashed_password="hashed",
            first_name="Other",
            last_name="User2",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        
        from app.auth import create_access_token
        token = create_access_token(subject=other_user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.delete(f"/api/v1/documents/{doc.id}", headers=headers)
        assert response.status_code == 403

    def test_delete_document_unauthorized(self, client: TestClient, db: Session, test_project: Project, test_user: User):
        doc = Document(
            project_id=test_project.id,
            name="Unauthorized Delete.pdf",
            file_path="/uploads/unauthdelete.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id,
            version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.delete(f"/api/v1/documents/{doc.id}")
        assert response.status_code == 403
