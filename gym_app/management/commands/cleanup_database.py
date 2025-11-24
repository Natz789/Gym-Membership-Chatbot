# Create this file: gym_app/management/commands/cleanup_database.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from gym_app.models import (
    MembershipPlan, FlexibleAccess, UserMembership, 
    Payment, WalkInPayment, Analytics, AuditLog, Attendance
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean up database - remove all data except superusers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm database cleanup',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  WARNING: This will delete ALL data except superusers!\n'
                    'This includes:\n'
                    '  - All members, staff users, and their data\n'
                    '  - All memberships and payments\n'
                    '  - All walk-in sales\n'
                    '  - All attendance records\n'
                    '  - All analytics data\n'
                    '  - All audit logs\n'
                    '  - All membership plans and walk-in passes\n\n'
                    'To proceed, run: python manage.py cleanup_database --confirm\n'
                )
            )
            return

        self.stdout.write(self.style.WARNING('\n🗑️  Starting database cleanup...\n'))

        # Count records before deletion
        stats = {
            'Attendance': Attendance.objects.count(),
            'Audit Logs': AuditLog.objects.count(),
            'Analytics': Analytics.objects.count(),
            'Walk-in Payments': WalkInPayment.objects.count(),
            'Member Payments': Payment.objects.count(),
            'User Memberships': UserMembership.objects.count(),
            'Walk-in Passes': FlexibleAccess.objects.count(),
            'Membership Plans': MembershipPlan.objects.count(),
            'Non-superusers': User.objects.filter(is_superuser=False).count(),
        }

        self.stdout.write(self.style.WARNING('📊 Records to be deleted:'))
        for key, value in stats.items():
            self.stdout.write(f'   {key}: {value}')

        # Delete in correct order (respecting foreign keys)
        
        # 1. Delete attendance records
        Attendance.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Deleted all attendance records'))

        # 2. Delete audit logs
        AuditLog.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Deleted all audit logs'))

        # 3. Delete analytics
        Analytics.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Deleted all analytics'))

        # 4. Delete walk-in payments
        WalkInPayment.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Deleted all walk-in payments'))

        # 5. Delete member payments
        Payment.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Deleted all member payments'))

        # 6. Delete user memberships
        UserMembership.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Deleted all user memberships'))

        # 7. Delete walk-in passes
        FlexibleAccess.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Deleted all walk-in passes'))

        # 8. Delete membership plans
        MembershipPlan.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✓ Deleted all membership plans'))

        # 9. Delete non-superuser accounts
        non_superusers = User.objects.filter(is_superuser=False)
        deleted_count = non_superusers.count()
        non_superusers.delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {deleted_count} non-superuser accounts'))

        # Show remaining superusers
        superusers = User.objects.filter(is_superuser=True)
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Database cleanup complete!')
        )
        self.stdout.write(
            self.style.WARNING(f'\n👥 Remaining superuser accounts ({superusers.count()}):')
        )
        for user in superusers:
            self.stdout.write(f'   - {user.username} ({user.email})')

        self.stdout.write(
            self.style.SUCCESS(
                '\n💡 Next steps:\n'
                '   1. Create sample membership plans\n'
                '   2. Create sample walk-in passes\n'
                '   3. Register test members\n'
                '   4. Test the kiosk system\n'
            )
        )