from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from comments.api.permissions import IsObjectOwner
from comments.models import Comment
from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
    CommentSerializerForUpdate
)


class CommentViewSet(viewsets.GenericViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializerForCreate

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['update', 'destroy']:
            return [IsAuthenticated(), IsObjectOwner()]
        return [AllowAny()]


    def create(self, request, *args, **kwargs):
        serializer = CommentSerializerForCreate(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        comment = serializer.save()

        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )
    # have to add *args and **kwargs, otherwise, no pk.
    def update(self, request, *args, **kwargs):
        # self.get_object() will check from queryset if comment exist.
        # return 404 if not exist
        comment = self.get_object()
        serializer = CommentSerializerForUpdate(
            instance = comment,
            data=request.data
        )
        # check if length is within 140 chars
        if not serializer.is_valid():
            return Response({
                'message': 'Please check your input.'
            }, status=status.HTTP_400_BAD_REQUEST)
        # save will call update if parameter has instance, otherwise call create
        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        # comment.delete()
        Comment.objects.filter(id=comment.id).delete()

        return Response({'success': True}, status=status.HTTP_200_OK)