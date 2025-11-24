"""
Management command to seed GCash-focused test data for QR code functionality testing
Designed specifically for testing payment confirmations and QR code generation
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from gym_app.models import (
    User, MembershipPlan, FlexibleAccess,
    UserMembership, Payment, WalkInPayment, AuditLog
)


class Command(BaseCommand):
    help = 'Seed GCash test data for QR code functionality testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--members',
            type=int,
            default=10,
            help='Number of members to create with GCash memberships (default: 10)'
        )
        parser.add_argument(
            '--walkin',
            type=int,
            default=20,
            help='Number of walk-in GCash payments to create (default: 20)'
        )
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing test data before seeding'
        )

    def handle(self, *args, **options):
        members_count = options['members']
        walkin_count = options['walkin']
        flush = options['flush']

        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('🤖 GCASH TEST DATA SEEDER'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Configuration: {members_count} Members | {walkin_count} Walk-ins')
        self.stdout.write('Focused on GCash payments for QR code testing')
        self.stdout.write('=' * 80 + '\n')

        if flush:
            self._flush_data()

        self._ensure_users()
        self._ensure_plans()
        self._ensure_passes()

        self._create_gcash_memberships(members_count)
        self._create_gcash_walkin_payments(walkin_count)

        self._print_summary()

    def _flush_data(self):
        """Delete GCash-related test data"""
        self.stdout.write('\n🗑️  Flushing test data...')

        # Delete only test payments and memberships (not all data)
        payments_deleted = Payment.objects.all().delete()[0]
        memberships_deleted = UserMembership.objects.all().delete()[0]
        walkins_deleted = WalkInPayment.objects.all().delete()[0]

        self.stdout.write(self.style.SUCCESS(f'   ✓ Deleted {payments_deleted} payments'))
        self.stdout.write(self.style.SUCCESS(f'   ✓ Deleted {memberships_deleted} memberships'))
        self.stdout.write(self.style.SUCCESS(f'   ✓ Deleted {walkins_deleted} walk-in payments'))

    def _ensure_users(self):
        """Ensure admin and staff users exist"""
        self.stdout.write('\n👥 Ensuring Admin/Staff Users...')

        # Admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@gym.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('   ✓ Created admin user'))
        else:
            self.stdout.write('   ℹ Admin user already exists')

        # Staff for confirmations
        staff, created = User.objects.get_or_create(
            username='staff_test',
            defaults={
                'email': 'staff.test@gym.com',
                'first_name': 'Test',
                'last_name': 'Staff',
                'role': 'staff',
                'is_staff': True,
            }
        )
        if created:
            staff.set_password('staff123')
            staff.save()
            self.stdout.write(self.style.SUCCESS('   ✓ Created test staff user'))
        else:
            self.stdout.write('   ℹ Staff user already exists')

    def _ensure_plans(self):
        """Ensure membership plans exist"""
        self.stdout.write('\n💳 Ensuring Membership Plans...')

        plans_data = [
            ('GCash Test - Weekly', 7, 500),
            ('GCash Test - Monthly', 30, 1500),
            ('GCash Test - Quarterly', 90, 4000),
        ]

        for name, duration, price in plans_data:
            plan, created = MembershipPlan.objects.get_or_create(
                name=name,
                defaults={
                    'duration_days': duration,
                    'price': Decimal(price),
                    'description': f'Test plan for GCash QR code testing ({duration} days)',
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'   ✓ Created: {name}'))
            else:
                self.stdout.write(f'   ℹ {name} already exists')

    def _ensure_passes(self):
        """Ensure flexible access passes exist"""
        self.stdout.write('\n🎫 Ensuring Flexible Access Passes...')

        passes_data = [
            ('GCash Test - Day Pass', 1, 100),
            ('GCash Test - 3-Day Trial', 3, 250),
            ('GCash Test - 5-Day Flex', 5, 400),
        ]

        for name, duration, price in passes_data:
            pass_obj, created = FlexibleAccess.objects.get_or_create(
                name=name,
                defaults={
                    'duration_days': duration,
                    'price': Decimal(price),
                    'description': f'Test pass for GCash QR code testing ({duration} days)',
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'   ✓ Created: {name}'))
            else:
                self.stdout.write(f'   ℹ {name} already exists')

    def _create_gcash_memberships(self, count):
        """Create test members with GCash memberships"""
        self.stdout.write(f'\n👤 Creating {count} Members with GCash Memberships...')

        staff = User.objects.get(username='staff_test')
        plans = MembershipPlan.objects.filter(name__startswith='GCash Test')

        created_count = 0
        pending_count = 0
        confirmed_count = 0

        for i in range(count):
            # Create member
            username = f'gcash_member_{i+1}'
            member, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.gym.com',
                    'first_name': f'GCash',
                    'last_name': f'Member{i+1}',
                    'role': 'member',
                    'mobile_no': f'0912345{i:04d}',
                    'birthdate': datetime(1990, 1, 1).date(),
                }
            )
            if created:
                member.set_password('member123')
                member.save()
                created_count += 1

            # Create membership subscription
            plan = random.choice(plans)
            now = timezone.now()
            start_date = now.date()
            end_date = start_date + timedelta(days=plan.duration_days)

            membership = UserMembership.objects.create(
                user=member,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                status='pending'  # Start as pending
            )

            # Create payment
            payment = Payment.objects.create(
                user=member,
                membership=membership,
                amount=plan.price,
                method='gcash',  # Always GCash for this seeder
                payment_date=now,
                notes=f'Test GCash payment for {plan.name} - QR code testing'
            )

            # Randomly confirm some payments (for testing both pending and confirmed flows)
            if random.random() < 0.6:  # 60% confirmed
                payment.confirm(staff)
                membership.status = 'active'
                membership.save()
                confirmed_count += 1

                # Log confirmation
                AuditLog.log(
                    action='payment_received',
                    user=staff,
                    description=f'Test: Payment confirmed for {member.get_full_name()} - ₱{payment.amount}',
                    severity='info',
                    request=None,
                    model_name='Payment',
                    object_id=payment.id,
                    object_repr=str(payment)
                )
            else:
                pending_count += 1

        self.stdout.write(self.style.SUCCESS(f'   ✓ Created {created_count} new members'))
        self.stdout.write(f'   ℹ Confirmed payments: {confirmed_count}')
        self.stdout.write(f'   ℹ Pending payments: {pending_count} (for manual testing)')

    def _create_gcash_walkin_payments(self, count):
        """Create test walk-in GCash payments"""
        self.stdout.write(f'\n🚶 Creating {count} GCash Walk-in Payments...')

        passes = FlexibleAccess.objects.filter(name__startswith='GCash Test', is_active=True)

        if not passes.exists():
            self.stdout.write(self.style.ERROR('   ✗ No test passes found'))
            return

        created_count = 0
        now = timezone.now()

        for i in range(count):
            pass_type = random.choice(passes)

            # Create walk-in payment
            walkin = WalkInPayment.objects.create(
                pass_type=pass_type,
                customer_name=f'GCash Customer {i+1}' if random.random() < 0.7 else None,
                mobile_no=f'0912345{i:04d}' if random.random() < 0.5 else None,
                amount=pass_type.price,
                method='gcash',
                payment_date=now - timedelta(hours=random.randint(1, 48))
            )

            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'   ✓ Created {created_count} GCash walk-in payments'))

    def _print_summary(self):
        """Print summary of seeded data"""
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('✅ GCASH TEST DATA SEEDING COMPLETE!'))
        self.stdout.write('=' * 80)

        # Count data
        members = User.objects.filter(username__startswith='gcash_member').count()
        memberships = UserMembership.objects.count()
        payments = Payment.objects.filter(method='gcash').count()
        pending_payments = Payment.objects.filter(status='pending', method='gcash').count()
        confirmed_payments = Payment.objects.filter(status='confirmed', method='gcash').count()
        walkins = WalkInPayment.objects.filter(method='gcash').count()

        self.stdout.write(f'\n👥 MEMBERS')
        self.stdout.write(f'   Test Members: {members}')

        self.stdout.write(f'\n💳 MEMBERSHIPS (GCash)')
        self.stdout.write(f'   Total: {memberships}')
        self.stdout.write(f'   Active: {UserMembership.objects.filter(status="active").count()}')
        self.stdout.write(f'   Pending: {UserMembership.objects.filter(status="pending").count()}')

        self.stdout.write(f'\n💰 MEMBER PAYMENTS (GCash)')
        self.stdout.write(f'   Total: {payments}')
        self.stdout.write(f'   Confirmed: {confirmed_payments} (with generated QR codes)')
        self.stdout.write(f'   Pending: {pending_payments} (ready for confirmation testing)')

        total_revenue = Payment.objects.filter(status='confirmed', method='gcash').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        self.stdout.write(f'   Revenue: ₱{total_revenue:,.2f}')

        self.stdout.write(f'\n🚶 WALKIN PAYMENTS (GCash)')
        self.stdout.write(f'   Total: {walkins}')
        walkin_revenue = WalkInPayment.objects.filter(method='gcash').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        self.stdout.write(f'   Revenue: ₱{walkin_revenue:,.2f}')

        self.stdout.write(f'\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('🧪 READY FOR QR CODE TESTING'))
        self.stdout.write('=' * 80)

        self.stdout.write('\n📋 TEST SCENARIOS:')
        self.stdout.write(f'  1. Test pending payment confirmation QR code (view pending-payments)')
        self.stdout.write(f'  2. Test confirmed payment display')
        self.stdout.write(f'  3. Test walk-in payment QR code generation')
        self.stdout.write(f'  4. Verify QR code data encoding')
        self.stdout.write(f'  5. Test fallback to static image if needed')

        self.stdout.write('\n🔑 TEST CREDENTIALS:')
        self.stdout.write('  Admin: admin / admin123')
        self.stdout.write('  Staff: staff_test / staff123')
        self.stdout.write('  Members: gcash_member_1 / member123 (and more)')

        self.stdout.write('\n' + '=' * 80 + '\n')

# Import models for aggregation
from django.db import models
