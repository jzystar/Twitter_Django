from rest_framework.pagination import BasePagination
from rest_framework.response import Response


# /api/tweets/?user_id=1&created_at__lt=...
class EndlessPagination(BasePagination):
    page_size = 20
    has_next_page = False

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

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data
        })