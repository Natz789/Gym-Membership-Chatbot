"""
Comprehensive Database Seeder for Gym Management System
Demonstrates ALL features with realistic test data:
- 50 Members, 5 Staff, 3 Admins
- All models populated
- All system functions demonstrated

Usage:
    python manage.py comprehensive_seeder
    python manage.py comprehensive_seeder --flush  # Clear and reseed
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from gym_app.models import (
    User, MembershipPlan, FlexibleAccess, UserMembership,
    Payment, WalkInPayment, Analytics, AuditLog, Attendance,
    LoginActivity, Conversation, ConversationMessage
)
from decimal import Decimal
from datetime import datetime, timedelta, date
import random
import uuid


class Command(BaseCommand):
    help = 'Create comprehensive test data demonstrating ALL gym system features'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing data before seeding'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of historical data to generate (default: 90)'
        )

    def handle(self, *args, **options):
        flush = options['flush']
        self.num_days = options['days']

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🏋️  COMPREHENSIVE GYM SYSTEM SEEDER'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('📊 Configuration: 50 Members | 5 Staff | 3 Admins'))
        self.stdout.write(self.style.SUCCESS('🎯 Demonstrating ALL system features'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        if flush:
            self.flush_database()

        # Seed all data
        self.create_admin_users()
        self.create_staff_users()
        self.create_membership_plans()
        self.create_flexible_access()
        self.create_member_users()
        self.create_memberships()
        self.create_payments()
        self.create_walk_in_payments()
        self.create_attendance_records()
        self.create_login_activity()
        self.create_conversations()
        self.create_analytics()
        self.create_comprehensive_audit_logs()

        self.print_summary()

    def flush_database(self):
        """Delete all existing data"""
        self.stdout.write(self.style.WARNING('\n🗑️  Flushing existing data...\n'))

        models_to_flush = [
            (ConversationMessage, 'Conversation messages'),
            (Conversation, 'Conversations'),
            (LoginActivity, 'Login activities'),
            (Attendance, 'Attendance records'),
            (Analytics, 'Analytics'),
            (AuditLog, 'Audit logs'),
            (WalkInPayment, 'Walk-in payments'),
            (Payment, 'Payments'),
            (UserMembership, 'User memberships'),
        ]

        for model, name in models_to_flush:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(f'   ✓ Deleted {count} {name}')

        # Delete users except superusers created outside seeder
        user_count = User.objects.filter(is_superuser=False).count()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(f'   ✓ Deleted {user_count} users (kept external superusers)')

        # Delete plans and passes
        MembershipPlan.objects.all().delete()
        FlexibleAccess.objects.all().delete()
        self.stdout.write(f'   ✓ Deleted all plans and passes\n')

    def create_admin_users(self):
        """Create 3 admin users"""
        self.stdout.write(self.style.SUCCESS('👑 Creating 3 Admin Users...\n'))

        admin_data = [
            {
                'username': 'admin',
                'email': 'admin@gym.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'mobile_no': '09171234567',
                'address': '123 Admin Tower, Makati City',
                'is_superuser': True,
            },
            {
                'username': 'manager',
                'email': 'manager@gym.com',
                'first_name': 'John',
                'last_name': 'Manager',
                'mobile_no': '09181234567',
                'address': '456 Management Ave, BGC, Taguig',
                'is_superuser': False,
            },
            {
                'username': 'director',
                'email': 'director@gym.com',
                'first_name': 'Patricia',
                'last_name': 'Director',
                'mobile_no': '09191234567',
                'address': '789 Executive Plaza, Ortigas, Pasig',
                'is_superuser': False,
            }
        ]

        for data in admin_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    **data,
                    'password': make_password('admin123'),
                    'role': 'admin',
                    'is_staff': True,
                    'birthdate': date(1985, random.randint(1, 12), random.randint(1, 28)),
                }
            )
            if created:
                self.stdout.write(f'   ✓ Created admin: {user.username} ({user.email})')
            else:
                self.stdout.write(f'   ⚠ Admin exists: {user.username}')

        self.stdout.write('')

    def create_staff_users(self):
        """Create 5 staff users"""
        self.stdout.write(self.style.SUCCESS('👥 Creating 5 Staff Users...\n'))

        staff_data = [
            {
                'username': 'staff1',
                'email': 'sarah.johnson@gym.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'mobile_no': '09201234567'
            },
            {
                'username': 'staff2',
                'email': 'mike.williams@gym.com',
                'first_name': 'Mike',
                'last_name': 'Williams',
                'mobile_no': '09211234567'
            },
            {
                'username': 'staff3',
                'email': 'lisa.martinez@gym.com',
                'first_name': 'Lisa',
                'last_name': 'Martinez',
                'mobile_no': '09221234567'
            },
            {
                'username': 'staff4',
                'email': 'david.garcia@gym.com',
                'first_name': 'David',
                'last_name': 'Garcia',
                'mobile_no': '09231234567'
            },
            {
                'username': 'staff5',
                'email': 'emma.rodriguez@gym.com',
                'first_name': 'Emma',
                'last_name': 'Rodriguez',
                'mobile_no': '09241234567'
            },
        ]

        cities = ['Quezon City', 'Manila', 'Makati', 'Pasig', 'Taguig']

        for data in staff_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    **data,
                    'password': make_password('staff123'),
                    'role': 'staff',
                    'is_staff': True,
                    'birthdate': date(1990, random.randint(1, 12), random.randint(1, 28)),
                    'address': f'{random.randint(1, 999)} Main Street, {random.choice(cities)}',
                }
            )
            if created:
                self.stdout.write(f'   ✓ Created staff: {user.username} ({user.email})')
            else:
                self.stdout.write(f'   ⚠ Staff exists: {user.username}')

        self.stdout.write('')

    def create_membership_plans(self):
        """Create membership plans including archived ones"""
        self.stdout.write(self.style.SUCCESS('💳 Creating Membership Plans...\n'))

        plans_data = [
            {
                'name': 'Weekly Pass',
                'duration_days': 7,
                'price': Decimal('500.00'),
                'description': 'Perfect for trying out the gym. 7 days of full access to all facilities.',
                'is_active': True,
                'is_archived': False
            },
            {
                'name': 'Monthly Membership',
                'duration_days': 30,
                'price': Decimal('1500.00'),
                'description': '30 days of unlimited gym access. Most popular choice!',
                'is_active': True,
                'is_archived': False
            },
            {
                'name': 'Quarterly Membership',
                'duration_days': 90,
                'price': Decimal('4000.00'),
                'description': '3 months of commitment for serious fitness goals. Save ₱500!',
                'is_active': True,
                'is_archived': False
            },
            {
                'name': 'Semi-Annual Premium',
                'duration_days': 180,
                'price': Decimal('7500.00'),
                'description': '6 months of premium gym access. Best value with ₱1500 savings!',
                'is_active': True,
                'is_archived': False
            },
            {
                'name': 'Annual VIP Membership',
                'duration_days': 365,
                'price': Decimal('14000.00'),
                'description': 'Full year of VIP access. Ultimate savings of ₱4000!',
                'is_active': True,
                'is_archived': False
            },
            # Archived plans (discontinued but in records)
            {
                'name': 'Student Special',
                'duration_days': 30,
                'price': Decimal('1000.00'),
                'description': 'Discontinued student discount plan.',
                'is_active': False,
                'is_archived': True
            },
            {
                'name': 'Senior Citizen Plan',
                'duration_days': 30,
                'price': Decimal('1200.00'),
                'description': 'Legacy senior citizen plan (replaced by new pricing).',
                'is_active': False,
                'is_archived': True
            },
        ]

        admin_user = User.objects.filter(role='admin').first()

        for plan_data in plans_data:
            plan, created = MembershipPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created and plan_data['is_archived']:
                plan.archived_by = admin_user
                plan.archived_at = timezone.now() - timedelta(days=random.randint(30, 90))
                plan.save()
                self.stdout.write(f'   ✓ Created archived plan: {plan.name}')
            elif created:
                self.stdout.write(f'   ✓ Created plan: {plan.name} (₱{plan.price})')
            else:
                self.stdout.write(f'   ⚠ Plan exists: {plan.name}')

        self.stdout.write('')

    def create_flexible_access(self):
        """Create walk-in passes including archived ones"""
        self.stdout.write(self.style.SUCCESS('🎫 Creating Walk-in Passes...\n'))

        passes_data = [
            {
                'name': 'Single Day Pass',
                'duration_days': 1,
                'price': Decimal('100.00'),
                'description': 'One-time gym access for a single day. Try before you buy!',
                'is_active': True,
                'is_archived': False
            },
            {
                'name': '3-Day Trial Pass',
                'duration_days': 3,
                'price': Decimal('250.00'),
                'description': '3 consecutive days of gym access. Perfect for visitors!',
                'is_active': True,
                'is_archived': False
            },
            {
                'name': '5-Day Flex Pass',
                'duration_days': 5,
                'price': Decimal('400.00'),
                'description': '5 days of flexible gym access within a week.',
                'is_active': True,
                'is_archived': False
            },
            # Archived pass
            {
                'name': 'Weekend Warrior',
                'duration_days': 2,
                'price': Decimal('150.00'),
                'description': 'Discontinued weekend-only pass.',
                'is_active': False,
                'is_archived': True
            },
        ]

        admin_user = User.objects.filter(role='admin').first()

        for pass_data in passes_data:
            pass_obj, created = FlexibleAccess.objects.get_or_create(
                name=pass_data['name'],
                defaults=pass_data
            )
            if created and pass_data['is_archived']:
                pass_obj.archived_by = admin_user
                pass_obj.archived_at = timezone.now() - timedelta(days=random.randint(60, 120))
                pass_obj.save()
                self.stdout.write(f'   ✓ Created archived pass: {pass_obj.name}')
            elif created:
                self.stdout.write(f'   ✓ Created pass: {pass_obj.name} (₱{pass_obj.price})')
            else:
                self.stdout.write(f'   ⚠ Pass exists: {pass_obj.name}')

        self.stdout.write('')

    def create_member_users(self):
        """Create 50 member users with realistic Filipino data"""
        self.stdout.write(self.style.SUCCESS('👤 Creating 50 Member Users...\n'))

        # Filipino-inspired names
        first_names = [
            'Juan', 'Maria', 'Jose', 'Ana', 'Carlos', 'Sofia', 'Miguel', 'Isabel',
            'Roberto', 'Carmen', 'Pedro', 'Rosa', 'Luis', 'Elena', 'Diego', 'Lucia',
            'Fernando', 'Patricia', 'Ricardo', 'Teresa', 'Antonio', 'Angelina',
            'Ramon', 'Gloria', 'Enrique', 'Victoria', 'Rafael', 'Beatriz',
            'Mark', 'Angel', 'Christian', 'Faith', 'Joshua', 'Grace', 'Daniel', 'Hope',
            'Gabriel', 'Mary', 'Joseph', 'Catherine', 'David', 'Elizabeth', 'Samuel', 'Anne'
        ]

        last_names = [
            'Santos', 'Reyes', 'Cruz', 'Bautista', 'Garcia', 'Mendoza', 'Torres',
            'Flores', 'Rivera', 'Gomez', 'Ramos', 'Castillo', 'Alvarez', 'Diaz',
            'Morales', 'Aquino', 'Dela Cruz', 'Gonzales', 'Lopez', 'Fernandez',
            'Martinez', 'Perez', 'Villanueva', 'Santiago', 'Navarro', 'Hernandez'
        ]

        cities = [
            'Quezon City', 'Manila', 'Makati', 'Pasig', 'Taguig', 'Mandaluyong',
            'Pasay', 'Caloocan', 'Las Piñas', 'Parañaque', 'Muntinlupa', 'Marikina'
        ]

        streets = ['Main', 'Market', 'Central', 'Rizal', 'Bonifacio', 'Aguinaldo', 'Luna', 'Mabini']

        created_count = 0
        for i in range(50):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f'{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}'
            email = f'{username}@gmail.com'

            # Generate realistic birthdate (18-65 years old)
            years_ago = random.randint(18, 65)
            birthdate = date.today() - timedelta(days=years_ago*365 + random.randint(0, 365))

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'password': make_password('member123'),
                    'role': 'member',
                    'mobile_no': f'09{random.randint(100000000, 999999999)}',
                    'address': f'{random.randint(1, 999)} {random.choice(streets)} Street, {random.choice(cities)}',
                    'birthdate': birthdate,
                }
            )

            if created:
                # Generate kiosk PIN for members
                user.generate_kiosk_pin()
                created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} new members with kiosk PINs\n')

    def create_memberships(self):
        """Create user memberships with diverse statuses"""
        self.stdout.write(self.style.SUCCESS('📋 Creating User Memberships...\n'))

        members = User.objects.filter(role='member')
        active_plans = list(MembershipPlan.objects.filter(is_active=True, is_archived=False))
        archived_plans = list(MembershipPlan.objects.filter(is_archived=True))

        if not active_plans:
            self.stdout.write(self.style.ERROR('   ✗ No active membership plans found!\n'))
            return

        created_count = 0
        active_count = 0
        expired_count = 0
        cancelled_count = 0
        pending_count = 0

        for member in members:
            # 85% of members have at least one membership
            if random.random() < 0.85:
                # Number of memberships (1-3, weighted)
                num_memberships = random.choices([1, 2, 3], weights=[70, 25, 5])[0]

                for i in range(num_memberships):
                    # 95% use active plans, 5% have old archived plans
                    if random.random() < 0.95:
                        plan = random.choice(active_plans)
                    else:
                        plan = random.choice(archived_plans) if archived_plans else random.choice(active_plans)

                    # Calculate start date
                    days_ago = random.randint(0, self.num_days)
                    start_date = date.today() - timedelta(days=days_ago)
                    end_date = start_date + timedelta(days=plan.duration_days)

                    # Determine status with realistic distribution
                    if end_date < date.today():
                        status = 'expired'
                        expired_count += 1
                    elif random.random() < 0.08:  # 8% cancelled
                        status = 'cancelled'
                        cancelled_count += 1
                    elif random.random() < 0.05:  # 5% pending payment
                        status = 'pending'
                        pending_count += 1
                    else:
                        status = 'active'
                        active_count += 1

                    membership, created = UserMembership.objects.get_or_create(
                        user=member,
                        plan=plan,
                        start_date=start_date,
                        defaults={
                            'end_date': end_date,
                            'status': status,
                        }
                    )

                    if created:
                        created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} memberships')
        self.stdout.write(f'   ℹ Active: {active_count}')
        self.stdout.write(f'   ℹ Expired: {expired_count}')
        self.stdout.write(f'   ℹ Pending: {pending_count}')
        self.stdout.write(f'   ℹ Cancelled: {cancelled_count}\n')

    def create_payments(self):
        """Create payment records with varied statuses"""
        self.stdout.write(self.style.SUCCESS('💰 Creating Payment Records...\n'))

        memberships = UserMembership.objects.all()
        payment_methods = ['cash', 'gcash']
        staff_users = list(User.objects.filter(role__in=['admin', 'staff']))

        created_count = 0
        pending_count = 0
        confirmed_count = 0
        rejected_count = 0

        for membership in memberships:
            # Create payment for non-cancelled memberships
            if membership.status != 'cancelled':
                # Status distribution: 75% confirmed, 15% pending, 10% rejected
                status_choice = random.choices(
                    ['confirmed', 'pending', 'rejected'],
                    weights=[75, 15, 10]
                )[0]

                payment, created = Payment.objects.get_or_create(
                    user=membership.user,
                    membership=membership,
                    defaults={
                        'amount': membership.plan.price,
                        'method': random.choice(payment_methods),
                        'payment_date': timezone.make_aware(
                            datetime.combine(membership.start_date, datetime.min.time())
                            + timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))
                        ),
                        'status': status_choice,
                        'notes': random.choice([
                            'Payment via GCash',
                            'Cash payment at counter',
                            'Online payment received',
                            'Bank transfer completed',
                            'Payment through app',
                            None, None, None  # More likely to have no notes
                        ])
                    }
                )

                if created:
                    # Update payment based on status
                    if status_choice == 'confirmed' and staff_users:
                        payment.approved_by = random.choice(staff_users)
                        payment.approved_at = payment.payment_date + timedelta(hours=random.randint(1, 24))
                        payment.save()
                        confirmed_count += 1
                    elif status_choice == 'rejected' and staff_users:
                        payment.approved_by = random.choice(staff_users)
                        payment.approved_at = payment.payment_date + timedelta(hours=random.randint(1, 48))
                        payment.rejection_reason = random.choice([
                            'Invalid reference number',
                            'Payment amount mismatch',
                            'Duplicate payment submission',
                            'Insufficient proof of payment',
                            'Requested by customer - refund issued'
                        ])
                        payment.save()
                        rejected_count += 1
                    elif status_choice == 'pending':
                        pending_count += 1

                    created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} payment records')
        self.stdout.write(f'   ℹ Confirmed: {confirmed_count}')
        self.stdout.write(f'   ℹ Pending: {pending_count}')
        self.stdout.write(f'   ℹ Rejected: {rejected_count}\n')

    def create_walk_in_payments(self):
        """Create walk-in payment records"""
        self.stdout.write(self.style.SUCCESS('🚶 Creating Walk-in Payments...\n'))

        passes = list(FlexibleAccess.objects.filter(is_active=True, is_archived=False))
        if not passes:
            self.stdout.write(self.style.ERROR('   ✗ No active flexible access passes found!\n'))
            return

        staff_users = list(User.objects.filter(role__in=['admin', 'staff']))
        payment_methods = ['cash', 'gcash']

        customer_first_names = ['John', 'Jane', 'Mark', 'Sarah', 'Mike', 'Lisa', 'Alex',
                                'Chris', 'Taylor', 'Jordan', 'Sam', 'Pat', 'Casey', 'Drew']
        customer_last_names = ['Doe', 'Smith', 'Johnson', 'Williams', 'Brown', 'Davis',
                               'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson']

        # Generate 3-10 walk-in payments per day
        created_count = 0
        for days_ago in range(self.num_days):
            payment_date = date.today() - timedelta(days=days_ago)
            num_payments = random.randint(3, 10)

            for _ in range(num_payments):
                pass_type = random.choice(passes)

                # 70% provide name, 30% anonymous
                if random.random() < 0.7:
                    customer_name = f'{random.choice(customer_first_names)} {random.choice(customer_last_names)}'
                    mobile_no = f'09{random.randint(100000000, 999999999)}'
                else:
                    customer_name = None
                    mobile_no = None

                payment_datetime = timezone.make_aware(
                    datetime.combine(
                        payment_date,
                        datetime.min.time().replace(
                            hour=random.randint(6, 21),
                            minute=random.randint(0, 59)
                        )
                    )
                )

                WalkInPayment.objects.create(
                    pass_type=pass_type,
                    customer_name=customer_name,
                    mobile_no=mobile_no,
                    amount=pass_type.price,
                    method=random.choice(payment_methods),
                    payment_date=payment_datetime,
                    processed_by=random.choice(staff_users) if staff_users else None,
                    notes=random.choice([
                        None, None, None,  # Most have no notes
                        'First time visitor',
                        'Regular walk-in customer',
                        'Tourist',
                    ])
                )
                created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} walk-in payments\n')

    def create_attendance_records(self):
        """Create attendance/check-in records"""
        self.stdout.write(self.style.SUCCESS('📊 Creating Attendance Records...\n'))

        # Get members with active memberships
        active_members = User.objects.filter(
            role='member',
            memberships__status='active',
            memberships__end_date__gte=date.today()
        ).distinct()

        created_count = 0
        checked_in_count = 0  # Still in gym

        for days_ago in range(self.num_days):
            check_date = date.today() - timedelta(days=days_ago)

            # Each active member has 40-75% chance of attending each day
            for member in active_members:
                if random.random() < random.uniform(0.4, 0.75):
                    # Random check-in time (5 AM - 10 PM)
                    check_in_hour = random.randint(5, 22)
                    check_in_minute = random.randint(0, 59)
                    check_in = timezone.make_aware(
                        datetime.combine(
                            check_date,
                            datetime.min.time().replace(hour=check_in_hour, minute=check_in_minute)
                        )
                    )

                    # 95% have checked out, 5% still in progress (for recent dates)
                    if days_ago == 0 and random.random() < 0.05:
                        # Still checked in
                        check_out = None
                        duration_minutes = None
                        checked_in_count += 1
                    else:
                        # Workout duration: 30 minutes to 3 hours
                        duration_minutes = random.randint(30, 180)
                        check_out = check_in + timedelta(minutes=duration_minutes)

                    Attendance.objects.create(
                        user=member,
                        check_in=check_in,
                        check_out=check_out,
                        duration_minutes=duration_minutes,
                        notes=random.choice([
                            None, None, None, None,  # Most have no notes
                            'Regular workout',
                            'Cardio session',
                            'Weight training',
                            'Group class',
                        ])
                    )
                    created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} attendance records')
        self.stdout.write(f'   ℹ Currently checked in: {checked_in_count}\n')

    def create_login_activity(self):
        """Create login activity records"""
        self.stdout.write(self.style.SUCCESS('🔐 Creating Login Activity Records...\n'))

        all_users = list(User.objects.all())
        created_count = 0
        failed_count = 0

        for days_ago in range(self.num_days):
            login_date = date.today() - timedelta(days=days_ago)

            # Random number of logins per day (5-30)
            num_logins = random.randint(5, 30)

            for _ in range(num_logins):
                user = random.choice(all_users)

                # 95% successful, 5% failed
                success = random.random() < 0.95

                login_time = timezone.make_aware(
                    datetime.combine(
                        login_date,
                        datetime.min.time().replace(
                            hour=random.randint(6, 23),
                            minute=random.randint(0, 59),
                            second=random.randint(0, 59)
                        )
                    )
                )

                failure_reason = None
                if not success:
                    failure_reason = random.choice([
                        'Invalid password',
                        'User does not exist',
                        'Account locked',
                        'Invalid credentials',
                    ])
                    failed_count += 1

                activity = LoginActivity.objects.create(
                    user=user,
                    ip_address=f'{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}',
                    user_agent=random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)',
                    ]),
                    success=success,
                    failure_reason=failure_reason
                )
                # Update timestamp manually
                activity.login_time = login_time
                activity.save(update_fields=['login_time'])
                created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} login activities')
        self.stdout.write(f'   ℹ Successful: {created_count - failed_count}')
        self.stdout.write(f'   ℹ Failed: {failed_count}\n')

    def create_conversations(self):
        """Create chatbot conversations with messages"""
        self.stdout.write(self.style.SUCCESS('💬 Creating Chatbot Conversations...\n'))

        members = list(User.objects.filter(role='member')[:20])  # Use 20 members
        staff = list(User.objects.filter(role='staff'))
        # Hardcoded model (permanently configured to Qwen2.5-0.5B)
        active_model = 'qwen2.5:0.5b'

        conversation_topics = [
            {
                'user_msg': 'What are your gym hours?',
                'bot_msg': 'Our gym is open 24/7! We provide round-the-clock access to all our members. However, our front desk staff are available from 6 AM to 10 PM daily for assistance.'
            },
            {
                'user_msg': 'What membership plans do you offer?',
                'bot_msg': 'We offer several membership plans: Weekly Pass (₱500), Monthly Membership (₱1,500), Quarterly Membership (₱4,000), Semi-Annual Premium (₱7,500), and Annual VIP Membership (₱14,000). Each plan offers full access to all our facilities!'
            },
            {
                'user_msg': 'Do you have personal training?',
                'bot_msg': 'Yes! We offer personalized training sessions with certified trainers. They can help you achieve your fitness goals through customized workout plans. Please contact our front desk to schedule a session.'
            },
            {
                'user_msg': 'What equipment do you have?',
                'bot_msg': 'Our gym is fully equipped with cardio machines (treadmills, ellipticals, bikes), strength training equipment (free weights, machines), and functional training areas. We also have group class studios!'
            },
            {
                'user_msg': 'How do I cancel my membership?',
                'bot_msg': 'To cancel your membership, please contact our staff at the front desk or send an email to support@gym.com. Cancellation policies vary by membership type, and our team will guide you through the process.'
            },
            {
                'user_msg': 'What are your payment methods?',
                'bot_msg': 'We accept both cash and GCash payments for your convenience. You can pay at our front desk or through our online payment system.'
            },
            {
                'user_msg': 'Do you offer group classes?',
                'bot_msg': 'Yes! We offer various group fitness classes including yoga, Zumba, spinning, and HIIT. Check with our front desk for the current class schedule.'
            },
            {
                'user_msg': 'Is there parking available?',
                'bot_msg': 'Yes, we have parking facilities available for our members. The parking area is located adjacent to the gym building.'
            },
        ]

        created_conversations = 0
        created_messages = 0

        # Create conversations for members
        for member in members:
            num_conversations = random.randint(1, 3)

            for _ in range(num_conversations):
                conversation_id = str(uuid.uuid4())
                topic = random.choice(conversation_topics)

                conversation = Conversation.objects.create(
                    user=member,
                    conversation_id=conversation_id,
                    model_used=active_model,
                    session_key=None
                )

                # Create user message
                user_msg = ConversationMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=topic['user_msg'],
                    tokens_used=random.randint(10, 30),
                    response_time_ms=None
                )
                created_messages += 1

                # Create assistant response
                assistant_msg = ConversationMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=topic['bot_msg'],
                    tokens_used=random.randint(50, 150),
                    response_time_ms=random.randint(500, 2000)
                )
                created_messages += 1

                # Generate title from first message
                conversation.generate_title()
                created_conversations += 1

        # Create a few anonymous conversations (session-based)
        for _ in range(5):
            conversation_id = str(uuid.uuid4())
            session_key = str(uuid.uuid4())[:32]
            topic = random.choice(conversation_topics)

            conversation = Conversation.objects.create(
                user=None,
                conversation_id=conversation_id,
                model_used=config.active_model,
                session_key=session_key
            )

            ConversationMessage.objects.create(
                conversation=conversation,
                role='user',
                content=topic['user_msg'],
                tokens_used=random.randint(10, 30)
            )
            created_messages += 1

            ConversationMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=topic['bot_msg'],
                tokens_used=random.randint(50, 150),
                response_time_ms=random.randint(500, 2000)
            )
            created_messages += 1

            conversation.generate_title()
            created_conversations += 1

        self.stdout.write(f'   ✓ Created {created_conversations} conversations')
        self.stdout.write(f'   ✓ Created {created_messages} messages\n')

    def create_analytics(self):
        """Generate analytics data"""
        self.stdout.write(self.style.SUCCESS('📈 Generating Analytics Data...\n'))

        created_count = 0
        for days_ago in range(self.num_days):
            target_date = date.today() - timedelta(days=days_ago)
            analytics = Analytics.generate_daily_report(target_date)
            created_count += 1

        self.stdout.write(f'   ✓ Generated {created_count} analytics records\n')

    def create_comprehensive_audit_logs(self):
        """Create comprehensive audit logs covering all action types"""
        self.stdout.write(self.style.SUCCESS('📝 Creating Comprehensive Audit Logs...\n'))

        users = list(User.objects.all())

        # All possible actions with their typical severity
        audit_actions = [
            # Authentication
            ('login', 'info', 'User logged in successfully'),
            ('logout', 'info', 'User logged out'),
            ('login_failed', 'warning', 'Failed login attempt'),
            ('register', 'info', 'New user registered'),

            # User Management
            ('user_created', 'info', 'User account created'),
            ('user_updated', 'info', 'User profile updated'),
            ('user_deleted', 'warning', 'User account deleted'),
            ('role_changed', 'warning', 'User role changed'),

            # Membership
            ('membership_created', 'info', 'New membership subscription created'),
            ('membership_updated', 'info', 'Membership updated'),
            ('membership_cancelled', 'warning', 'Membership cancelled'),
            ('membership_expired', 'info', 'Membership expired'),

            # Payments
            ('payment_received', 'info', 'Payment received and processed'),
            ('walkin_sale', 'info', 'Walk-in pass sold'),
            ('payment_refunded', 'warning', 'Payment refunded to customer'),

            # Plans
            ('plan_created', 'info', 'New membership plan created'),
            ('plan_updated', 'info', 'Membership plan updated'),
            ('plan_deleted', 'warning', 'Membership plan deleted'),

            # System
            ('data_export', 'info', 'Data exported from system'),
            ('report_generated', 'info', 'Report generated'),
            ('settings_changed', 'warning', 'System settings modified'),

            # Security
            ('unauthorized_access', 'error', 'Unauthorized access attempt detected'),
            ('password_changed', 'warning', 'User password changed'),
            ('permission_denied', 'warning', 'Permission denied for action'),
        ]

        created_count = 0
        for _ in range(500):  # Create 500 diverse audit logs
            user = random.choice(users)
            action, severity, base_description = random.choice(audit_actions)

            days_ago = random.randint(0, self.num_days)
            timestamp = timezone.now() - timedelta(
                days=days_ago,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            # Customize description based on user
            description = f'{base_description} for {user.get_full_name()}'

            log = AuditLog.objects.create(
                user=user,
                action=action,
                severity=severity,
                description=description,
                ip_address=f'{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}',
                user_agent=random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                    'Mozilla/5.0 (X11; Linux x86_64)',
                ]),
            )
            # Manually set timestamp
            log.timestamp = timestamp
            log.save(update_fields=['timestamp'])
            created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} comprehensive audit log entries')

        # Show breakdown by action type
        self.stdout.write('\n   📊 Audit Log Breakdown:')
        for action, _ in AuditLog.ACTION_CHOICES[:10]:  # Show first 10
            count = AuditLog.objects.filter(action=action).count()
            if count > 0:
                self.stdout.write(f'      • {action}: {count}')

        self.stdout.write('')

    def print_summary(self):
        """Print comprehensive summary of seeded data"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('✅ COMPREHENSIVE DATABASE SEEDING COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        from django.db import models

        summary_data = [
            ('👥 USERS', ''),
            ('   ├─ Admins', User.objects.filter(role='admin').count()),
            ('   ├─ Staff', User.objects.filter(role='staff').count()),
            ('   └─ Members', User.objects.filter(role='member').count()),
            ('      └─ With Kiosk PINs', User.objects.filter(role='member', kiosk_pin__isnull=False).count()),
            ('', ''),
            ('💳 MEMBERSHIP PLANS', MembershipPlan.objects.count()),
            ('   ├─ Active Plans', MembershipPlan.objects.filter(is_active=True, is_archived=False).count()),
            ('   └─ Archived Plans', MembershipPlan.objects.filter(is_archived=True).count()),
            ('', ''),
            ('🎫 FLEXIBLE ACCESS PASSES', FlexibleAccess.objects.count()),
            ('   ├─ Active Passes', FlexibleAccess.objects.filter(is_active=True, is_archived=False).count()),
            ('   └─ Archived Passes', FlexibleAccess.objects.filter(is_archived=True).count()),
            ('', ''),
            ('📋 USER MEMBERSHIPS', UserMembership.objects.count()),
            ('   ├─ Active', UserMembership.objects.filter(status='active').count()),
            ('   ├─ Pending', UserMembership.objects.filter(status='pending').count()),
            ('   ├─ Expired', UserMembership.objects.filter(status='expired').count()),
            ('   └─ Cancelled', UserMembership.objects.filter(status='cancelled').count()),
            ('', ''),
            ('💰 MEMBER PAYMENTS', Payment.objects.count()),
            ('   ├─ Confirmed', Payment.objects.filter(status='confirmed').count()),
            ('   ├─ Pending', Payment.objects.filter(status='pending').count()),
            ('   └─ Rejected', Payment.objects.filter(status='rejected').count()),
            ('', ''),
            ('🚶 WALK-IN PAYMENTS', WalkInPayment.objects.count()),
            ('   ├─ Cash', WalkInPayment.objects.filter(method='cash').count()),
            ('   └─ GCash', WalkInPayment.objects.filter(method='gcash').count()),
            ('', ''),
            ('📊 ATTENDANCE RECORDS', Attendance.objects.count()),
            ('   ├─ Completed Sessions', Attendance.objects.filter(check_out__isnull=False).count()),
            ('   └─ Currently Checked In', Attendance.objects.filter(check_out__isnull=True).count()),
            ('', ''),
            ('🔐 LOGIN ACTIVITIES', LoginActivity.objects.count()),
            ('   ├─ Successful', LoginActivity.objects.filter(success=True).count()),
            ('   └─ Failed', LoginActivity.objects.filter(success=False).count()),
            ('', ''),
            ('🤖 CHATBOT', ''),
            ('   ├─ Conversations', Conversation.objects.count()),
            ('   ├─ Messages', ConversationMessage.objects.count()),
            ('   └─ Active Model', 'Qwen 2.5 0.5B (Permanent)'),
            ('', ''),
            ('📈 ANALYTICS RECORDS', Analytics.objects.count()),
            ('📝 AUDIT LOGS', AuditLog.objects.count()),
        ]

        for label, value in summary_data:
            if label == '':
                self.stdout.write('')
            else:
                self.stdout.write(f'{label:<35} {value}')

        # Calculate total revenue
        member_revenue = Payment.objects.filter(status='confirmed').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        walkin_revenue = WalkInPayment.objects.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        total_revenue = member_revenue + walkin_revenue

        self.stdout.write(self.style.SUCCESS(f'\n💵 TOTAL REVENUE GENERATED: ₱{total_revenue:,.2f}'))
        self.stdout.write(f'   ├─ Member Payments (Confirmed): ₱{member_revenue:,.2f}')
        self.stdout.write(f'   └─ Walk-in Payments: ₱{walkin_revenue:,.2f}')

        # Feature demonstration summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🎯 FEATURES DEMONSTRATED'))
        self.stdout.write(self.style.SUCCESS('='*80))

        features = [
            '✓ User Management (Admin, Staff, Member roles)',
            '✓ Role-Based Access Control',
            '✓ Membership Plans (Active & Archived)',
            '✓ Flexible Access Passes (Walk-in)',
            '✓ User Subscriptions (All statuses)',
            '✓ Payment Processing (Pending, Confirmed, Rejected)',
            '✓ Walk-in Sales Management',
            '✓ Attendance Tracking (Check-in/out)',
            '✓ Kiosk System (PIN-based)',
            '✓ Login Activity Monitoring',
            '✓ AI Chatbot Integration',
            '✓ Conversation History',
            '✓ Analytics & Reporting',
            '✓ Comprehensive Audit Trail',
            '✓ Multi-payment Methods (Cash, GCash)',
        ]

        for feature in features:
            self.stdout.write(f'   {feature}')

        self.stdout.write(self.style.SUCCESS('\n' + '-'*80))
        self.stdout.write(self.style.SUCCESS('💡 DEFAULT CREDENTIALS'))
        self.stdout.write(self.style.SUCCESS('-'*80))
        self.stdout.write('🔑 Admin:  username=admin,   password=admin123')
        self.stdout.write('🔑 Staff:  username=staff1,  password=staff123')
        self.stdout.write('🔑 Member: username=<any member>, password=member123')
        self.stdout.write(self.style.SUCCESS('-'*80 + '\n'))
