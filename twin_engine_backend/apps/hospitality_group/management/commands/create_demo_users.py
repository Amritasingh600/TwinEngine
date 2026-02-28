"""
Management command to create demo data for testing authentication.
Creates a brand, outlet, and test users with different roles.

Usage:
    python manage.py create_demo_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.hospitality_group.models import Brand, Outlet, UserProfile


class Command(BaseCommand):
    help = 'Creates demo brand, outlet, and users for testing authentication'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Creating demo data...'))
        
        # Create Brand
        brand, created = Brand.objects.get_or_create(
            corporate_id='DEMO001',
            defaults={
                'name': 'Demo Restaurant Group',
                'contact_email': 'admin@demorestaurant.com',
                'subscription_tier': 'PRO',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created Brand: {brand.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'○ Brand already exists: {brand.name}'))
        
        # Create Outlet
        outlet, created = Outlet.objects.get_or_create(
            brand=brand,
            name='Downtown Cafe',
            defaults={
                'address': '123 Main Street, Downtown',
                'city': 'Mumbai',
                'seating_capacity': 50,
                'opening_time': '09:00:00',
                'closing_time': '22:00:00',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created Outlet: {outlet.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'○ Outlet already exists: {outlet.name}'))
        
        # Create demo users
        users_data = [
            {
                'username': 'manager_demo',
                'email': 'manager@demo.com',
                'password': 'manager123',
                'role': 'MANAGER',
                'phone': '+91-9876543211'
            },
            {
                'username': 'waiter_demo',
                'email': 'waiter@demo.com',
                'password': 'waiter123',
                'role': 'WAITER',
                'phone': '+91-9876543212'
            },
            {
                'username': 'chef_demo',
                'email': 'chef@demo.com',
                'password': 'chef123',
                'role': 'CHEF',
                'phone': '+91-9876543213'
            }
        ]
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Creating demo users...'))
        
        for user_data in users_data:
            # Create or get user
            user, user_created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                }
            )
            
            if user_created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created User: {user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'○ User already exists: {user.username}'))
            
            # Create or get profile
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'outlet': outlet,
                    'role': user_data['role'],
                    'phone': user_data['phone'],
                }
            )
            
            if profile_created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created Profile: {user_data["role"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ○ Profile already exists'))
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Demo Data Created Successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Test Credentials:'))
        self.stdout.write('')
        self.stdout.write('Manager:')
        self.stdout.write('  Username: manager_demo')
        self.stdout.write('  Password: manager123')
        self.stdout.write('')
        self.stdout.write('Waiter:')
        self.stdout.write('  Username: waiter_demo')
        self.stdout.write('  Password: waiter123')
        self.stdout.write('')
        self.stdout.write('Chef:')
        self.stdout.write('  Username: chef_demo')
        self.stdout.write('  Password: chef123')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Test API:'))
        self.stdout.write('  POST http://127.0.0.1:8000/api/auth/token/')
        self.stdout.write('  Body: {"username": "manager_demo", "password": "manager123"}')
        self.stdout.write('')
