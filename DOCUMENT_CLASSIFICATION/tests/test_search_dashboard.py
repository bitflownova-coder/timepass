"""
Tests for search and dashboard endpoints
"""
import io
import pytest


class TestSearch:

    def test_search_requires_auth(self, client):
        res = client.get('/api/search?q=invoice')
        assert res.status_code in (401, 422)

    def test_search_empty_returns_results(self, client, auth_headers):
        res = client.get('/api/search?q=invoice', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True
        assert 'results' in data
        assert 'pagination' in data

    def test_search_with_category_filter(self, client, auth_headers):
        res = client.get('/api/search?category=Bills', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        for doc in data.get('results', []):
            assert doc['predicted_label'] == 'Bills'

    def test_search_suggestions(self, client, auth_headers):
        res = client.get('/api/search/suggestions?q=inv', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True
        assert isinstance(data['suggestions'], list)

    def test_search_suggestions_too_short(self, client, auth_headers):
        res = client.get('/api/search/suggestions?q=a', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['suggestions'] == []


class TestDashboard:

    def test_stats_requires_auth(self, client):
        res = client.get('/api/dashboard/stats')
        assert res.status_code in (401, 422)

    def test_stats_returns_data(self, client, auth_headers):
        res = client.get('/api/dashboard/stats', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True
        assert 'total_documents' in data
        assert 'categories' in data
        assert 'confidence' in data

    def test_recent_documents(self, client, auth_headers):
        res = client.get('/api/dashboard/recent?limit=5', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True
        assert isinstance(data['documents'], list)

    def test_activity_feed(self, client, auth_headers):
        res = client.get('/api/dashboard/activity', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True
        assert isinstance(data['activity'], list)

    def test_uploads_chart(self, client, auth_headers):
        res = client.get('/api/dashboard/chart/uploads?days=7', headers=auth_headers)
        data = res.get_json()
        assert res.status_code == 200
        assert data['success'] is True
        assert isinstance(data['data'], list)
