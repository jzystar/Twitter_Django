from dateutil import parser
from django.conf import settings
from rest_framework.pagination import BasePagination
from rest_framework.response import Response


# /api/tweets/?user_id=1&created_at__lt=...
class EndlessPagination(BasePagination):
    page_size = 20
    has_next_page = False

    def paginate_ordered_list(self, reverse_ordered_list, request):
        if 'created_at__gt' in request.query_params:
            # '2021-11-02 13:21:23.123456'
            created_at__gt = parser.isoparse(request.query_params['created_at__gt'])
            objects = []
            for obj in reverse_ordered_list:
                if obj.created_at > created_at__gt:
                    objects.append(obj)
                else:
                    break
            self.has_next_page = False

            return objects

        index = 0
        if 'created_at__lt' in request.query_params:
            created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            for index, obj in enumerate(reverse_ordered_list):
                if obj.created_at < created_at__lt:
                    break
            else:
                reverse_ordered_list = []
        # moment when get into someone's tweets list
        self.has_next_page = len(reverse_ordered_list) - 1 >= index + self.page_size

        return reverse_ordered_list[index: index + self.page_size]

    def paginate_queryset(self, queryset, request, view=None):
        if 'created_at__gt' in request.query_params:
            queryset = queryset.filter(created_at__gt=request.query_params['created_at__gt'])
            self.has_next_page = False

            return queryset.order_by('-created_at')

        if 'created_at__lt' in request.query_params:
            queryset = queryset.filter(created_at__lt=request.query_params['created_at__lt'])

        # check is there are more tweets one next page, so get one more zie
        queryset = queryset.order_by('-created_at')[:self.page_size + 1]
        self.has_next_page = len(queryset) > self.page_size
        return queryset[:self.page_size]

    def paginated_cached_list_in_redis(self, cached_list, request):
        paginated_list = self.paginate_ordered_list(cached_list, request)
        if 'created_at__gt' in request.query_params:
            return paginated_list
        # if having next page, meaning still have cached data in cached_list
        if self.has_next_page:
            return paginated_list
        # if not having next page, and cached_list has all cached data
        if len(cached_list) < settings.REDIS_LIST_LENGTH_LIMIT:
            return paginated_list
        # if len(cached_list) == settings.REDIS_LIST_LENGTH_LIMIT,
        # which means maybe there is some data in DB.
        return None

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data
        })