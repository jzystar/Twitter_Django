from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class FriendshipPagination(PageNumberPagination):
    # http://.../api/friendships/<id>/followers/?page=3&size=10
    page_size = 20 # default page size if user doesn't provide size
    page_size_query_param = 'size' # default is None
    max_page_size = 20 # default is None

    def get_paginated_response(self, data):
        return Response({
            'total_result': self.page.paginator.count,
            'total_page': self.page.paginator.num_pages,
            'page_number': self.page.number,
            'has_next_page': self.page.has_next(),
            'results': data,
        })