from django.urls import path
from .views import FileUploadView, MultiFileUploadView, FileDeleteView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('upload/multi/', MultiFileUploadView.as_view(), name='multi-file-upload'),
    path('upload/delete/', FileDeleteView.as_view(), name='file-delete'),
]
