from .models import Store

def current_store(request):
    store = None

    # إذا كان عندك /store/<slug>/ بالمسار
    slug = request.resolver_match.kwargs.get("store_slug") or \
           request.resolver_match.kwargs.get("slug")

    if slug:
        try:
            store = Store.objects.get(slug=slug)
        except Store.DoesNotExist:
            store = None

    return {
        "current_store": store
    }
