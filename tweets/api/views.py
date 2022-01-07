from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import TweetSerializer, TweetSerializerForCreate
from tweets.models import Tweet


class TweetViewSet(viewsets.GenericViewSet):
    serializer_class = TweetSerializerForCreate

    def get_permissions(self):
        # action - the name of the current action (e.g., list, create).
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request): # get tweets without logging in
        if 'user_id' not in request.query_params:
            return Response({'error': 'missing user_id'}, status=400)

        user_id = request.query_params['user_id']
        tweets = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
        serializer = TweetSerializer(tweets, many=True)

        return Response({'tweets': serializer.data})

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

        return Response(TweetSerializer(tweet).data, status=201)