"""
Tests for document upload, listing, and management endpoints
"""
import io
import pytest


class TestUpload:

    def test_upload_requires_auth(self, client, sample_txt_file):
        content, name = sample_txt_file
        res = client.post('/api/upload', data={
            'file': (content, name),
        }, content_type='multipart/form-data')
        assert res.status_code in (401, 422)

    def test_upload_txt_success(self, client, auth_headers, sample_txt_file):
        content, name = sample_txt_file
        res = client.post('/api/upload', data={
            'file': (content, name),
        }, content_type='multipart/form-data', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 201
        assert data['success'] is True
        assert 'document_id' in data
        assert data['original_filename'] == name

    def test_upload_no_file(self, client, auth_headers):
        res = client.post('/api/upload', data={},
                          content_type='multipart/form-data',
                          headers=auth_headers)
        assert res.status_code == 400
        assert res.get_json()['success'] is False

    def test_upload_disallowed_extension(self, client, auth_headers):
        bad_file = (io.BytesIO(b'exec content'), 'malware.exe')
        res = client.post('/api/upload', data={'file': bad_file},
                          content_type='multipart/form-data',
                          headers=auth_headers)
        assert res.status_code == 415
        assert res.get_json()['success'] is False

    def test_duplicate_detection(self, client, auth_headers, sample_txt_file):
        content, name = sample_txt_file

        # First upload
        res1 = client.post('/api/upload', data={'file': (content, name)},
                           content_type='multipart/form-data',
                           headers=auth_headers)
        assert res1.get_json()['success'] is True

        # Second upload – same content
        content.seek(0)
        res2 = client.post('/api/upload', data={'file': (content, name)},
                           content_type='multipart/form-data',
                           headers=auth_headers)
        data2 = res2.get_json()
        assert res2.status_code == 200
        assert data2['is_duplicate'] is True

    def test_upload_with_manual_category(self, client, auth_headers):
        f = (io.BytesIO(b'Some contract text about services.'), 'contract.txt')
        res = client.post('/api/upload',
                          data={'file': f, 'category': 'Legal', 'tags': 'contract,2024'},
                          content_type='multipart/form-data',
                          headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 201
        assert data['predicted_label'] == 'Legal'


class TestDocumentListing:

    def test_list_documents(self, client, auth_headers):
        res = client.get('/api/documents', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True
        assert 'documents' in data
        assert 'pagination' in data

    def test_list_documents_paginated(self, client, auth_headers):
        res = client.get('/api/documents?page=1&per_page=5', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['pagination']['per_page'] == 5

    def test_get_document_not_found(self, client, auth_headers):
        res = client.get('/api/documents/99999', headers=auth_headers)
        assert res.status_code == 404


class TestDocumentActions:

    @pytest.fixture
    def uploaded_doc_id(self, client, auth_headers):
        f = (io.BytesIO(b'Test document content for actions.'), 'test_action.txt')
        res = client.post('/api/upload', data={'file': f},
                          content_type='multipart/form-data',
                          headers=auth_headers)
        return res.get_json().get('document_id')

    def test_get_document_detail(self, client, auth_headers, uploaded_doc_id):
        if not uploaded_doc_id:
            pytest.skip('Upload failed in fixture')
        res = client.get(f'/api/documents/{uploaded_doc_id}', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['document']['id'] == uploaded_doc_id

    def test_update_document_tags(self, client, auth_headers, uploaded_doc_id):
        if not uploaded_doc_id:
            pytest.skip('Upload failed in fixture')
        res = client.patch(f'/api/documents/{uploaded_doc_id}',
                           json={'tags': 'updated,tags'},
                           headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True

    def test_soft_delete_document(self, client, auth_headers, uploaded_doc_id):
        if not uploaded_doc_id:
            pytest.skip('Upload failed in fixture')
        res = client.delete(f'/api/documents/{uploaded_doc_id}', headers=auth_headers)
        assert res.status_code == 200
        assert res.get_json()['success'] is True

        # Verify it's gone
        res2 = client.get(f'/api/documents/{uploaded_doc_id}', headers=auth_headers)
        assert res2.status_code == 404
