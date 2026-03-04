"""
Tests for cloudinary_service app – serializer validation and API views.
All Cloudinary calls are mocked.
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.cloudinary_service.serializers import (
    FileUploadSerializer,
    MultiFileUploadSerializer,
    FileDeleteSerializer,
)


# ---------------------------------------------------------------------------
# Serializer tests
# ---------------------------------------------------------------------------
class FileUploadSerializerTest(TestCase):

    def test_valid_file(self):
        f = SimpleUploadedFile('test.txt', b'hello', content_type='text/plain')
        s = FileUploadSerializer(data={'file': f})
        self.assertTrue(s.is_valid())

    def test_file_too_large(self):
        # 11 MB
        f = SimpleUploadedFile('big.bin', b'x' * (11 * 1024 * 1024), content_type='application/octet-stream')
        s = FileUploadSerializer(data={'file': f})
        self.assertFalse(s.is_valid())
        self.assertIn('file', s.errors)

    def test_default_folder(self):
        f = SimpleUploadedFile('test.txt', b'hello')
        s = FileUploadSerializer(data={'file': f})
        s.is_valid()
        self.assertEqual(s.validated_data['folder'], 'uploads')


class MultiFileUploadSerializerTest(TestCase):

    def test_too_many_files(self):
        files = [SimpleUploadedFile(f'f{i}.txt', b'x') for i in range(11)]
        s = MultiFileUploadSerializer(data={'files': files})
        self.assertFalse(s.is_valid())
        self.assertIn('files', s.errors)

    def test_valid_batch(self):
        files = [SimpleUploadedFile(f'f{i}.txt', b'x') for i in range(3)]
        s = MultiFileUploadSerializer(data={'files': files})
        self.assertTrue(s.is_valid())


class FileDeleteSerializerTest(TestCase):

    def test_valid(self):
        s = FileDeleteSerializer(data={'public_id': 'twinengine/uploads/abc', 'resource_type': 'raw'})
        self.assertTrue(s.is_valid())

    def test_invalid_resource_type(self):
        s = FileDeleteSerializer(data={'public_id': 'x', 'resource_type': 'audio'})
        self.assertFalse(s.is_valid())


# ---------------------------------------------------------------------------
# API tests (mocked Cloudinary)
# ---------------------------------------------------------------------------
class FileUploadViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='uploader', password='pass1234')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.cloudinary_service.views.CloudinaryUploadService.upload_file')
    def test_upload_success(self, mock_upload):
        mock_upload.return_value = {
            'success': True,
            'url': 'https://res.cloudinary.com/demo/file.txt',
            'public_id': 'twinengine/uploads/file',
            'resource_type': 'raw',
            'original_filename': 'file.txt',
            'format': 'txt',
            'bytes': 5,
        }
        f = SimpleUploadedFile('file.txt', b'hello', content_type='text/plain')
        resp = self.client.post('/api/upload/', {'file': f}, format='multipart')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data['success'])

    @patch('apps.cloudinary_service.views.CloudinaryUploadService.upload_file')
    def test_upload_failure(self, mock_upload):
        mock_upload.return_value = {'success': False, 'error': 'Cloudinary down'}
        f = SimpleUploadedFile('file.txt', b'hello')
        resp = self.client.post('/api/upload/', {'file': f}, format='multipart')
        self.assertEqual(resp.status_code, 502)

    def test_upload_unauthenticated(self):
        client = APIClient()
        f = SimpleUploadedFile('file.txt', b'hello')
        resp = client.post('/api/upload/', {'file': f}, format='multipart')
        self.assertEqual(resp.status_code, 401)


class MultiFileUploadViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='multi_up', password='pass1234')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.cloudinary_service.views.CloudinaryUploadService.upload_file')
    def test_multi_upload_success(self, mock_upload):
        mock_upload.return_value = {
            'success': True, 'url': 'https://example.com/file',
            'public_id': 'id', 'resource_type': 'raw',
            'original_filename': 'f', 'format': 'txt', 'bytes': 1,
        }
        f1 = SimpleUploadedFile('a.txt', b'a')
        f2 = SimpleUploadedFile('b.txt', b'b')
        resp = self.client.post('/api/upload/multi/', {'files': [f1, f2], 'folder': 'test'}, format='multipart')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(len(resp.data['uploaded']), 2)


class FileDeleteViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='deleter', password='pass1234')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.cloudinary_service.views.CloudinaryUploadService.delete_file')
    def test_delete_success(self, mock_delete):
        mock_delete.return_value = {'success': True}
        resp = self.client.delete(
            '/api/upload/delete/',
            {'public_id': 'twinengine/uploads/abc', 'resource_type': 'raw'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)

    @patch('apps.cloudinary_service.views.CloudinaryUploadService.delete_file')
    def test_delete_failure(self, mock_delete):
        mock_delete.return_value = {'success': False, 'error': 'not found'}
        resp = self.client.delete(
            '/api/upload/delete/',
            {'public_id': 'bad_id', 'resource_type': 'raw'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)
