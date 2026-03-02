import logging

from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import FileUploadSerializer, MultiFileUploadSerializer, FileDeleteSerializer
from .upload import CloudinaryUploadService

logger = logging.getLogger(__name__)


class FileUploadView(APIView):
    """
    POST /api/upload/
    Upload a single file (image, PDF, CSV, etc.) to Cloudinary.

    Request (multipart/form-data):
        file   - the file to upload (required)
        folder - Cloudinary sub-folder (optional, default "uploads")

    Response 201:
        {
            "success": true,
            "url": "https://res.cloudinary.com/…",
            "public_id": "twinengine/uploads/abc123",
            "resource_type": "raw",
            "original_filename": "report.pdf",
            "format": "pdf",
            "bytes": 12345
        }
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        folder = serializer.validated_data.get("folder", "uploads")

        result = CloudinaryUploadService.upload_file(uploaded_file, folder=folder)

        if result["success"]:
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(result, status=status.HTTP_502_BAD_GATEWAY)


class MultiFileUploadView(APIView):
    """
    POST /api/upload/multi/
    Upload multiple files at once (max 10).

    Request (multipart/form-data):
        files  - list of files (required)
        folder - Cloudinary sub-folder (optional)

    Response 201:
        {
            "uploaded": [ { …result… }, … ],
            "failed": [ { "filename": "x.pdf", "error": "…" } ]
        }
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MultiFileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        files = serializer.validated_data["files"]
        folder = serializer.validated_data.get("folder", "uploads")

        uploaded = []
        failed = []

        for f in files:
            result = CloudinaryUploadService.upload_file(f, folder=folder)
            if result["success"]:
                uploaded.append(result)
            else:
                failed.append({"filename": f.name, "error": result["error"]})

        http_status = status.HTTP_201_CREATED if uploaded else status.HTTP_502_BAD_GATEWAY
        return Response({"uploaded": uploaded, "failed": failed}, status=http_status)


class FileDeleteView(APIView):
    """
    DELETE /api/upload/delete/
    Delete a file from Cloudinary by its public_id.

    Request (JSON):
        {
            "public_id": "twinengine/uploads/abc123",
            "resource_type": "raw"
        }

    Response 200:
        { "success": true }
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        serializer = FileDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        public_id = serializer.validated_data["public_id"]
        resource_type = serializer.validated_data.get("resource_type", "image")

        result = CloudinaryUploadService.delete_file(public_id, resource_type=resource_type)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
