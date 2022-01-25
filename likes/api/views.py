from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from likes.models import Like
from likes.api.serializers import (
    LikeSerializerForCreate,
    LikeSerializer
)


class LikeViewSet(viewsets.GenericViewSet):
    queryset = Like.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class =  LikeSerializerForCreate

    def create(self, request, *args, **kwargs):
        serializer = LikeSerializerForCreate(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check your input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        like = serializer.save()

        return Response(
            LikeSerializer(like).data,
            status=status.HTTP_201_CREATED
        )