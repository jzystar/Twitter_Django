from django.utils.decorators import method_decorator
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from ratelimit.decorators import ratelimit
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        return NewsFeedService.get_cached_newsfeeds(self.request.user.id)
        # return NewsFeed.objects.filter(user=self.request.user)

    @method_decorator(ratelimit(key='user', rate='5/s', method='GET', block=True))
    def list(self, request):
        cached_newsfeeds_list = self.get_queryset()
        newsfeeds = self.paginator.paginated_cached_list_in_redis(cached_newsfeeds_list, request)
        # if none, which means data is not in redis cache, then pull from DB.
        if newsfeeds is None:
            queryset = NewsFeed.objects.filter(user=request.user)
            newsfeeds = self.paginate_queryset(queryset)

        serializer = NewsFeedSerializer(
            newsfeeds,
            context={'request': request},
            many=True,
        )

        return self.get_paginated_response(serializer.data)