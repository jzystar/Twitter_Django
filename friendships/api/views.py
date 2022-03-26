from friendships.api.paginations import FriendshipPagination
from friendships.api.serializers import (
    FollowerSerializer,
    FollowingSerializer,
    FollowingSerializerForCreate
)
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from friendships.models import Friendship
from friendships.services import FriendshipService
from ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


class FriendshipViewSet(viewsets.GenericViewSet):
    serializer_class = FollowingSerializerForCreate
    # 我们希望 POST /api/friendship/1/follow 是去 follow user_id=1 的用户
    # 因此这里 queryset 需要是 User.objects.all()
    # 如果是 Friendship.objects.all 的话就会出现 404 Not Found
    # 因为 detail=True 的 actions 会默认先去调用 get_object() 也就是
    # queryset.filter(pk=1) 查询一下这个 object 在不在
    queryset = User.objects.all()
    pagination_class = FriendshipPagination
    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    @method_decorator(ratelimit(key='user_or_ip', rate='3/s', method='GET', block=True))
    def followers(self, request, pk):
        friendships = Friendship.objects.filter(to_user=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships) # do list slicing
        serializer = FollowerSerializer(page, many=True, context={'request': request})

        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    @method_decorator(ratelimit(key='user_or_ip', rate='3/s', method='GET', block=True))
    def followings(self, request, pk):
        friendships = Friendship.objects.filter(from_user=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowingSerializer(page, many=True, context={'request': request})

        return self.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    @method_decorator(ratelimit(key='user', rate='10/s', method='POST', block=True))
    def follow(self, request, pk):
        self.get_object() #check if to_user=pk exist, it not exist return 404

        if FriendshipService.has_followed(request.user.id, int(pk)):
            return Response({
                'success': False,
                'message': 'Please check your input.',
                'errors': [{'pk': 'You have followed user with id = {}'.format(pk)}]
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = FollowingSerializerForCreate(
            data = {
                'from_user_id': request.user.id,
                'to_user_id': pk
            }
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check your input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        friendships = serializer.save()

        return Response(
            FollowingSerializer(friendships, context={'request': request}).data,
            status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    @method_decorator(ratelimit(key='user', rate='10/s', method='POST', block=True))
    def unfollow(self, request, pk):
        unfollow_user = self.get_object() #check if to_user=pk exist, it not exist return 404
        if unfollow_user.id == request.user.id:
            return Response({
                'success': False,
                'message': 'You cannot unfollow yourself.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # deleted: how many were deleted, _: how many were deleted for each category
        deleted, _ = Friendship.objects.filter(
            from_user=request.user,
            to_user=unfollow_user
        ).delete()

        return Response({
            'success': True,
            'deleted': deleted
        })

    def list(self, request):
        return Response({
            'message': 'followers homepage.'
        })