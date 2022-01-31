from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from newsfeeds.models import NewsFeed
from newsfeeds.api.serializers import NewsFeedSerializer


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        serializer = NewsFeedSerializer(
            NewsFeed.objects.filter(user=self.request.user),
            context={'request': request},
            many=True,
        )
        return Response({
            'newsfeeds': serializer.data
        }, status=status.HTTP_200_OK)