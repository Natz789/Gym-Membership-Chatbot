# Create this file: gym_app/management/commands/create_sample_data.py

from django.core.management.base import BaseCommand
from gym_app.models import MembershipPlan, FlexibleAccess
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample membership plans and walk-in passes'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n🎯 Creating sample data...\n'))

        # Create Membership Plans
        plans_data = [
            {
                'name': 'Weekly Pass',
                'duration_days': 7,
                'price': Decimal('500.00'),
                'description': 'Perfect for trying out the gym. 7 days of full access to all facilities.'
            },
            {
                'name': 'Monthly Membership',
                'duration_days': 30,
                'price': Decimal('1500.00'),
                'description': '30 days of unlimited gym access. Most popular choice!'
            },
            {
                'name': 'Quarterly Membership',
                'duration_days': 90,
                'price': Decimal('4000.00'),
                'description': '3 months of commitment for serious fitness goals. Save ₱500!'
            },
            {
                'name': 'Semi-Annual Premium',
                'duration_days': 180,
                'price': Decimal('7500.00'),
                'description': '6 months of premium gym access. Best value with ₱1500 savings!'
            },
            {
                'name': 'Annual VIP Membership',
                'duration_days': 365,
                'price': Decimal('14000.00'),
                'description': 'Full year of VIP access. Ultimate savings of ₱4000!'
            },
        ]

        for plan_data in plans_data:
            plan, created = MembershipPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults={
                    'duration_days': plan_data['duration_days'],
                    'price': plan_data['price'],
                    'description': plan_data['description'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created plan: {plan.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Plan already exists: {plan.name}'))

        # Create Walk-in Passes
        passes_data = [
            {
                'name': 'Single Day Pass',
                'duration_days': 1,
                'price': Decimal('100.00'),
                'description': 'One-time gym access for a single day. Try before you buy!'
            },
            {
                'name': '3-Day Trial Pass',
                'duration_days': 3,
                'price': Decimal('250.00'),
                'description': '3 consecutive days of gym access. Perfect for visitors!'
            },
            {
                'name': '5-Day Flex Pass',
                'duration_days': 5,
                'price': Decimal('400.00'),
                'description': '5 days of flexible gym access within a week.'
            },
        ]

        for pass_data in passes_data:
            pass_obj, created = FlexibleAccess.objects.get_or_create(
                name=pass_data['name'],
                defaults={
                    'duration_days': pass_data['duration_days'],
                    'price': pass_data['price'],
                    'description': pass_data['description'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created pass: {pass_obj.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Pass already exists: {pass_obj.name}'))

        # Summary
        total_plans = MembershipPlan.objects.count()
        total_passes = FlexibleAccess.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Sample data creation complete!\n'
                f'   📋 Membership Plans: {total_plans}\n'
                f'   🎫 Walk-in Passes: {total_passes}\n\n'
                f'💡 You can now:\n'
                f'   - Visit /plans/ to view membership plans\n'
                f'   - Visit /kiosk/ to test the attendance kiosk\n'
                f'   - Register test members to try the system\n'
            )
        )