from rest_framework import serializers


class FileUploadSerializer(serializers.Serializer):
    """Serializer for generic file upload."""
    file = serializers.FileField(help_text="File to upload (image, PDF, CSV, etc.)")
    folder = serializers.CharField(
        required=False,
        default="uploads",
        help_text="Sub-folder in Cloudinary (e.g., 'reports', 'brand-logos', 'menus')",
    )

    def validate_file(self, value):
        # Max 10 MB
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File too large. Max size is 10 MB, got {value.size / (1024*1024):.1f} MB."
            )
        return value


class MultiFileUploadSerializer(serializers.Serializer):
    """Serializer for uploading multiple files at once."""
    files = serializers.ListField(
        child=serializers.FileField(),
        help_text="List of files to upload",
    )
    folder = serializers.CharField(
        required=False,
        default="uploads",
        help_text="Sub-folder in Cloudinary",
    )

    def validate_files(self, value):
        max_size = 10 * 1024 * 1024
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 files per request.")
        for f in value:
            if f.size > max_size:
                raise serializers.ValidationError(
                    f"File '{f.name}' is too large. Max size is 10 MB."
                )
        return value


class FileDeleteSerializer(serializers.Serializer):
    """Serializer for deleting a file from Cloudinary."""
    public_id = serializers.CharField(help_text="Cloudinary public_id of the file")
    resource_type = serializers.ChoiceField(
        choices=["image", "raw", "video"],
        default="image",
        help_text="Cloudinary resource type",
    )
