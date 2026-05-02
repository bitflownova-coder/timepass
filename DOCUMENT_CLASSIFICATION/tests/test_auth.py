"""
Tests for authentication endpoints
"""
import pytest


class TestRegister:

    def test_register_success(self, client, user_payload):
        res = client.post('/api/auth/register', json=user_payload)
        data = res.get_json()
        assert res.status_code == 201
        assert data['success'] is True
        assert 'token' in data

    def test_register_duplicate_email(self, client, user_payload, registered_user):
        res = client.post('/api/auth/register', json=user_payload)
        data = res.get_json()
        assert res.status_code in (400, 409)
        assert data['success'] is False

    def test_register_invalid_email(self, client):
        res = client.post('/api/auth/register', json={
            'email': 'not-an-email', 'password': 'Test@1234!'
        })
        assert res.status_code == 400
        assert res.get_json()['success'] is False

    def test_register_weak_password(self, client):
        res = client.post('/api/auth/register', json={
            'email': 'user2@example.com', 'password': 'weakpassword'
        })
        assert res.status_code == 400
        assert res.get_json()['success'] is False

    def test_register_missing_fields(self, client):
        res = client.post('/api/auth/register', json={})
        assert res.status_code == 400


class TestLogin:

    def test_login_success(self, client, user_payload, registered_user):
        res = client.post('/api/auth/login', json={
            'email': user_payload['email'],
            'password': user_payload['password'],
        })
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True
        assert 'token' in data

    def test_login_wrong_password(self, client, user_payload, registered_user):
        res = client.post('/api/auth/login', json={
            'email': user_payload['email'],
            'password': 'WrongPassword1!',
        })
        assert res.status_code in (400, 401)
        assert res.get_json()['success'] is False

    def test_login_unknown_email(self, client):
        res = client.post('/api/auth/login', json={
            'email': 'nobody@example.com', 'password': 'Test@1234!'
        })
        assert res.status_code in (400, 401)
        assert res.get_json()['success'] is False


class TestProfile:

    def test_get_profile_authenticated(self, client, auth_headers, user_payload):
        res = client.get('/api/auth/profile', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True
        assert data['user']['email'] == user_payload['email']

    def test_get_profile_unauthenticated(self, client):
        res = client.get('/api/auth/profile')
        assert res.status_code in (401, 422)

    def test_update_profile(self, client, auth_headers):
        res = client.patch('/api/auth/profile',
                           json={'full_name': 'Updated Name'},
                           headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True
