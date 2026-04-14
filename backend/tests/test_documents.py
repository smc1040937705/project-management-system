import pytest
import os
import io
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models import User, Project, Document, UserRole


class TestDocuments:
    """文档管理接口测试"""

    async def test_list_documents_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_project: Project,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试获取文档列表成功"""
        doc1 = Document(
            project_id=test_project.id,
            name="test1.pdf",
            file_path="/tmp/test1.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id
        )
        doc2 = Document(
            project_id=test_project.id,
            name="test2.docx",
            file_path="/tmp/test2.docx",
            file_size=2048,
            mime_type="application/vnd.openxmlformats",
            uploaded_by=test_user.id
        )
        db_session.add_all([doc1, doc2])
        db_session.commit()

        response = await client.get("/api/v1/documents", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_list_documents_with_filters(
        self,
        client: AsyncClient,
        test_user: User,
        test_project: Project,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试带过滤参数获取文档列表"""
        doc = Document(
            project_id=test_project.id,
            name="filter_test.pdf",
            file_path="/tmp/filter_test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id
        )
        db_session.add(doc)
        db_session.commit()

        params = {
            "project_id": test_project.id,
            "search": "filter_test",
            "skip": 0,
            "limit": 10
        }
        response = await client.get("/api/v1/documents", headers=user_auth_headers, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any("filter_test" in d["name"] for d in data)

    async def test_list_documents_no_auth(self, client: AsyncClient):
        """测试未认证获取文档列表"""
        response = await client.get("/api/v1/documents")
        
        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data

    async def test_get_document_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_project: Project,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试获取文档详情成功"""
        doc = Document(
            project_id=test_project.id,
            name="detail.pdf",
            file_path="/tmp/detail.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        response = await client.get(f"/api/v1/documents/{doc.id}", headers=user_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc.id
        assert data["name"] == "detail.pdf"

    async def test_get_document_not_found(
        self,
        client: AsyncClient,
        user_auth_headers: dict
    ):
        """测试获取不存在的文档"""
        response = await client.get("/api/v1/documents/9999", headers=user_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Document not found"

    async def test_get_document_no_permission(
        self,
        client: AsyncClient,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试获取无权限的文档"""
        other_user = User(
            email="other@example.com",
            username="other",
            hashed_password="hashed",
            first_name="Other",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_project = Project(
            name="Private Project",
            description="Private",
            owner_id=other_user.id
        )
        db_session.add(other_project)
        db_session.commit()
        db_session.refresh(other_project)

        doc = Document(
            project_id=other_project.id,
            name="secret.pdf",
            file_path="/tmp/secret.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=other_user.id
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        response = await client.get(f"/api/v1/documents/{doc.id}", headers=user_auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_upload_document_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_project: Project,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试上传文档成功"""
        file_content = b"Test document content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = await client.post(
            f"/api/v1/documents/upload?project_id={test_project.id}",
            files=files,
            headers=user_auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test.pdf"
        assert data["file_size"] == len(file_content)
        assert data["project_id"] == test_project.id

    async def test_upload_document_project_not_found(
        self,
        client: AsyncClient,
        user_auth_headers: dict
    ):
        """测试上传文档到不存在的项目"""
        file_content = b"Test document content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = await client.post(
            "/api/v1/documents/upload?project_id=9999",
            files=files,
            headers=user_auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Project not found"

    async def test_upload_document_no_permission(
        self,
        client: AsyncClient,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试上传文档到无权限项目"""
        other_user = User(
            email="owner@example.com",
            username="owner",
            hashed_password="hashed",
            first_name="Owner",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        private_project = Project(
            name="Private",
            description="Private project",
            owner_id=other_user.id
        )
        db_session.add(private_project)
        db_session.commit()
        db_session.refresh(private_project)

        file_content = b"Test document content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = await client.post(
            f"/api/v1/documents/upload?project_id={private_project.id}",
            files=files,
            headers=user_auth_headers
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_upload_document_file_type_not_allowed(
        self,
        client: AsyncClient,
        test_project: Project,
        user_auth_headers: dict
    ):
        """测试上传不允许的文件类型"""
        file_content = b"Malicious executable"
        files = {"file": ("virus.exe", io.BytesIO(file_content), "application/exe")}
        
        response = await client.post(
            f"/api/v1/documents/upload?project_id={test_project.id}",
            files=files,
            headers=user_auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "File type not allowed" in data["detail"]

    async def test_upload_document_large_file(
        self,
        client: AsyncClient,
        test_project: Project,
        user_auth_headers: dict
    ):
        """测试上传过大的文件"""
        large_content = b"X" * (15 * 1024 * 1024)
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        
        response = await client.post(
            f"/api/v1/documents/upload?project_id={test_project.id}",
            files=files,
            headers=user_auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "File size exceeds maximum" in data["detail"]

    async def test_upload_document_no_auth(self, client: AsyncClient, test_project: Project):
        """测试未认证上传文档"""
        file_content = b"Test document content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = await client.post(
            f"/api/v1/documents/upload?project_id={test_project.id}",
            files=files
        )
        
        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data

    async def test_delete_document_by_uploader_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_project: Project,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试上传者删除文档成功"""
        doc = Document(
            project_id=test_project.id,
            name="to_delete.pdf",
            file_path="/tmp/to_delete.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        response = await client.delete(f"/api/v1/documents/{doc.id}", headers=user_auth_headers)
        
        assert response.status_code == 204
        
        deleted_doc = db_session.query(Document).filter(Document.id == doc.id).first()
        assert deleted_doc is None

    async def test_delete_document_by_admin_success(
        self,
        client: AsyncClient,
        db_session: Session,
        admin_auth_headers: dict
    ):
        """测试管理员删除文档成功"""
        doc = Document(
            project_id=1,
            name="admin_delete.pdf",
            file_path="/tmp/admin_delete.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=999
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        response = await client.delete(f"/api/v1/documents/{doc.id}", headers=admin_auth_headers)
        
        assert response.status_code == 204
        
        deleted_doc = db_session.query(Document).filter(Document.id == doc.id).first()
        assert deleted_doc is None

    async def test_delete_document_not_found(
        self,
        client: AsyncClient,
        user_auth_headers: dict
    ):
        """测试删除不存在的文档"""
        response = await client.delete("/api/v1/documents/9999", headers=user_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Document not found"

    async def test_delete_document_no_permission(
        self,
        client: AsyncClient,
        test_user: User,
        test_project: Project,
        db_session: Session,
        user_auth_headers: dict
    ):
        """测试删除无权限的文档"""
        other_user = User(
            email="uploader@example.com",
            username="uploader",
            hashed_password="hashed",
            first_name="Uploader",
            last_name="User",
            role=UserRole.MEMBER
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        doc = Document(
            project_id=test_project.id,
            name="others_doc.pdf",
            file_path="/tmp/others_doc.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=other_user.id
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        response = await client.delete(f"/api/v1/documents/{doc.id}", headers=user_auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Not enough permissions"

    async def test_delete_document_no_auth(
        self,
        client: AsyncClient,
        test_user: User,
        test_project: Project,
        db_session: Session
    ):
        """测试未认证删除文档"""
        doc = Document(
            project_id=test_project.id,
            name="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            uploaded_by=test_user.id
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        response = await client.delete(f"/api/v1/documents/{doc.id}")
        
        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data
