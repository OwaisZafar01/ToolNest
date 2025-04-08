

from django.shortcuts import render, redirect
from django.http import HttpResponse
import random
import string
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

def generate_short_url():
    letters = ''.join(random.choices(string.ascii_letters, k=3))
    digits = ''.join(random.choices(string.digits, k=3))
    chars = letters + digits
    return chars

@csrf_exempt
def urlshorten(request):
    context = {}
    
    if request.method == 'POST':
        original_url = request.POST.get('url')
        
        if not original_url:
            context['error'] = 'Please enter a valid URL'
            return render(request, 'urlshorten.html', context)
        
        short_url = generate_short_url()
        cache.set(f"url_shortener_{short_url}", original_url, timeout=None)
        domain = request.build_absolute_uri('/').rstrip('/')
        full_short_url = f"{domain}/{short_url}"
        
        context['original_url'] = original_url
        context['short_url'] = full_short_url
    
    return render(request, 'urlshorten.html', context)

def redirect_to_original(request, short_code):
    original_url = cache.get(f"url_shortener_{short_code}")
    
    if original_url:
        return redirect(original_url)
    else:
        return HttpResponse("URL not found", status=404)
