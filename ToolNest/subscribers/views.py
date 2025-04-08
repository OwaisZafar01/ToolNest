

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Subscriber
from django.utils import timezone

@csrf_exempt
def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'})
            
        # Check if email already exists
        if Subscriber.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False, 
                'errors': '{"email":[{"message":"This email is already subscribed!","code":"unique"}]}'
            })
            
        
        try:
            subscriber = Subscriber(email=email)
            subscriber.save()  
            return JsonResponse({
                'success': True, 
                'message': 'Thanks for subscribing! We will keep you updated on our new tools.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)