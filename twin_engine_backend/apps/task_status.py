"""
Generic Celery task-status polling endpoint.

GET /api/tasks/<task_id>/  →  { task_id, status, result | error, ... }
"""
from celery.result import AsyncResult
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes


class TaskStatusSerializer(serializers.Serializer):
    """Schema for the task-status response."""
    task_id = serializers.CharField()
    status = serializers.ChoiceField(choices=[
        'PENDING', 'STARTED', 'PROGRESS', 'SUCCESS', 'FAILURE', 'RETRY', 'REVOKED',
    ])
    result = serializers.JSONField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
    date_done = serializers.DateTimeField(required=False, allow_null=True)


class TaskStatusView(APIView):
    """
    Poll the status of any Celery task by its ID.

    Returns the task state and, once finished, the result or error.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Tasks'],
        summary='Poll Celery task status',
        responses={200: TaskStatusSerializer},
    )
    def get(self, request, task_id: str):
        result = AsyncResult(task_id)

        payload = {
            'task_id': task_id,
            'status': result.status,
            'result': None,
            'error': None,
            'date_done': None,
        }

        if result.successful():
            payload['result'] = result.result
        elif result.failed():
            payload['error'] = str(result.result)  # result holds the exception

        if result.date_done:
            payload['date_done'] = result.date_done.isoformat()

        return Response(payload)
