from rest_framework import viewsets, status
from notifications.models import Notification
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from inbox.api.serializers import (
    NotificationSerializer,
    NotificationSerializerForUpdate,
)


class NotificationViewSet(viewsets.GenericViewSet, viewsets.mixins.ListModelMixin):

    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationSerializerForUpdate
    filterset_fields = ('unread',) # unread can be used to be filtered by ListModelMixin
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(methods=['GET'], detail=False, url_path='unread-count')
    def unread_count(self, request):
        count = self.get_queryset().filter(unread=True).count()
        return Response({
            'unread_count': count
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='mark-all-as-read')
    def mark_all_as_read(self, request):
        updated_count = self.get_queryset().filter(unread=True).update(unread=False)
        return Response({
            'marked_count': updated_count
        }, status=status.HTTP_200_OK)

    # /api/notifications/1/
    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        serializer = NotificationSerializerForUpdate(
            instance = notification,
            data = request.data,
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check your input.'
            }, status=status.HTTP_400_BAD_REQUEST)

        notification = serializer.save()
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK
        )