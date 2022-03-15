def push_tweet_to_cache(sender, instance, created, **kwargs):
    from tweets.services import TweetService
    if not created: # updates shouldn't append tweet to list
        return

    TweetService.push_tweet_to_cache(instance)