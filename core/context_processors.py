

# from .models import Message

# def unread_message_count(request):
#     if request.user.is_authenticated:
#         count = Message.objects.filter(recipient=request.user, is_read=False).count()
#     else:
#         count = 0
#     return {'unread_message_count': count}

# core/context_processors.py
def user_profile(request):
    if request.user.is_authenticated:
        from .models import UserProfile  # İçe aktarma işlemi fonksiyon içinde
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        return {'user_profile': profile}
    else:
        return {}