from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        return NewsFeedService.get_cached_newsfeeds(self.request.user.id)
        # return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        newsfeed = self.paginate_queryset(self.get_queryset())
        serializer = NewsFeedSerializer(
            newsfeed,
            context={'request': request},
            many=True,
        )

        return self.get_paginated_response(serializer.data)