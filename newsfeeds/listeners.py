def push_newsfeed_to_cache(sender, instance, created, **kwargs):
    from newsfeeds.services import NewsFeedService
    if not created:
        return

    NewsFeedService.push_newsfeed_to_cache(instance)