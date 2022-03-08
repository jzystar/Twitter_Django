def profile_changed(sender, instance, **kwargs):
    from accounts.services import UserService
    return UserService.invalidate_profile_cache(instance.user_id)