def studyos_preferences(request):
    if not request.user.is_authenticated:
        return {'studyos_theme': 'light'}
    pref = getattr(request.user, 'preference', None)
    return {'studyos_theme': getattr(pref, 'theme', 'light')}
