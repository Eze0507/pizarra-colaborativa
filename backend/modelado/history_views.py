from django.http import Http404
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .history import execute_history, load_history, history_error
from .models import Proyecto


class HistoryCommandSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['undo', 'redo', 'restore'])
    kind = serializers.ChoiceField(choices=['any', 'entity', 'attribute', 'method', 'relationship'], required=False)
    name = serializers.CharField(max_length=150, required=False)
    owner = serializers.CharField(max_length=150, required=False)
    endpoints = serializers.ListField(child=serializers.CharField(max_length=150), min_length=2, max_length=2, required=False)
    latest = serializers.BooleanField(required=False)
    operation_id = serializers.UUIDField(required=False)


class HistoryRequestSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=100)
    expected_revision = serializers.IntegerField(min_value=0)
    command = HistoryCommandSerializer()


class DiagramHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            return Response(load_history(pk, request.user))
        except Proyecto.DoesNotExist as exc:
            raise Http404 from exc

    def post(self, request, pk):
        serializer = HistoryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if values['command'].get('operation_id'):
            values['command']['operation_id'] = str(values['command']['operation_id'])
        try:
            return Response(execute_history(pk, request.user, values['command'], values['expected_revision'], values['request_id']))
        except Proyecto.DoesNotExist as exc:
            raise Http404 from exc
        except Exception as exc:
            error = history_error(exc)
            return Response(error, status=403 if error['codigo'] == 'permission_denied' else 409)
