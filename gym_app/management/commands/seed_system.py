"""
Comprehensive Gym System Seeder
Creates exactly:
- 3 Admins
- 5 Staff
- 30 Members
With complete test data for all system functions

Usage:
    python manage.py seed_system
    python manage.py seed_system --flush  # Clear and reseed
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
    help = 'Create comprehensive test data: 3 admins, 5 staff, 30 members'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing data before seeding'
        )

    def handle(self, *args, **options):
        flush = options['flush']

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🏋️  GYM MANAGEMENT SYSTEM - COMPREHENSIVE SEEDER'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('Creating: 3 Admins | 5 Staff | 30 Members'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        if flush:
            self.flush_database()

        # Track all credentials for the summary
        self.credentials = {
            'admins': [],
            'staff': [],
            'members': []
        }

        # Seed data in order
        self.create_admins()
        self.create_staff()
        self.create_membership_plans()
        self.create_flexible_access()
        self.create_members()
        self.create_memberships()
        self.create_payments()
        self.create_walk_in_payments()
        self.create_attendance_records()
        self.create_analytics()
        self.create_audit_logs()

        self.print_summary()
        self.save_credentials_file()

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

    def create_admins(self):
        """Create exactly 3 admin users"""
        self.stdout.write(self.style.SUCCESS('👔 Creating 3 Admin Users...\n'))

        admins = [
            {
                'username': 'admin',
                'password': 'admin123',
                'email': 'admin@gym.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'mobile_no': '09171111111',
                'address': '123 Admin Tower, Makati City',
                'birthdate': date(1980, 1, 15),
                'is_superuser': True,
                'is_staff': True,
            },
            {
                'username': 'gym_manager',
                'password': 'manager123',
                'email': 'manager@gym.com',
                'first_name': 'Roberto',
                'last_name': 'Santos',
                'mobile_no': '09172222222',
                'address': '456 Business Park, Taguig City',
                'birthdate': date(1985, 6, 20),
                'is_superuser': False,
                'is_staff': True,
            },
            {
                'username': 'director',
                'password': 'director123',
                'email': 'director@gym.com',
                'first_name': 'Patricia',
                'last_name': 'Reyes',
                'mobile_no': '09173333333',
                'address': '789 Executive Village, Quezon City',
                'birthdate': date(1982, 11, 10),
                'is_superuser': False,
                'is_staff': True,
            }
        ]

        for admin_data in admins:
            password = admin_data.pop('password')
            user, created = User.objects.get_or_create(
                username=admin_data['username'],
                defaults={
                    **admin_data,
                    'password': make_password(password),
                    'role': 'admin',
                }
            )
            if created:
                self.credentials['admins'].append({
                    'username': user.username,
                    'password': password,
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}",
                    'mobile': user.mobile_no
                })
                self.stdout.write(f'   ✓ Created admin: {user.username} ({user.email})')
            else:
                self.stdout.write(f'   ⚠ Admin exists: {user.username}')

        self.stdout.write('')

    def create_staff(self):
        """Create exactly 5 staff users"""
        self.stdout.write(self.style.SUCCESS('👨‍💼 Creating 5 Staff Users...\n'))

        staff_list = [
            {
                'username': 'staff_sarah',
                'password': 'staff123',
                'email': 'sarah.johnson@gym.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'mobile_no': '09181234567',
                'address': '111 Maple Street, Pasig City',
                'birthdate': date(1992, 3, 15),
            },
            {
                'username': 'staff_michael',
                'password': 'staff123',
                'email': 'michael.cruz@gym.com',
                'first_name': 'Michael',
                'last_name': 'Cruz',
                'mobile_no': '09182345678',
                'address': '222 Pine Avenue, Mandaluyong City',
                'birthdate': date(1990, 7, 22),
            },
            {
                'username': 'staff_maria',
                'password': 'staff123',
                'email': 'maria.garcia@gym.com',
                'first_name': 'Maria',
                'last_name': 'Garcia',
                'mobile_no': '09183456789',
                'address': '333 Oak Lane, Manila',
                'birthdate': date(1994, 9, 8),
            },
            {
                'username': 'staff_juan',
                'password': 'staff123',
                'email': 'juan.santos@gym.com',
                'first_name': 'Juan',
                'last_name': 'Santos',
                'mobile_no': '09184567890',
                'address': '444 Cedar Road, Quezon City',
                'birthdate': date(1991, 12, 5),
            },
            {
                'username': 'staff_lisa',
                'password': 'staff123',
                'email': 'lisa.martinez@gym.com',
                'first_name': 'Lisa',
                'last_name': 'Martinez',
                'mobile_no': '09185678901',
                'address': '555 Birch Boulevard, Makati City',
                'birthdate': date(1993, 5, 18),
            },
        ]

        for staff_data in staff_list:
            password = staff_data.pop('password')
            user, created = User.objects.get_or_create(
                username=staff_data['username'],
                defaults={
                    **staff_data,
                    'password': make_password(password),
                    'role': 'staff',
                    'is_staff': True,
                }
            )
            if created:
                self.credentials['staff'].append({
                    'username': user.username,
                    'password': password,
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}",
                    'mobile': user.mobile_no
                })
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

        self.stdout.write('')

    def create_members(self):
        """Create exactly 30 member users"""
        self.stdout.write(self.style.SUCCESS('👥 Creating 30 Member Users...\n'))

        # Filipino-inspired names
        member_data = [
            {'first_name': 'Juan', 'last_name': 'Dela Cruz'},
            {'first_name': 'Maria', 'last_name': 'Santos'},
            {'first_name': 'Jose', 'last_name': 'Garcia'},
            {'first_name': 'Ana', 'last_name': 'Reyes'},
            {'first_name': 'Carlos', 'last_name': 'Bautista'},
            {'first_name': 'Sofia', 'last_name': 'Mendoza'},
            {'first_name': 'Miguel', 'last_name': 'Torres'},
            {'first_name': 'Isabel', 'last_name': 'Flores'},
            {'first_name': 'Roberto', 'last_name': 'Rivera'},
            {'first_name': 'Carmen', 'last_name': 'Gomez'},
            {'first_name': 'Pedro', 'last_name': 'Ramos'},
            {'first_name': 'Rosa', 'last_name': 'Castillo'},
            {'first_name': 'Luis', 'last_name': 'Alvarez'},
            {'first_name': 'Elena', 'last_name': 'Diaz'},
            {'first_name': 'Diego', 'last_name': 'Morales'},
            {'first_name': 'Lucia', 'last_name': 'Aquino'},
            {'first_name': 'Fernando', 'last_name': 'Gonzales'},
            {'first_name': 'Patricia', 'last_name': 'Lopez'},
            {'first_name': 'Ricardo', 'last_name': 'Fernandez'},
            {'first_name': 'Teresa', 'last_name': 'Martinez'},
            {'first_name': 'Antonio', 'last_name': 'Perez'},
            {'first_name': 'Angelina', 'last_name': 'Villanueva'},
            {'first_name': 'Ramon', 'last_name': 'Santiago'},
            {'first_name': 'Gloria', 'last_name': 'Navarro'},
            {'first_name': 'Enrique', 'last_name': 'Hernandez'},
            {'first_name': 'Victoria', 'last_name': 'Cruz'},
            {'first_name': 'Rafael', 'last_name': 'Ramos'},
            {'first_name': 'Beatriz', 'last_name': 'Domingo'},
            {'first_name': 'Mark', 'last_name': 'Tan'},
            {'first_name': 'Angel', 'last_name': 'Lim'},
        ]

        cities = [
            'Quezon City', 'Manila', 'Makati', 'Pasig', 'Taguig',
            'Mandaluyong', 'Pasay', 'Caloocan', 'Las Piñas', 'Parañaque'
        ]

        streets = ['Main', 'Market', 'Central', 'Rizal', 'Bonifacio', 'Luna', 'Del Pilar', 'Mabini']

        created_count = 0
        for i, member in enumerate(member_data, 1):
            username = f"member{i:02d}"
            password = 'member123'

            # Generate realistic birthdate (18-55 years old)
            years_ago = random.randint(18, 55)
            birthdate = date.today() - timedelta(days=years_ago*365 + random.randint(0, 365))

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{member['first_name'].lower()}.{member['last_name'].lower()}@gmail.com",
                    'first_name': member['first_name'],
                    'last_name': member['last_name'],
                    'password': make_password(password),
                    'role': 'member',
                    'mobile_no': f'09{random.randint(100000000, 999999999)}',
                    'address': f'{random.randint(1, 999)} {random.choice(streets)} Street, {random.choice(cities)}',
                    'birthdate': birthdate,
                }
            )

            if created:
                # Generate kiosk PIN for members
                user.generate_kiosk_pin()
                self.credentials['members'].append({
                    'username': user.username,
                    'password': password,
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}",
                    'mobile': user.mobile_no,
                    'kiosk_pin': user.kiosk_pin
                })
                created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} members\n')

    def create_memberships(self):
        """Create user memberships"""
        self.stdout.write(self.style.SUCCESS('📋 Creating User Memberships...\n'))

        members = User.objects.filter(role='member')
        plans = list(MembershipPlan.objects.all())

        created_count = 0
        for member in members:
            # 80% of members have active memberships
            if random.random() < 0.8:
                plan = random.choice(plans)

                # Most start within last 60 days
                days_ago = random.randint(0, 60)
                start_date = date.today() - timedelta(days=days_ago)
                end_date = start_date + timedelta(days=plan.duration_days)

                # Determine status
                if end_date < date.today():
                    status = 'expired'
                elif random.random() < 0.05:
                    status = 'cancelled'
                else:
                    status = 'active'

                membership = UserMembership.objects.create(
                    user=member,
                    plan=plan,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                )
                created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} memberships')
        self.stdout.write(f'   ℹ Active: {UserMembership.objects.filter(status="active").count()}')
        self.stdout.write(f'   ℹ Expired: {UserMembership.objects.filter(status="expired").count()}')
        self.stdout.write(f'   ℹ Cancelled: {UserMembership.objects.filter(status="cancelled").count()}\n')

    def create_payments(self):
        """Create payment records"""
        self.stdout.write(self.style.SUCCESS('💰 Creating Payment Records...\n'))

        memberships = UserMembership.objects.all()
        payment_methods = ['cash', 'gcash']
        staff_users = list(User.objects.filter(role__in=['admin', 'staff']))

        created_count = 0
        for membership in memberships:
            # 70% confirmed, 20% pending, 10% rejected
            status_choice = random.choices(
                ['confirmed', 'pending', 'rejected'],
                weights=[70, 20, 10]
            )[0]

            payment = Payment.objects.create(
                user=membership.user,
                membership=membership,
                amount=membership.plan.price,
                method=random.choice(payment_methods),
                payment_date=timezone.make_aware(
                    datetime.combine(membership.start_date, datetime.min.time())
                    + timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))
                ),
                status=status_choice,
            )

            if status_choice == 'confirmed' and staff_users:
                payment.approved_by = random.choice(staff_users)
                payment.approved_at = payment.payment_date + timedelta(hours=random.randint(1, 24))
                payment.save()
            elif status_choice == 'rejected' and staff_users:
                payment.approved_by = random.choice(staff_users)
                payment.approved_at = payment.payment_date + timedelta(hours=random.randint(1, 48))
                payment.rejection_reason = random.choice([
                    'Invalid reference number',
                    'Payment amount mismatch',
                    'Duplicate payment submission'
                ])
                payment.save()

            created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} payments')
        self.stdout.write(f'   ℹ Confirmed: {Payment.objects.filter(status="confirmed").count()}')
        self.stdout.write(f'   ℹ Pending: {Payment.objects.filter(status="pending").count()}')
        self.stdout.write(f'   ℹ Rejected: {Payment.objects.filter(status="rejected").count()}\n')

    def create_walk_in_payments(self):
        """Create walk-in payments for last 30 days"""
        self.stdout.write(self.style.SUCCESS('🚶 Creating Walk-in Payments...\n'))

        passes = list(FlexibleAccess.objects.all())
        staff_users = list(User.objects.filter(role__in=['admin', 'staff']))
        payment_methods = ['cash', 'gcash']

        created_count = 0
        for days_ago in range(30):
            payment_date = date.today() - timedelta(days=days_ago)
            num_payments = random.randint(3, 8)

            for _ in range(num_payments):
                pass_type = random.choice(passes)

                # 50% provide name
                if random.random() < 0.5:
                    names = ['John Doe', 'Jane Smith', 'Mark Wilson', 'Sarah Brown', 'Mike Davis', 'Lisa Anderson']
                    customer_name = random.choice(names)
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

    def create_attendance_records(self):
        """Create attendance records for last 30 days"""
        self.stdout.write(self.style.SUCCESS('📊 Creating Attendance Records...\n'))

        active_members = User.objects.filter(
            role='member',
            memberships__status='active',
            memberships__end_date__gte=date.today()
        ).distinct()

        created_count = 0
        for days_ago in range(30):
            check_date = date.today() - timedelta(days=days_ago)

            for member in active_members:
                # 50% chance of attending each day
                if random.random() < 0.5:
                    check_in_hour = random.randint(6, 21)
                    check_in_minute = random.randint(0, 59)
                    check_in = timezone.make_aware(
                        datetime.combine(
                            check_date,
                            datetime.min.time().replace(hour=check_in_hour, minute=check_in_minute)
                        )
                    )

                    # 90% checked out
                    if random.random() < 0.9:
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

    def create_analytics(self):
        """Generate analytics for last 30 days"""
        self.stdout.write(self.style.SUCCESS('📈 Generating Analytics Data...\n'))

        created_count = 0
        for days_ago in range(30):
            target_date = date.today() - timedelta(days=days_ago)
            Analytics.generate_daily_report(target_date)
            created_count += 1

        self.stdout.write(f'   ✓ Generated {created_count} analytics records\n')

    def create_audit_logs(self):
        """Create sample audit logs"""
        self.stdout.write(self.style.SUCCESS('📝 Creating Audit Logs...\n'))

        users = list(User.objects.all())
        actions = [
            ('login', 'info', 'User logged in successfully'),
            ('logout', 'info', 'User logged out'),
            ('membership_created', 'info', 'New membership subscription'),
            ('payment_received', 'info', 'Payment processed'),
            ('walkin_sale', 'info', 'Walk-in pass sold'),
        ]

        created_count = 0
        for _ in range(100):
            user = random.choice(users)
            action, severity, description = random.choice(actions)

            days_ago = random.randint(0, 30)
            timestamp = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))

            log = AuditLog.objects.create(
                user=user,
                action=action,
                severity=severity,
                description=f'{description} for {user.get_full_name()}',
                ip_address=f'192.168.1.{random.randint(1, 255)}',
            )
            log.timestamp = timestamp
            log.save(update_fields=['timestamp'])
            created_count += 1

        self.stdout.write(f'   ✓ Created {created_count} audit logs\n')

    def print_summary(self):
        """Print summary of seeded data"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('✅ DATABASE SEEDING COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # Print counts
        self.stdout.write(f'👥 Total Users: {User.objects.count()}')
        self.stdout.write(f'   ├─ Admins: {len(self.credentials["admins"])}')
        self.stdout.write(f'   ├─ Staff: {len(self.credentials["staff"])}')
        self.stdout.write(f'   └─ Members: {len(self.credentials["members"])}\n')

        self.stdout.write(f'💳 Membership Plans: {MembershipPlan.objects.count()}')
        self.stdout.write(f'🎫 Walk-in Passes: {FlexibleAccess.objects.count()}')
        self.stdout.write(f'📋 User Memberships: {UserMembership.objects.count()}')
        self.stdout.write(f'💰 Payments: {Payment.objects.count()}')
        self.stdout.write(f'🚶 Walk-in Payments: {WalkInPayment.objects.count()}')
        self.stdout.write(f'📊 Attendance Records: {Attendance.objects.count()}')
        self.stdout.write(f'📈 Analytics Records: {Analytics.objects.count()}')
        self.stdout.write(f'📝 Audit Logs: {AuditLog.objects.count()}\n')

        # Calculate revenue
        member_revenue = Payment.objects.filter(status='confirmed').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        walkin_revenue = WalkInPayment.objects.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        total_revenue = member_revenue + walkin_revenue

        self.stdout.write(self.style.SUCCESS(f'💵 Total Revenue: ₱{total_revenue:,.2f}'))
        self.stdout.write(f'   ├─ Member Payments: ₱{member_revenue:,.2f}')
        self.stdout.write(f'   └─ Walk-in Payments: ₱{walkin_revenue:,.2f}\n')

        # Print credentials preview
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('🔑 SYSTEM CREDENTIALS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        self.stdout.write(self.style.WARNING('ADMINS (3):'))
        for admin in self.credentials['admins']:
            self.stdout.write(f"   Username: {admin['username']:20} Password: {admin['password']:15} ({admin['name']})")

        self.stdout.write(self.style.WARNING('\nSTAFF (5):'))
        for staff in self.credentials['staff']:
            self.stdout.write(f"   Username: {staff['username']:20} Password: {staff['password']:15} ({staff['name']})")

        self.stdout.write(self.style.WARNING(f'\nMEMBERS (30):'))
        self.stdout.write(f"   All members use password: member123")
        self.stdout.write(f"   Usernames: member01 to member30\n")

        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('📄 Full credentials list saved to: SYSTEM_CREDENTIALS.md'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

    def save_credentials_file(self):
        """Save comprehensive credentials list to file"""
        content = f"""# 🏋️ Gym Management System - Complete Credentials List

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 👔 ADMINISTRATORS (3)

| # | Username | Password | Email | Full Name | Mobile | Role |
|---|----------|----------|-------|-----------|--------|------|
"""
        for i, admin in enumerate(self.credentials['admins'], 1):
            content += f"| {i} | `{admin['username']}` | `{admin['password']}` | {admin['email']} | {admin['name']} | {admin['mobile']} | Superuser Admin |\n"

        content += """
---

## 👨‍💼 STAFF MEMBERS (5)

| # | Username | Password | Email | Full Name | Mobile |
|---|----------|----------|-------|-----------|--------|
"""
        for i, staff in enumerate(self.credentials['staff'], 1):
            content += f"| {i} | `{staff['username']}` | `{staff['password']}` | {staff['email']} | {staff['name']} | {staff['mobile']} |\n"

        content += """
---

## 👥 GYM MEMBERS (30)

**All members use the same password:** `member123`

| # | Username | Password | Email | Full Name | Mobile | Kiosk PIN |
|---|----------|----------|-------|-----------|--------|-----------|
"""
        for i, member in enumerate(self.credentials['members'], 1):
            content += f"| {i:02d} | `{member['username']}` | `{member['password']}` | {member['email']} | {member['name']} | {member['mobile']} | `{member['kiosk_pin']}` |\n"

        content += """
---

## 🔐 Quick Access Guide

### Admin Login
- **Best for:** Full system management, reports, analytics
- **Examples:**
  - Username: `admin` | Password: `admin123`
  - Username: `gym_manager` | Password: `manager123`
  - Username: `director` | Password: `director123`

### Staff Login
- **Best for:** Daily operations, walk-in sales, member management
- **Examples:**
  - Username: `staff_sarah` | Password: `staff123`
  - Username: `staff_michael` | Password: `staff123`
  - Username: `staff_maria` | Password: `staff123`

### Member Login
- **Best for:** Personal dashboard, membership management, payments
- **Examples:**
  - Username: `member01` | Password: `member123`
  - Username: `member15` | Password: `member123`
  - Username: `member30` | Password: `member123`

### Kiosk Check-in
- **Access Method:** Enter 6-digit PIN (no username/password)
- **Example PINs:** See "Kiosk PIN" column in Members table above
- **Note:** Only members with active memberships can use kiosk

---

## 📊 System Functions Available

### Admins Can:
- ✅ Manage all users (create, edit, delete)
- ✅ Create and manage membership plans
- ✅ Approve/reject payments
- ✅ View all reports and analytics
- ✅ Access audit trail
- ✅ Configure chatbot settings
- ✅ Process walk-in sales
- ✅ View all members and transactions

### Staff Can:
- ✅ Process walk-in sales
- ✅ View member list
- ✅ Manage check-ins/check-outs
- ✅ Approve payments
- ✅ View attendance records
- ❌ Cannot modify plans
- ❌ Cannot access full analytics

### Members Can:
- ✅ Subscribe to membership plans
- ✅ Make payments
- ✅ View payment history
- ✅ Update personal profile
- ✅ Use kiosk check-in/check-out
- ✅ View own attendance history
- ❌ Cannot access other members' data

---

## 💳 Membership Plans

| Plan Name | Duration | Price | Description |
|-----------|----------|-------|-------------|
| Weekly Pass | 7 days | ₱500.00 | Perfect for trying out the gym |
| Monthly Membership | 30 days | ₱1,500.00 | Most popular choice! |
| Quarterly Membership | 90 days | ₱4,000.00 | 3 months commitment (Save ₱500) |
| Semi-Annual Premium | 180 days | ₱7,500.00 | 6 months access (Save ₱1,500) |
| Annual VIP Membership | 365 days | ₱14,000.00 | Full year VIP (Save ₱4,000) |

---

## 🎫 Walk-in Passes

| Pass Name | Duration | Price | Description |
|-----------|----------|-------|-------------|
| Single Day Pass | 1 day | ₱100.00 | One-time gym access |
| 3-Day Trial Pass | 3 days | ₱250.00 | Perfect for visitors |
| 5-Day Flex Pass | 5 days | ₱400.00 | Flexible access within a week |

---

## 🤖 AI Chatbot

- **Access:** Available on all pages for all users
- **Config:** Admins can configure in Chatbot Settings
- **Models:** llama3.2:1b, llama3.2:3b, gemma2:2b, phi3, mistral
- **Features:** Context-aware responses, role-based assistance

---

## 📝 Notes

1. **Kiosk PINs:** Each member has a unique 6-digit PIN for quick check-in/check-out
2. **Default Password:** All members use `member123` for easy testing
3. **Payment Methods:** Cash and GCash supported
4. **Membership Status:** Active, Expired, Cancelled, Pending
5. **Payment Status:** Confirmed, Pending, Rejected

---

## 🔧 Testing Scenarios

### Test Member Flow:
1. Login as any member (e.g., `member01` / `member123`)
2. View active membership on dashboard
3. Subscribe to a new plan
4. Make a payment
5. Check payment history

### Test Staff Operations:
1. Login as staff (e.g., `staff_sarah` / `staff123`)
2. Process walk-in sale
3. Approve pending payment
4. View member list
5. Check attendance records

### Test Admin Functions:
1. Login as admin (`admin` / `admin123`)
2. View full dashboard with analytics
3. Create new membership plan
4. Generate reports
5. View audit trail
6. Configure chatbot settings

### Test Kiosk:
1. Access `/kiosk/` URL
2. Enter any member's 6-digit PIN
3. Check in successfully
4. Later, enter same PIN to check out

---

## 🆘 Support

For issues or questions:
- Check system documentation in project files
- Review SYSTEM_DESCRIPTION.md for detailed info
- Check SEEDER_README.md for seeder details

---

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Seeder Version:** 2.0
**Total Users:** {len(self.credentials['admins']) + len(self.credentials['staff']) + len(self.credentials['members'])}
"""

        # Save to file
        with open('SYSTEM_CREDENTIALS.md', 'w', encoding='utf-8') as f:
            f.write(content)


# Import models for aggregation
from django.db import models
