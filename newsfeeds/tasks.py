from celery import shared_task
from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from tweets.models import Tweet
from utils.time_constants import ONE_HOUR


@shared_task(time_limit=ONE_HOUR)
def fanout_newsfeeds_tasks(tweet_id):
    # import here since there is a cycle import
    from newsfeeds.services import NewsFeedService

    tweet = Tweet.objects.get(id=tweet_id) # get not filter
    followers = FriendshipService.get_followers(tweet.user)
    # crate N queries, too slow.
    # for follower in followers:
    #     NewsFeed.objects.create(user=follower, tweet=tweet)

    newsfeeds = [
        # this won't do query insertion without .save()
        NewsFeed(user=follower, tweet=tweet)
        for follower in followers
    ]
    newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
    NewsFeed.objects.bulk_create(newsfeeds)
    # bulk_create won't trigger post_save signal
    for newsfeed in newsfeeds:
        NewsFeedService.push_newsfeed_to_cache(newsfeed)