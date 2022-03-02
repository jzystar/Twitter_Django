from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from newsfeeds.models import NewsFeed
from newsfeeds.api.serializers import NewsFeedSerializer
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def list(self, request):
        newsfeed = NewsFeed.objects.filter(user=self.request.user)
        newsfeed = self.paginate_queryset(newsfeed)
        serializer = NewsFeedSerializer(
            newsfeed,
            context={'request': request},
            many=True,
        )

        return self.get_paginated_response(serializer.data)