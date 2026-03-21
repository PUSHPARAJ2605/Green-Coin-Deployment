import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'civicwaste.settings')
django.setup()

from accounts.models import CustomUser

def seed():
    # Citizen
    if not CustomUser.objects.filter(email='citizen@gmail.com').exists():
        CustomUser.objects.create_user(
            email='citizen@gmail.com',
            password='123456',
            full_name='John Citizen',
            role='citizen'
        )
        print("Created citizen@gmail.com")
    
    # Collector
    if not CustomUser.objects.filter(email='collector@gmail.com').exists():
        CustomUser.objects.create_user(
            email='collector@gmail.com',
            password='123456',
            full_name='Mike Collector',
            role='collector'
        )
        print("Created collector@gmail.com")

if __name__ == '__main__':
    seed()
