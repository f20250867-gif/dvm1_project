from django.http import HttpResponse

def debug_host(request):
    return HttpResponse(
        f"""
        host={request.get_host()}<br>
        META_HOST={request.META.get('HTTP_HOST')}<br>
        X_FORWARDED_HOST={request.META.get('HTTP_X_FORWARDED_HOST')}<br>
        SERVER_PORT={request.META.get('SERVER_PORT')}<br>
        """
    )