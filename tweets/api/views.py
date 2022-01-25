from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import (
    TweetSerializer,
    TweetSerializerForCreate,
    TweetSerializerWithComment,
)
from tweets.models import Tweet
from newsfeeds.services import NewsFeedService
from utils.decorators import required_param


class TweetViewSet(viewsets.GenericViewSet):
    serializer_class = TweetSerializerForCreate
    queryset = Tweet.objects.all()

    def get_permissions(self):
        # action - the name of the current action (e.g., list, create).
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


    @required_param(params=['user_id'])
    def list(self, request): # get tweets without logging in
        # if 'user_id' not in request.query_params:
        #     return Response({'error': 'missing user_id'}, status=400)

        user_id = request.query_params['user_id']
        tweets = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
        serializer = TweetSerializer(tweets, many=True)

        return Response({'tweets': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()
        return Response(
            TweetSerializerWithComment(tweet).data,
            status=status.HTTP_200_OK
        )

    def create(self, request):
        serializer = TweetSerializerForCreate(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check input.',
                'errors': serializer.errors
            }, status=400)
        tweet = serializer.save() # call create method in TweetSerializerForCreate
        NewsFeedService.fanout_to_followers(tweet)

        return Response(TweetSerializer(tweet).data, status=201)