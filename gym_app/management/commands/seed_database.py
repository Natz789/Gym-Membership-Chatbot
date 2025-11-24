"""
Comprehensive Database Seeder for Gym Management System

This seeder creates realistic test data for all models:
- Users (admin, staff, members)
- Membership Plans & Flexible Access
- User Memberships
- Payments (member & walk-in)
- Attendance Records
- Analytics
- Audit Logs

Usage:
    python manage.py seed_database
    python manage.py seed_database --users 50 --days 90
    python manage.py seed_database --flush  # Clear and reseed
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from gym_app.models import (
    User, MembershipPlan, FlexibleAccess, UserMembership,
    Payment, WalkInPayment, Analytics, AuditLog, Attendance
)
from decimal import Decimal
from datetime import datetime, timedelta, date
import random


class Command(BaseCommand):
    help = 'Create comprehensive test data for the gym management system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=100,
            help='Number of member users to create (default: 100)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of historical data to generate (default: 90)'
        )
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing data before seeding'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        num_days = options['days']
        flush = options['flush']

        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🏋️  GYM MANAGEMENT SYSTEM - COMPREHENSIVE DATABASE SEEDER'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        if flush:
            self.flush_database()

        # Seed data in order
        self.create_admin_staff()
        self.create_membership_plans()
        self.create_flexible_access()
        self.create_members(num_users)
        self.create_memberships(num_days)
        self.create_payments()
        self.create_walk_in_payments(num_days)
        self.create_attendance_records(num_days)
        self.create_analytics(num_days)
        self.create_audit_logs()

        self.print_summary()

    def flush_database(self):
        """Delete all existing data"""
        self.stdout.write(self.style.WARNING('\n🗑️  Flushing existing data...\n'))

        models_to_flush = [
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

        # Delete users except superusers
        user_count = User.objects.filter(is_superuser=False).count()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(f'   ✓ Deleted {user_count} users (kept superusers)')

        # Delete plans and passes
        MembershipPlan.objects.all().delete()
        FlexibleAccess.objects.all().delete()
        self.stdout.write(f'   ✓ Deleted all plans and passes\n')

    def create_admin_staff(self):
        """Create admin and staff users"""
        self.stdout.write(self.style.SUCCESS('👥 Creating Admin & Staff Users...\n'))

        admin_data = [
            {
                'username': 'admin',
                'email': 'admin@gym.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'manager',
                'email': 'manager@gym.com',
                'first_name': 'John',
                'last_name': 'Manager',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': False,
            },
            {
                'username': 'director',
                'email': 'director@gym.com',
                'first_name': 'Patricia',
                'last_name': 'Director',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': False,
            }
        ]

        staff_data = [
            {'username': 'staff1', 'email': 'sarah.johnson@gym.com', 'first_name': 'Sarah', 'last_name': 'Johnson', 'role': 'staff', 'mobile_no': '09171234567'},
            {'username': 'staff2', 'email': 'mike.williams@gym.com', 'first_name': 'Mike', 'last_name': 'Williams', 'role': 'staff', 'mobile_no': '09181234567'},
            {'username': 'staff3', 'email': 'lisa.martinez@gym.com', 'first_name': 'Lisa', 'last_name': 'Martinez', 'role': 'staff', 'mobile_no': '09191234567'},
            {'username': 'staff4', 'email': 'david.garcia@gym.com', 'first_name': 'David', 'last_name': 'Garcia', 'role': 'staff', 'mobile_no': '09201234567'},
            {'username': 'staff5', 'email': 'emma.rodriguez@gym.com', 'first_name': 'Emma', 'last_name': 'Rodriguez', 'role': 'staff', 'mobile_no': '09211234567'},
            {'username': 'staff6', 'email': 'james.lopez@gym.com', 'first_name': 'James', 'last_name': 'Lopez', 'role': 'staff', 'mobile_no': '09221234567'},
            {'username': 'staff7', 'email': 'sophia.hernandez@gym.com', 'first_name': 'Sophia', 'last_name': 'Hernandez', 'role': 'staff', 'mobile_no': '09231234567'},
            {'username': 'staff8', 'email': 'robert.gonzalez@gym.com', 'first_name': 'Robert', 'last_name': 'Gonzalez', 'role': 'staff', 'mobile_no': '09241234567'},
            {'username': 'staff9', 'email': 'olivia.perez@gym.com', 'first_name': 'Olivia', 'last_name': 'Perez', 'role': 'staff', 'mobile_no': '09251234567'},
            {'username': 'staff10', 'email': 'william.sanchez@gym.com', 'first_name': 'William', 'last_name': 'Sanchez', 'role': 'staff', 'mobile_no': '09261234567'},
            {'username': 'staff11', 'email': 'ava.ramirez@gym.com', 'first_name': 'Ava', 'last_name': 'Ramirez', 'role': 'staff', 'mobile_no': '09271234567'},
            {'username': 'staff12', 'email': 'alexander.torres@gym.com', 'first_name': 'Alexander', 'last_name': 'Torres', 'role': 'staff', 'mobile_no': '09281234567'},
            {'username': 'staff13', 'email': 'isabella.flores@gym.com', 'first_name': 'Isabella', 'last_name': 'Flores', 'role': 'staff', 'mobile_no': '09291234567'},
            {'username': 'staff14', 'email': 'daniel.rivera@gym.com', 'first_name': 'Daniel', 'last_name': 'Rivera', 'role': 'staff', 'mobile_no': '09301234567'},
            {'username': 'staff15', 'email': 'mia.cruz@gym.com', 'first_name': 'Mia', 'last_name': 'Cruz', 'role': 'staff', 'mobile_no': '09311234567'},
        ]

        for data in admin_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    **data,
                    'password': make_password('admin123'),  # Default password
                    'birthdate': date(1985, 5, 15),
                }
            )
            if created:
                self.stdout.write(f'   ✓ Created admin: {user.username} ({user.email})')
            else:
                self.stdout.write(f'   ⚠ Admin exists: {user.username}')

        for data in staff_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    **data,
                    'password': make_password('staff123'),  # Default password
                    'is_staff': True,
                    'birthdate': date(1990, random.randint(1, 12), random.randint(1, 28)),
                    'address': f'{random.randint(1, 999)} Main Street, Quezon City',
                }
            )
            if created:
                self.stdout.write(f'   ✓ Created staff: {user.username} ({user.email})')
            else:
                self.stdout.write(f'   ⚠ Staff exists: {user.username}')

        self.stdout.write('')

    def create_membership_plans(self):
        """Create membership plans"""
        self.stdout.write(self.style.SUCCESS('💳 Creating Membership Plans...\n'))

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
                self.stdout.write(f'   ✓ Created plan: {plan.name} (₱{plan.price})')
            else:
                self.stdout.write(f'   ⚠ Plan exists: {plan.name}')

        self.stdout.write('')

    def create_flexible_access(self):
        """Create walk-in passes"""
        self.stdout.write(self.style.SUCCESS('🎫 Creating Walk-in Passes...\n'))

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
                self.stdout.write(f'   ✓ Created pass: {pass_obj.name} (₱{pass_obj.price})')
            else:
                self.stdout.write(f'   ⚠ Pass exists: {pass_obj.name}')

        self.stdout.write('')

    def create_members(self, count):
        """Create member users with realistic data"""
        self.stdout.write(self.style.SUCCESS(f'👤 Creating {count} Member Users...\n'))

        # Filipino-inspired names
        first_names = [
            'Juan', 'Maria', 'Jose', 'Ana', 'Carlos', 'Sofia', 'Miguel', 'Isabel',
            'Roberto', 'Carmen', 'Pedro', 'Rosa', 'Luis', 'Elena', 'Diego', 'Lucia',
            'Fernando', 'Patricia', 'Ricardo', 'Teresa', 'Antonio', 'Angelina',
            'Ramon', 'Gloria', 'Enrique', 'Victoria', 'Rafael', 'Beatriz',
            'Mark', 'Angel', 'Christian', 'Faith', 'Joshua', 'Grace', 'Daniel', 'Hope'
        ]

        last_names = [
            'Santos', 'Reyes', 'Cruz', 'Bautista', 'Garcia', 'Mendoza', 'Torres',
            'Flores', 'Rivera', 'Gomez', 'Ramos', 'Castillo', 'Alvarez', 'Diaz',
            'Morales', 'Aquino', 'Dela Cruz', 'Gonzales', 'Lopez', 'Fernandez',
            'Martinez', 'Perez', 'Villanueva', 'Santiago', 'Navarro', 'Hernandez'
        ]

        cities = [
            'Quezon City', 'Manila', 'Makati', 'Pasig', 'Taguig', 'Mandaluyong',
            'Pasay', 'Caloocan', 'Las Piñas', 'Parañaque', 'Muntinlupa'
        ]

        created_count = 0
        for i in range(count):
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
                    'address': f'{random.randint(1, 999)} {random.choice(["Main", "Market", "Central", "Rizal", "Bonifacio"])} Street, {random.choice(cities)}',
                    'birthdate': birthdate,
                }
            )

            if created:
                # Generate kiosk PIN for members
                user.generate_kiosk_pin()
                created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} new members\n')

    def create_memberships(self, days_back):
        """Create user memberships with various statuses"""
        self.stdout.write(self.style.SUCCESS('📋 Creating User Memberships...\n'))

        members = User.objects.filter(role='member')
        plans = list(MembershipPlan.objects.all())

        if not plans:
            self.stdout.write(self.style.ERROR('   ✗ No membership plans found!\n'))
            return

        created_count = 0
        for member in members:
            # 80% of members have at least one membership
            if random.random() < 0.8:
                # Number of memberships (1-3)
                num_memberships = random.choices([1, 2, 3], weights=[60, 30, 10])[0]

                for i in range(num_memberships):
                    plan = random.choice(plans)

                    # Calculate start date (within the last days_back days)
                    days_ago = random.randint(0, days_back)
                    start_date = date.today() - timedelta(days=days_ago)
                    end_date = start_date + timedelta(days=plan.duration_days)

                    # Determine status
                    if end_date < date.today():
                        status = 'expired'
                    elif random.random() < 0.05:  # 5% cancelled
                        status = 'cancelled'
                    else:
                        status = 'active'

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

        self.stdout.write(f'   ✓ Created {created_count} memberships\n')
        self.stdout.write(f'   ℹ Active: {UserMembership.objects.filter(status="active").count()}')
        self.stdout.write(f'   ℹ Expired: {UserMembership.objects.filter(status="expired").count()}')
        self.stdout.write(f'   ℹ Cancelled: {UserMembership.objects.filter(status="cancelled").count()}\n')

    def create_payments(self):
        """Create payment records for memberships with varied statuses"""
        self.stdout.write(self.style.SUCCESS('💰 Creating Payment Records...\n'))

        memberships = UserMembership.objects.all()
        payment_methods = ['cash', 'gcash']
        staff_users = list(User.objects.filter(role__in=['admin', 'staff']))

        created_count = 0
        pending_count = 0
        confirmed_count = 0
        rejected_count = 0

        for membership in memberships:
            # Only create payments for non-cancelled memberships
            if membership.status != 'cancelled':
                # Determine payment status (70% confirmed, 20% pending, 10% rejected)
                status_choice = random.choices(
                    ['confirmed', 'pending', 'rejected'],
                    weights=[70, 20, 10]
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
                            None, None  # More likely to have no notes
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
                            'Requested by customer'
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

    def create_walk_in_payments(self, days_back):
        """Create walk-in payment records"""
        self.stdout.write(self.style.SUCCESS('🚶 Creating Walk-in Payments...\n'))

        passes = list(FlexibleAccess.objects.all())
        if not passes:
            self.stdout.write(self.style.ERROR('   ✗ No flexible access passes found!\n'))
            return

        staff_users = list(User.objects.filter(role__in=['admin', 'staff']))
        payment_methods = ['cash', 'gcash']

        # Generate 2-8 walk-in payments per day
        created_count = 0
        for days_ago in range(days_back):
            payment_date = date.today() - timedelta(days=days_ago)
            num_payments = random.randint(2, 8)

            for _ in range(num_payments):
                pass_type = random.choice(passes)

                # 60% provide name, 40% anonymous
                if random.random() < 0.6:
                    customer_name = f'{random.choice(["John", "Jane", "Mark", "Sarah", "Mike", "Lisa", "Alex", "Chris", "Taylor", "Jordan"])} {random.choice(["Doe", "Smith", "Johnson", "Williams", "Brown", "Davis", "Wilson"])}'
                    mobile_no = f'09{random.randint(100000000, 999999999)}'
                else:
                    customer_name = None
                    mobile_no = None

                payment_datetime = timezone.make_aware(
                    datetime.combine(
                        payment_date,
                        datetime.min.time().replace(
                            hour=random.randint(6, 20),
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
                )
                created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} walk-in payments\n')

    def create_attendance_records(self, days_back):
        """Create attendance/check-in records"""
        self.stdout.write(self.style.SUCCESS('📊 Creating Attendance Records...\n'))

        # Get members with active memberships
        active_members = User.objects.filter(
            role='member',
            memberships__status='active',
            memberships__end_date__gte=date.today()
        ).distinct()

        created_count = 0
        for days_ago in range(days_back):
            check_date = date.today() - timedelta(days=days_ago)

            # Each active member has 40-70% chance of attending each day
            for member in active_members:
                if random.random() < random.uniform(0.4, 0.7):
                    # Random check-in time (6 AM - 9 PM)
                    check_in_hour = random.randint(6, 21)
                    check_in_minute = random.randint(0, 59)
                    check_in = timezone.make_aware(
                        datetime.combine(
                            check_date,
                            datetime.min.time().replace(hour=check_in_hour, minute=check_in_minute)
                        )
                    )

                    # 90% have checked out, 10% still in progress
                    if random.random() < 0.9:
                        # Workout duration: 30 minutes to 3 hours
                        duration_minutes = random.randint(30, 180)
                        check_out = check_in + timedelta(minutes=duration_minutes)
                    else:
                        check_out = None
                        duration_minutes = None

                    Attendance.objects.create(
                        user=member,
                        check_in=check_in,
                        check_out=check_out,
                        duration_minutes=duration_minutes,
                    )
                    created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} attendance records\n')

    def create_analytics(self, days_back):
        """Generate analytics data"""
        self.stdout.write(self.style.SUCCESS('📈 Generating Analytics Data...\n'))

        created_count = 0
        for days_ago in range(days_back):
            target_date = date.today() - timedelta(days=days_ago)
            analytics = Analytics.generate_daily_report(target_date)
            created_count += 1

        self.stdout.write(f'   ✓ Generated {created_count} analytics records\n')

    def create_audit_logs(self):
        """Create sample audit logs"""
        self.stdout.write(self.style.SUCCESS('📝 Creating Audit Logs...\n'))

        users = list(User.objects.all())
        actions = [
            ('login', 'info', 'User logged in successfully'),
            ('logout', 'info', 'User logged out'),
            ('user_created', 'info', 'New user account created'),
            ('membership_created', 'info', 'New membership subscription created'),
            ('payment_received', 'info', 'Payment processed successfully'),
            ('walkin_sale', 'info', 'Walk-in pass sold'),
        ]

        created_count = 0
        for _ in range(200):  # Create 200 audit logs
            user = random.choice(users)
            action, severity, description = random.choice(actions)

            days_ago = random.randint(0, 60)
            timestamp = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))

            log = AuditLog.objects.create(
                user=user,
                action=action,
                severity=severity,
                description=f'{description} for {user.get_full_name()}',
                ip_address=f'192.168.1.{random.randint(1, 255)}',
            )
            # Manually set timestamp (since auto_now_add is True)
            log.timestamp = timestamp
            log.save(update_fields=['timestamp'])
            created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} audit log entries\n')

    def print_summary(self):
        """Print summary of seeded data"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('✅ DATABASE SEEDING COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        summary_data = [
            ('👥 Total Users', User.objects.count()),
            ('   ├─ Admins', User.objects.filter(role='admin').count()),
            ('   ├─ Staff', User.objects.filter(role='staff').count()),
            ('   └─ Members', User.objects.filter(role='member').count()),
            ('', ''),
            ('💳 Membership Plans', MembershipPlan.objects.count()),
            ('🎫 Walk-in Passes', FlexibleAccess.objects.count()),
            ('', ''),
            ('📋 User Memberships', UserMembership.objects.count()),
            ('   ├─ Active', UserMembership.objects.filter(status='active').count()),
            ('   ├─ Expired', UserMembership.objects.filter(status='expired').count()),
            ('   └─ Cancelled', UserMembership.objects.filter(status='cancelled').count()),
            ('', ''),
            ('💰 Member Payments', Payment.objects.count()),
            ('   ├─ Confirmed', Payment.objects.filter(status='confirmed').count()),
            ('   ├─ Pending', Payment.objects.filter(status='pending').count()),
            ('   └─ Rejected', Payment.objects.filter(status='rejected').count()),
            ('', ''),
            ('🚶 Walk-in Payments', WalkInPayment.objects.count()),
            ('📊 Attendance Records', Attendance.objects.count()),
            ('📈 Analytics Records', Analytics.objects.count()),
            ('📝 Audit Logs', AuditLog.objects.count()),
        ]

        for label, value in summary_data:
            if label == '':
                self.stdout.write('')
            else:
                self.stdout.write(f'{label:<30} {value}')

        # Calculate total revenue
        member_revenue = Payment.objects.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        walkin_revenue = WalkInPayment.objects.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        total_revenue = member_revenue + walkin_revenue

        self.stdout.write(self.style.SUCCESS(f'\n💵 Total Revenue Generated: ₱{total_revenue:,.2f}'))
        self.stdout.write(f'   ├─ Member Payments: ₱{member_revenue:,.2f}')
        self.stdout.write(f'   └─ Walk-in Payments: ₱{walkin_revenue:,.2f}')

        self.stdout.write(self.style.SUCCESS('\n' + '-'*70))
        self.stdout.write(self.style.SUCCESS('💡 DEFAULT CREDENTIALS:'))
        self.stdout.write(self.style.SUCCESS('-'*70))
        self.stdout.write('Admin:  username=admin, password=admin123')
        self.stdout.write('Staff:  username=staff1, password=staff123')
        self.stdout.write('Member: username=<any member>, password=member123')
        self.stdout.write(self.style.SUCCESS('-'*70 + '\n'))


# Import models for revenue calculation
from django.db import models