"""
Comprehensive data seeder for the Gym App
Run with: python manage.py shell < seeder.py
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta, date
import random
import string

from gym_app.models import (
    MembershipPlan, FlexibleAccess, UserMembership, 
    Payment, WalkInPayment, Analytics, AuditLog, Attendance
)

User = get_user_model()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_user(username, email, first_name, last_name, role='member', 
                mobile_no=None, birthdate=None, is_staff=False, is_superuser=False):
    """Create a user with specified details"""
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'mobile_no': mobile_no or f'09{random.randint(100000000, 999999999)}',
            'birthdate': birthdate,
            'is_staff': is_staff,
            'is_superuser': is_superuser,
            'address': f"{random.randint(100, 999)} {random.choice(['Main', 'Oak', 'Maple', 'Pine', 'Cedar'])} Street, {random.choice(['Cabanatuan', 'Talugtug', 'General Tinio', 'San Jose City'])}",
        }
    )
    if created:
        user.set_password('password123')
        user.save()
    return user

def random_birthdate(min_age=18, max_age=80):
    """Generate random birthdate"""
    days_back = random.randint(min_age * 365, max_age * 365)
    return date.today() - timedelta(days=days_back)

def random_date_in_range(start_date, end_date):
    """Generate random datetime between two dates"""
    time_between = end_date - start_date
    random_days = random.randrange(time_between.days)
    return start_date + timedelta(days=random_days)

# ============================================================================
# 1. CREATE ADMIN AND STAFF USERS
# ============================================================================

print("Creating admin and staff users...")

admin_user = create_user(
    username='admin',
    email='admin@gym.com',
    first_name='System',
    last_name='Administrator',
    role='admin',
    is_staff=True,
    is_superuser=True,
    birthdate=date(1990, 5, 15)
)

staff_users = []
for i in range(5):
    staff = create_user(
        username=f'staff{i+1}',
        email=f'staff{i+1}@gym.com',
        first_name=f'Staff Member',
        last_name=f'{i+1}',
        role='staff',
        is_staff=True,
        birthdate=random_birthdate(25, 55)
    )
    staff_users.append(staff)

print(f"✓ Created 1 admin and {len(staff_users)} staff members")

# ============================================================================
# 2. CREATE MEMBERSHIP PLANS
# ============================================================================

print("Creating membership plans...")

plans_data = [
    ('1-Week Pass', 7, 299.00, 'Access for 1 week'),
    ('2-Week Pass', 14, 499.00, 'Access for 2 weeks'),
    ('1-Month Plan', 30, 999.00, 'Monthly membership with unlimited access'),
    ('3-Month Plan', 90, 2499.00, '3-month membership discount'),
    ('6-Month Plan', 180, 4499.00, '6-month commitment plan'),
    ('Annual Plan', 365, 7999.00, 'Full year membership with benefits'),
    ('Student Plan', 30, 599.00, 'Special rate for students'),
    ('Family Plan', 30, 1799.00, 'Up to 3 family members'),
]

membership_plans = []
for name, duration, price, description in plans_data:
    plan, created = MembershipPlan.objects.get_or_create(
        name=name,
        defaults={
            'duration_days': duration,
            'price': price,
            'description': description,
            'is_active': True
        }
    )
    membership_plans.append(plan)

print(f"✓ Created {len(membership_plans)} membership plans")

# ============================================================================
# 3. CREATE FLEXIBLE ACCESS PASSES
# ============================================================================

print("Creating flexible access passes...")

flex_data = [
    ('Day Pass', 1, 150.00, 'Single day access'),
    ('3-Day Pass', 3, 399.00, 'Valid for 3 days'),
    ('5-Day Pass', 5, 599.00, 'Valid for 5 days'),
    ('Weekly Pass', 7, 799.00, 'Valid for 1 week'),
    ('10-Entry Pass', 30, 1299.00, 'Use within 30 days, 10 visits'),
    ('Weekend Pass', 2, 299.00, 'Friday to Sunday access'),
]

flex_passes = []
for name, duration, price, description in flex_data:
    pass_obj, created = FlexibleAccess.objects.get_or_create(
        name=name,
        defaults={
            'duration_days': duration,
            'price': price,
            'description': description,
            'is_active': True
        }
    )
    flex_passes.append(pass_obj)

print(f"✓ Created {len(flex_passes)} flexible access passes")

# ============================================================================
# 4. CREATE MEMBER USERS
# ============================================================================

print("Creating member users...")

member_count = 150
members = []
first_names = ['Juan', 'Maria', 'Carlos', 'Ana', 'Miguel', 'Rosa', 'José', 'Carmen', 
               'Diego', 'Isabel', 'Fernando', 'Sofia', 'Luis', 'Elena', 'Ramon']
last_names = ['Santos', 'Garcia', 'Reyes', 'Cruz', 'Flores', 'Morales', 'Torres',
             'Rivera', 'Gutierrez', 'Romero', 'Alvarez', 'Castillo', 'Dominguez']

for i in range(member_count):
    member = create_user(
        username=f'member{i+1}',
        email=f'member{i+1}@gym.com',
        first_name=random.choice(first_names),
        last_name=random.choice(last_names),
        role='member',
        birthdate=random_birthdate(18, 70)
    )
    members.append(member)

print(f"✓ Created {len(members)} member users")

# ============================================================================
# 5. CREATE USER MEMBERSHIPS
# ============================================================================

print("Creating user memberships...")

membership_count = 0
today = date.today()

for member in members:
    # 70% of members have active memberships
    if random.random() < 0.7:
        plan = random.choice(membership_plans)
        
        # Random start date in the past 6 months
        start_date = today - timedelta(days=random.randint(0, 180))
        
        membership = UserMembership.objects.create(
            user=member,
            plan=plan,
            start_date=start_date,
            status='active'
        )
        membership_count += 1
    
    # 30% have expired memberships
    elif random.random() < 0.4:
        plan = random.choice(membership_plans)
        end_date = today - timedelta(days=random.randint(1, 90))
        start_date = end_date - timedelta(days=plan.duration_days)
        
        membership = UserMembership.objects.create(
            user=member,
            plan=plan,
            start_date=start_date,
            status='expired'
        )
        membership_count += 1

print(f"✓ Created {membership_count} user memberships")

# ============================================================================
# 6. CREATE PAYMENTS FOR MEMBERS
# ============================================================================

print("Creating member payments...")

payment_count = 0
payment_methods = ['cash', 'gcash']

for membership in UserMembership.objects.all():
    # Payment records for member memberships
    payment = Payment.objects.create(
        user=membership.user,
        membership=membership,
        amount=membership.plan.price,
        method=random.choice(payment_methods),
        payment_date=timezone.make_aware(
            datetime.combine(membership.start_date, 
                           datetime.min.time()) + timedelta(hours=random.randint(8, 18))
        ),
        reference_no=f"PAY{random.randint(100000, 999999)}",
        notes=random.choice(['Standard payment', 'Online transfer', 'Counter payment', ''])
    )
    payment_count += 1
    
    # Some members have multiple payment records
    if random.random() < 0.3:
        payment2 = Payment.objects.create(
            user=membership.user,
            membership=membership,
            amount=random.randint(500, 2000),
            method=random.choice(payment_methods),
            payment_date=timezone.make_aware(
                datetime.combine(
                    membership.start_date + timedelta(days=random.randint(10, 20)),
                    datetime.min.time()
                ) + timedelta(hours=random.randint(8, 18))
            ),
            reference_no=f"PAY{random.randint(100000, 999999)}",
            notes='Additional payment'
        )
        payment_count += 1

print(f"✓ Created {payment_count} member payments")

# ============================================================================
# 7. CREATE WALK-IN PAYMENTS
# ============================================================================

print("Creating walk-in payments...")

walkin_count = 0
last_90_days = today - timedelta(days=90)

for day_offset in range(90):
    current_date = last_90_days + timedelta(days=day_offset)
    
    # 40-80% of days have walk-in sales
    if random.random() < 0.6:
        # 1-5 walk-in sales per day
        daily_sales = random.randint(1, 5)
        
        for _ in range(daily_sales):
            walkin = WalkInPayment.objects.create(
                pass_type=random.choice(flex_passes),
                customer_name=f"{random.choice(first_names)} {random.choice(last_names)}",
                mobile_no=f'09{random.randint(100000000, 999999999)}',
                amount=random.choice(flex_passes).price,
                method=random.choice(payment_methods),
                payment_date=timezone.make_aware(
                    datetime.combine(current_date, 
                                   datetime.min.time()) + timedelta(hours=random.randint(6, 20))
                ),
                reference_no=f"WI{random.randint(100000, 999999)}",
                notes=random.choice(['Walk-in', 'Referral', 'First time', ''])
            )
            walkin_count += 1

print(f"✓ Created {walkin_count} walk-in payments")

# ============================================================================
# 8. CREATE ATTENDANCE RECORDS
# ============================================================================

print("Creating attendance records...")

attendance_count = 0
active_members = [m for m in members if m.memberships.filter(status='active').exists()]

for member in active_members:
    # 5-30 attendance records per active member
    visit_count = random.randint(5, 30)
    
    # Generate attendance records over the last 60 days
    for visit in range(visit_count):
        check_in_date = today - timedelta(days=random.randint(0, 60))
        check_in_time = datetime.min.time().replace(hour=random.randint(6, 19), 
                                                     minute=random.randint(0, 59))
        check_in = timezone.make_aware(datetime.combine(check_in_date, check_in_time))
        
        # Duration: 30 minutes to 3 hours
        duration = random.randint(30, 180)
        check_out = check_in + timedelta(minutes=duration)
        
        attendance = Attendance.objects.create(
            user=member,
            check_in=check_in,
            check_out=check_out,
            notes=random.choice(['', 'Cardio day', 'Strength training', 'Legs day', 'Rest day'])
        )
        attendance_count += 1

print(f"✓ Created {attendance_count} attendance records")

# ============================================================================
# 9. GENERATE ANALYTICS
# ============================================================================

print("Generating analytics...")

analytics_count = 0
for day_offset in range(90):
    analytics_date = today - timedelta(days=day_offset)
    analytics = Analytics.generate_daily_report(analytics_date)
    analytics_count += 1

print(f"✓ Generated analytics for {analytics_count} days")

# ============================================================================
# 10. CREATE AUDIT LOGS
# ============================================================================

print("Creating audit logs...")

audit_count = 0

# Admin login logs
for i in range(10):
    log = AuditLog.log(
        action='login',
        user=admin_user,
        description='Admin user logged in successfully',
        severity='info'
    )
    audit_count += 1

# User registration logs
for member in members[:50]:
    log = AuditLog.log(
        action='register',
        user=member,
        description=f'New member {member.get_full_name()} registered',
        severity='info'
    )
    audit_count += 1

# Membership created logs
for membership in list(UserMembership.objects.all())[:100]:
    log = AuditLog.log(
        action='membership_created',
        user=membership.user,
        description=f'Membership to {membership.plan.name} created',
        severity='info',
        model_name='UserMembership',
        object_id=membership.id,
        object_repr=str(membership)
    )
    audit_count += 1

# Payment logs
for payment in list(Payment.objects.all())[:100]:
    log = AuditLog.log(
        action='payment_received',
        user=payment.user,
        description=f'Payment of ₱{payment.amount} received via {payment.method}',
        severity='info',
        model_name='Payment',
        object_id=payment.id
    )
    audit_count += 1

# Walk-in sale logs
for walkin in list(WalkInPayment.objects.all())[:100]:
    log = AuditLog.log(
        action='walkin_sale',
        user=None,
        description=f'Walk-in sale: {walkin.pass_type.name} for ₱{walkin.amount}',
        severity='info',
        model_name='WalkInPayment',
        object_id=walkin.id
    )
    audit_count += 1

print(f"✓ Created {audit_count} audit logs")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*60)
print("SEEDING COMPLETE!")
print("="*60)
print(f"✓ Admin users: 1")
print(f"✓ Staff users: {len(staff_users)}")
print(f"✓ Member users: {len(members)}")
print(f"✓ Membership plans: {len(membership_plans)}")
print(f"✓ Flexible passes: {len(flex_passes)}")
print(f"✓ User memberships: {UserMembership.objects.count()}")
print(f"✓ Member payments: {Payment.objects.count()}")
print(f"✓ Walk-in payments: {WalkInPayment.objects.count()}")
print(f"✓ Attendance records: {Attendance.objects.count()}")
print(f"✓ Analytics entries: {Analytics.objects.count()}")
print(f"✓ Audit logs: {AuditLog.objects.count()}")
print("="*60)