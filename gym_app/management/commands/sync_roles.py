from django.core.management.base import BaseCommand
from gym_app.models import User


class Command(BaseCommand):
    help = 'Sync user roles with Django permissions (superuser → admin, staff → staff)'

    def handle(self, *args, **kwargs):
        # Sync superusers to admin role
        superusers = User.objects.filter(is_superuser=True).exclude(role='admin')
        admin_count = superusers.update(role='admin')
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Synced {admin_count} superuser(s) to admin role')
        )
        
        # Sync staff users to staff role (only if they're currently members)
        staff_users = User.objects.filter(
            is_staff=True, 
            is_superuser=False,
            role='member'
        )
        staff_count = staff_users.update(role='staff')
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Synced {staff_count} staff user(s) to staff role')
        )
        
        # Summary
        total_admins = User.objects.filter(role='admin').count()
        total_staff = User.objects.filter(role='staff').count()
        total_members = User.objects.filter(role='member').count()
        
        self.stdout.write(
            self.style.SUCCESS(f'\n📊 Current Role Distribution:')
        )
        self.stdout.write(f'   Admins: {total_admins}')
        self.stdout.write(f'   Staff: {total_staff}')
        self.stdout.write(f'   Members: {total_members}')
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Role synchronization complete!')
        )