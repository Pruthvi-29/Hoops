from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactMessage
import json
import threading

def send_email_async(subject, message, from_email, recipient_list):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=True,
        )
    except Exception as e:
        print(f'Email error: {e}')

@csrf_exempt
def contact_submit(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            phone = data.get('phone', '').strip()
            message = data.get('message', '').strip()

            if not all([name, email, phone, message]):
                return JsonResponse({'success': False, 'error': 'All fields required'}, status=400)

            # Save to database immediately
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message,
            )

            # Send email in background thread
            thread = threading.Thread(
                target=send_email_async,
                args=(
                    f'New Enquiry from {name}',
                    f'Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_RECIPIENT_EMAIL],
                )
            )
            thread.daemon = True
            thread.start()

            # Return success immediately without waiting for email
            return JsonResponse({'success': True, 'message': 'Message sent successfully!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)