from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from .chatbot import GymChatbot
from .utils import generate_gcash_qr_code, get_gcash_merchant_info

from .models import (
    User, MembershipPlan, FlexibleAccess,
    UserMembership, Payment, WalkInPayment, Analytics, AuditLog, LoginActivity,
    HeroSection, GymGallery
)


# ==================== Public Views ====================

def home(request):
    """Homepage - displays available plans and walk-in options"""
    # Get only ACTIVE and NON-ARCHIVED plans and passes
    membership_plans = MembershipPlan.objects.filter(
        is_active=True,
        is_archived=False
    ).order_by('price')
    walk_in_passes = FlexibleAccess.objects.filter(
        is_active=True,
        is_archived=False
    ).order_by('duration_days')

    # Get active hero sections
    hero_sections = HeroSection.objects.filter(is_active=True).order_by('display_order')

    # Get featured gallery images
    gallery_images = GymGallery.objects.filter(
        is_active=True,
        is_featured=True
    ).order_by('display_order')[:6]  # Show max 6 featured images

    context = {
        'membership_plans': membership_plans,
        'walk_in_passes': walk_in_passes,
        'hero_sections': hero_sections,
        'gallery_images': gallery_images,
    }
    return render(request, 'gym_app/home.html', context)


def about(request):
    """About page"""
    return render(request, 'gym_app/about.html')


# ==================== Authentication Views ====================

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)

            # Record login activity
            LoginActivity.record_login(user, request, success=True)

            # Log successful login
            AuditLog.log(
                action='login',
                user=user,
                description=f'User {user.username} logged in successfully',
                severity='info',
                request=request
            )

            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('dashboard')
        else:
            # Try to find user for failed login tracking
            try:
                failed_user = User.objects.get(username=username)
                LoginActivity.record_login(
                    failed_user, request, success=False,
                    failure_reason='Invalid password'
                )
            except User.DoesNotExist:
                pass  # User doesn't exist, can't track

            # Log failed login attempt
            AuditLog.log(
                action='login_failed',
                description=f'Failed login attempt for username: {username}',
                severity='warning',
                request=request
            )

            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'gym_app/login.html')


@login_required
def logout_view(request):
    """Handle user logout"""
    username = request.user.username
    
    # Log logout
    AuditLog.log(
        action='logout',
        user=request.user,
        description=f'User {username} logged out',
        severity='info',
        request=request
    )
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def register_step1(request):
    """Step 1: Account Information"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'gym_app/register_step1.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'gym_app/register_step1.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'gym_app/register_step1.html')

        # Store in session
        request.session['registration_data'] = {
            'username': username,
            'email': email,
            'password': password,
        }

        return redirect('register_step2')

    return render(request, 'gym_app/register_step1.html')


def register_step2(request):
    """Step 2: Personal Information"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if 'registration_data' not in request.session:
        messages.error(request, 'Please start from step 1.')
        return redirect('register_step1')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        mobile_no = request.POST.get('mobile_no')
        address = request.POST.get('address')
        birthdate_str = request.POST.get('birthdate')

        # Validation
        if not first_name or not last_name:
            messages.error(request, 'First name and last name are required.')
            return render(request, 'gym_app/register_step2.html')

        # Update session data
        request.session['registration_data'].update({
            'first_name': first_name,
            'last_name': last_name,
            'mobile_no': mobile_no,
            'address': address,
            'birthdate': birthdate_str,
        })
        request.session.modified = True

        return redirect('register_step3')

    return render(request, 'gym_app/register_step2.html')


def register_step3(request):
    """Step 3: Profile Image Upload (Optional)"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if 'registration_data' not in request.session:
        messages.error(request, 'Please start from step 1.')
        return redirect('register_step1')

    if request.method == 'POST':
        profile_image = request.FILES.get('profile_image')

        # Store image temporarily
        if profile_image:
            import os
            from django.core.files.storage import default_storage
            from django.conf import settings

            # Save to temporary location
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)

            temp_path = os.path.join('temp', profile_image.name)
            saved_path = default_storage.save(temp_path, profile_image)

            request.session['registration_data']['has_image'] = True
            request.session['temp_image_path'] = saved_path
        else:
            request.session['registration_data']['has_image'] = False

        request.session.modified = True
        return redirect('register_review')

    return render(request, 'gym_app/register_step3.html')


def register_review(request):
    """Step 4: Review and Confirm"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if 'registration_data' not in request.session:
        messages.error(request, 'Please start from step 1.')
        return redirect('register_step1')

    registration_data = request.session.get('registration_data')

    if request.method == 'POST':
        # Create user
        birthdate = None
        if registration_data.get('birthdate'):
            try:
                from datetime import datetime
                birthdate = datetime.strptime(registration_data['birthdate'], '%Y-%m-%d').date()
            except ValueError:
                pass

        user = User.objects.create_user(
            username=registration_data['username'],
            email=registration_data['email'],
            password=registration_data['password'],
            first_name=registration_data['first_name'],
            last_name=registration_data['last_name'],
            mobile_no=registration_data.get('mobile_no', ''),
            address=registration_data.get('address', ''),
            birthdate=birthdate,
            role='member'
        )

        # Handle profile image from temporary storage
        temp_image_path = request.session.get('temp_image_path')
        if temp_image_path:
            import os
            from django.core.files.storage import default_storage
            from django.core.files import File

            if default_storage.exists(temp_image_path):
                with default_storage.open(temp_image_path, 'rb') as temp_file:
                    user.profile_image.save(
                        os.path.basename(temp_image_path),
                        File(temp_file),
                        save=True
                    )
                # Delete temporary file
                default_storage.delete(temp_image_path)

        # Log registration
        AuditLog.log(
            action='register',
            user=user,
            description=f'New member registered: {user.get_full_name()} ({user.email})',
            severity='info',
            request=request
        )

        # Clear session
        del request.session['registration_data']
        if 'temp_image_path' in request.session:
            del request.session['temp_image_path']

        messages.success(request, 'Registration successful! Please log in.')
        return redirect('login')

    context = {
        'data': registration_data
    }
    return render(request, 'gym_app/register_review.html', context)


# Backward compatibility - redirect old registration to step 1
def register_view(request):
    """Legacy registration redirect"""
    return redirect('register_step1')


# ==================== Dashboard Views ====================

@login_required
def dashboard(request):
    """Role-based dashboard"""
    user = request.user
    
    # Redirect based on role
    if user.is_admin():
        return admin_dashboard(request)
    elif user.role == 'staff':
        return staff_dashboard(request)
    else:
        return member_dashboard(request)


@login_required
def admin_dashboard(request):
    """Admin dashboard with full analytics"""
    if not request.user.is_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    # Get today's stats
    today = date.today()

    # Active memberships
    active_memberships = UserMembership.objects.filter(
        status='active',
        end_date__gte=today
    ).count()

    # Total members
    total_members = User.objects.filter(role='member').count()

    # Today's revenue
    today_member_sales = Payment.objects.filter(
        payment_date__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    today_walkin_sales = WalkInPayment.objects.filter(
        payment_date__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    today_revenue = today_member_sales + today_walkin_sales

    # This month's revenue
    month_start = today.replace(day=1)
    month_member_sales = Payment.objects.filter(
        payment_date__date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    month_walkin_sales = WalkInPayment.objects.filter(
        payment_date__date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    month_revenue = month_member_sales + month_walkin_sales

    # Pending payments - IMPORTANT for admin to review
    pending_payments = Payment.objects.filter(
        status='pending'
    ).select_related('user', 'membership__plan').order_by('-payment_date')[:10]

    # New member registrations (last 7 days)
    seven_days_ago = today - timedelta(days=7)
    new_members = User.objects.filter(
        role='member',
        date_joined__gte=seven_days_ago
    ).prefetch_related('memberships').order_by('-date_joined')[:10]

    # Recent payments (confirmed only)
    recent_payments = Payment.objects.filter(
        status='confirmed'
    ).select_related('user', 'membership__plan').order_by('-payment_date')[:10]

    recent_walkins = WalkInPayment.objects.select_related('pass_type').order_by('-payment_date')[:10]

    # Expiring soon (next 7 days)
    expiring_soon = UserMembership.objects.filter(
        status='active',
        end_date__range=[today, today + timedelta(days=7)]
    ).select_related('user', 'plan').order_by('end_date')[:10]

    # Recent staff activity (from audit log)
    recent_staff_activity = AuditLog.objects.filter(
        user__role__in=['admin', 'staff']
    ).select_related('user').order_by('-timestamp')[:10]

    context = {
        'active_memberships': active_memberships,
        'total_members': total_members,
        'today_revenue': today_revenue,
        'month_revenue': month_revenue,
        'pending_payments': pending_payments,
        'new_members': new_members,
        'recent_payments': recent_payments,
        'recent_walkins': recent_walkins,
        'expiring_soon': expiring_soon,
        'recent_staff_activity': recent_staff_activity,
    }

    return render(request, 'gym_app/dashboard_admin.html', context)


@login_required
def staff_dashboard(request):
    """Staff dashboard - similar to admin but limited"""
    if not request.user.is_staff_or_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    today = date.today()

    # Today's transactions
    today_payments = Payment.objects.filter(
        payment_date__date=today
    ).count()

    today_walkins = WalkInPayment.objects.filter(
        payment_date__date=today
    ).count()

    # Today's revenue
    today_member_sales = Payment.objects.filter(
        payment_date__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    today_walkin_sales = WalkInPayment.objects.filter(
        payment_date__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    today_revenue = today_member_sales + today_walkin_sales

    # Pending payments - IMPORTANT for staff to review
    pending_payments = Payment.objects.filter(
        status='pending'
    ).select_related('user', 'membership__plan').order_by('-payment_date')[:10]

    # Recent activity (confirmed payments only)
    recent_payments = Payment.objects.filter(
        status='confirmed'
    ).select_related('user', 'membership__plan').order_by('-payment_date')[:10]

    recent_walkins = WalkInPayment.objects.select_related('pass_type').order_by('-payment_date')[:10]

    # Expiring soon
    expiring_soon = UserMembership.objects.filter(
        status='active',
        end_date__range=[today, today + timedelta(days=7)]
    ).select_related('user', 'plan').order_by('end_date')[:10]

    # Available membership plans
    membership_plans = MembershipPlan.objects.filter(is_active=True)

    context = {
        'today_payments': today_payments,
        'today_walkins': today_walkins,
        'today_revenue': today_revenue,
        'pending_payments': pending_payments,
        'recent_payments': recent_payments,
        'recent_walkins': recent_walkins,
        'expiring_soon': expiring_soon,
        'membership_plans': membership_plans,
    }

    return render(request, 'gym_app/dashboard_staff.html', context)


@login_required
def member_dashboard(request):
    """Member dashboard - view own membership status"""
    user = request.user
    
    # Get current membership
    current_membership = UserMembership.objects.filter(
        user=user,
        status='active'
    ).select_related('plan').first()
    
    # Payment history
    payment_history = Payment.objects.filter(
        user=user
    ).select_related('membership__plan').order_by('-payment_date')[:10]
    
    # All memberships (history)
    all_memberships = UserMembership.objects.filter(
        user=user
    ).select_related('plan').order_by('-start_date')
    
    context = {
        'current_membership': current_membership,
        'payment_history': payment_history,
        'all_memberships': all_memberships,
    }
    
    return render(request, 'gym_app/dashboard_member.html', context)


# ==================== Membership Management ====================

@login_required
def membership_plans_view(request):
    """View all available membership plans"""
    # Get only ACTIVE and NON-ARCHIVED plans
    plans = MembershipPlan.objects.filter(
        is_active=True,
        is_archived=False
    ).order_by('price')

    # If member, show if they have active membership
    current_membership = None
    if request.user.role == 'member':
        current_membership = UserMembership.objects.filter(
            user=request.user,
            status='active'
        ).first()

    context = {
        'plans': plans,
        'current_membership': current_membership,
    }

    return render(request, 'gym_app/membership_plans.html', context)


# Update the subscribe_plan view in gym_app/views.py
# Replace the POST section with this:

@login_required
def subscribe_plan(request, plan_id):
    """Subscribe to a membership plan"""
    if request.user.role != 'member':
        messages.error(request, 'Only members can subscribe to plans.')
        return redirect('membership_plans')
    
    plan = get_object_or_404(MembershipPlan, id=plan_id, is_active=True)
    
    # Check if user already has active membership
    active_membership = UserMembership.objects.filter(
        user=request.user,
        status='active'
    ).first()
    
    if active_membership:
        messages.warning(request, 'You already have an active membership.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        notes = request.POST.get('notes', '')

        # Create membership with pending status
        membership = UserMembership.objects.create(
            user=request.user,
            plan=plan,
            start_date=date.today(),
            status='pending'  # Changed to pending
        )

        # Create payment record with pending status (reference_no auto-generated)
        payment = Payment.objects.create(
            user=request.user,
            membership=membership,
            amount=plan.price,
            method=payment_method,
            notes=notes,
            status='pending',  # Payment needs confirmation
            payment_date=timezone.now()
        )

        # Don't generate PIN until payment is confirmed
        # PIN will be generated when staff/admin confirms payment

        # Log subscription
        AuditLog.log(
            action='membership_created',
            user=request.user,
            description=f'Subscribed to {plan.name} - ₱{plan.price} (Pending confirmation)',
            severity='info',
            request=request,
            model_name='UserMembership',
            object_id=membership.id,
            object_repr=str(membership),
            plan_name=plan.name,
            amount=float(plan.price)
        )

        # Log payment
        AuditLog.log(
            action='payment_received',
            user=request.user,
            description=f'Payment submitted: ₱{plan.price} via {payment_method} (Ref: {payment.reference_no})',
            severity='info',
            request=request,
            model_name='Payment',
            object_id=payment.id,
            object_repr=str(payment),
            amount=float(plan.price),
            payment_method=payment_method,
            reference_no=payment.reference_no
        )

        messages.success(
            request,
            f'Successfully subscribed to {plan.name}! '
            f'Your payment reference number is: {payment.reference_no}. '
            f'Your membership will be activated once payment is confirmed by staff.'
        )

        return redirect('dashboard')
    
    context = {
        'plan': plan,
    }
    
    return render(request, 'gym_app/subscribe_plan.html', context)


# ==================== Walk-in Management ====================

@login_required
def walkin_purchase(request):
    """Process walk-in pass purchase (staff/admin only)"""
    if not request.user.is_staff_or_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        pass_id = request.POST.get('pass_id')
        customer_name = request.POST.get('customer_name', '')
        mobile_no = request.POST.get('mobile_no', '')
        payment_method = request.POST.get('payment_method')
        reference_no = request.POST.get('reference_no', '')
        
        pass_type = get_object_or_404(FlexibleAccess, id=pass_id, is_active=True)
        
        # Store in session for confirmation
        request.session['pending_walkin'] = {
            'pass_id': pass_id,
            'pass_name': pass_type.name,
            'customer_name': customer_name,
            'mobile_no': mobile_no,
            'amount': str(pass_type.price),
            'payment_method': payment_method,
            'reference_no': reference_no,
        }
        
        return redirect('walkin_confirm')
    
    # Get only ACTIVE passes
    passes = FlexibleAccess.objects.filter(is_active=True).order_by('duration_days')
    recent_walkins = WalkInPayment.objects.select_related('pass_type').order_by('-payment_date')[:10]
    
    context = {
        'passes': passes,
        'recent_walkins': recent_walkins,
    }
    
    return render(request, 'gym_app/walkin_purchase.html', context)


@login_required
def walkin_confirm(request):
    """Confirm walk-in payment (staff/admin only)"""
    if not request.user.is_staff_or_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    pending = request.session.get('pending_walkin')
    if not pending:
        messages.error(request, 'No pending transaction.')
        return redirect('walkin_purchase')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'confirm':
            pass_type = get_object_or_404(FlexibleAccess, id=pending['pass_id'], is_active=True)

            # Create walk-in payment
            walkin_payment = WalkInPayment.objects.create(
                pass_type=pass_type,
                customer_name=pending['customer_name'],
                mobile_no=pending['mobile_no'],
                amount=pass_type.price,
                method=pending['payment_method'],
                reference_no=pending['reference_no'],
                payment_date=timezone.now()
            )

            # Log walk-in sale
            AuditLog.log(
                action='walkin_sale',
                user=request.user,
                description=f'Walk-in sale: {pass_type.name} - ₱{pass_type.price} to {pending["customer_name"] or "Anonymous"}',
                severity='info',
                request=request,
                model_name='WalkInPayment',
                object_id=walkin_payment.id,
                object_repr=str(walkin_payment),
                pass_name=pass_type.name,
                amount=float(pass_type.price),
                customer=pending['customer_name'] or 'Anonymous',
                payment_method=pending['payment_method']
            )

            # Clear session
            del request.session['pending_walkin']

            messages.success(request, f'Walk-in pass sold successfully! (₱{pass_type.price})')
            return redirect('walkin_purchase')
        else:
            # Cancel
            del request.session['pending_walkin']
            messages.info(request, 'Transaction cancelled.')
            return redirect('walkin_purchase')

    # Generate QR code for GCash payments
    qr_code_data = None
    gcash_merchant_info = None
    if pending.get('payment_method') == 'gcash':
        qr_code_data = generate_gcash_qr_code(pending['amount'], pending['reference_no'])
        gcash_merchant_info = get_gcash_merchant_info()

    context = {
        'pending': pending,
        'qr_code_data': qr_code_data,
        'gcash_merchant_info': gcash_merchant_info,
    }

    return render(request, 'gym_app/walkin_confirm.html', context)


# ==================== Reports & Analytics ====================

@login_required
def reports_view(request):
    """Analytics and reports (admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Generate today's analytics if not exists
    Analytics.generate_daily_report()
    
    # Get recent analytics
    recent_analytics = Analytics.objects.all()[:30]
    
    # Summary stats
    total_revenue = Payment.objects.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    total_walkin_revenue = WalkInPayment.objects.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    grand_total = total_revenue + total_walkin_revenue
    
    context = {
        'recent_analytics': recent_analytics,
        'total_revenue': total_revenue,
        'total_walkin_revenue': total_walkin_revenue,
        'grand_total': grand_total,
    }
    
    return render(request, 'gym_app/reports.html', context)


# ==================== Member Management (Admin/Staff) ====================

@login_required
def members_list(request):
    """List all members and staff (admin/staff only)"""
    if not request.user.is_staff_or_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    # Get members and staff separately
    members = User.objects.filter(role='member').order_by('-date_joined')
    staff = User.objects.filter(role='staff').order_by('-date_joined')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(mobile_no__icontains=search_query)
        )
        staff = staff.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(mobile_no__icontains=search_query)
        )

    context = {
        'members': members,
        'staff': staff,
        'search_query': search_query,
    }

    return render(request, 'gym_app/members_list.html', context)


@login_required
def create_staff_view(request):
    """Create staff user (admin only)"""
    if not request.user.is_admin():
        AuditLog.log(
            action='unauthorized_access',
            user=request.user,
            description='Attempted to create staff user',
            severity='warning',
            request=request
        )
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        mobile_no = request.POST.get('mobile_no')

        # Validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'gym_app/create_staff.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'gym_app/create_staff.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'gym_app/create_staff.html')

        # Create staff user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            mobile_no=mobile_no,
            role='staff',
            is_staff=True  # Django staff permission
        )

        # Log staff creation
        AuditLog.log(
            action='user_created',
            user=request.user,
            description=f'Created staff user: {user.get_full_name()} ({user.email})',
            severity='info',
            request=request,
            model_name='User',
            object_id=user.id,
            object_repr=str(user)
        )

        messages.success(request, f'Staff user {username} created successfully!')
        return redirect('members_list')

    return render(request, 'gym_app/create_staff.html')


@login_required
def staff_detail(request, user_id):
    """View staff details (admin/staff can view)"""
    if not request.user.is_staff_or_admin():
        AuditLog.log(
            action='unauthorized_access',
            user=request.user,
            description=f'Attempted to access staff detail for user_id: {user_id}',
            severity='warning',
            request=request
        )
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    staff_member = get_object_or_404(User, id=user_id, role='staff')

    # Get recent activity by this staff member from audit log
    recent_activity = AuditLog.objects.filter(
        user=staff_member
    ).order_by('-timestamp')[:20]

    context = {
        'staff_member': staff_member,
        'recent_activity': recent_activity,
    }

    return render(request, 'gym_app/staff_detail.html', context)


@login_required
def edit_staff(request, user_id):
    """Edit staff details (admin only)"""
    if not request.user.is_admin():
        AuditLog.log(
            action='unauthorized_access',
            user=request.user,
            description=f'Attempted to edit staff user_id: {user_id}',
            severity='warning',
            request=request
        )
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')

    staff_member = get_object_or_404(User, id=user_id, role='staff')

    if request.method == 'POST':
        # Update staff information
        staff_member.first_name = request.POST.get('first_name', staff_member.first_name)
        staff_member.last_name = request.POST.get('last_name', staff_member.last_name)
        staff_member.email = request.POST.get('email', staff_member.email)
        staff_member.mobile_no = request.POST.get('mobile_no', staff_member.mobile_no)
        staff_member.address = request.POST.get('address', staff_member.address)

        birthdate_str = request.POST.get('birthdate')
        if birthdate_str:
            try:
                from datetime import datetime
                staff_member.birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Invalid birthdate format.')
                return redirect('edit_staff', user_id=user_id)

        # Handle profile picture upload
        profile_image = request.FILES.get('profile_image')
        if profile_image:
            # Delete old profile image if exists
            if staff_member.profile_image:
                old_image_path = staff_member.profile_image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            staff_member.profile_image = profile_image

        staff_member.save()

        # Log staff update
        AuditLog.log(
            action='user_updated',
            user=request.user,
            description=f'Updated staff user: {staff_member.get_full_name()} ({staff_member.email})',
            severity='info',
            request=request,
            model_name='User',
            object_id=staff_member.id,
            object_repr=str(staff_member)
        )

        messages.success(request, f'Staff user {staff_member.username} updated successfully!')
        return redirect('staff_detail', user_id=user_id)

    context = {
        'staff_member': staff_member,
    }

    return render(request, 'gym_app/edit_staff.html', context)


@login_required
def member_detail(request, user_id):
    """View member details (admin/staff only)"""
    if not request.user.is_staff_or_admin():
        # Log unauthorized access
        AuditLog.log(
            action='unauthorized_access',
            user=request.user,
            description=f'Attempted to access member detail for user_id: {user_id}',
            severity='warning',
            request=request
        )
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    member = get_object_or_404(User, id=user_id, role='member')
    
    # Get memberships
    memberships = UserMembership.objects.filter(
        user=member
    ).select_related('plan').order_by('-start_date')
    
    # Get payments
    payments = Payment.objects.filter(
        user=member
    ).select_related('membership__plan').order_by('-payment_date')
    
    context = {
        'member': member,
        'memberships': memberships,
        'payments': payments,
    }
    
    return render(request, 'gym_app/member_detail.html', context)


@login_required
def cancel_membership(request, membership_id):
    """Cancel an active membership"""
    membership = get_object_or_404(UserMembership, id=membership_id)
    
    # Only the member or admin can cancel their membership
    if request.user != membership.user and not request.user.is_admin():
        messages.error(request, 'You can only cancel your own membership.')
        return redirect('dashboard')
    
    # Can only cancel active memberships
    if membership.status != 'active':
        messages.error(request, f'Cannot cancel {membership.status} membership.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        # Cancel the membership
        membership.cancel(user=request.user, reason=reason)
        
        # Log cancellation
        AuditLog.log(
            action='membership_cancelled',
            user=request.user,
            description=f'Membership cancelled: {membership.user.get_full_name()} - {membership.plan.name}. Reason: {reason}',
            severity='warning',
            request=request,
            model_name='UserMembership',
            object_id=membership.id,
            object_repr=str(membership)
        )
        
        messages.success(
            request,
            f'Your {membership.plan.name} membership has been cancelled successfully.'
        )
        
        return redirect('dashboard')
    
    context = {
        'membership': membership,
    }
    
    return render(request, 'gym_app/cancel_membership.html', context)


@login_required
def cancel_membership_confirm(request, membership_id):
    """Confirmation page for membership cancellation"""
    membership = get_object_or_404(UserMembership, id=membership_id)
    
    # Only the member or admin can view this
    if request.user != membership.user and not request.user.is_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Can only cancel active memberships
    if membership.status != 'active':
        messages.error(request, f'Cannot cancel {membership.status} membership.')
        return redirect('dashboard')
    
    context = {
        'membership': membership,
    }
    
    return render(request, 'gym_app/cancel_membership_confirm.html', context)



# ==================== Audit Trail Views ====================

@login_required
def audit_trail_view(request):
    """View audit trail (admin only)"""
    if not request.user.is_admin():
        AuditLog.log(
            action='unauthorized_access',
            user=request.user,
            description='Attempted to access audit trail',
            severity='warning',
            request=request
        )
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Filters
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    severity_filter = request.GET.get('severity', '')
    days_filter = request.GET.get('days', '7')
    
    # Base query
    logs = AuditLog.objects.all().select_related('user')
    
    # Apply filters
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    if severity_filter:
        logs = logs.filter(severity=severity_filter)
    
    if days_filter:
        try:
            days = int(days_filter)
            from datetime import timedelta
            start_date = timezone.now() - timedelta(days=days)
            logs = logs.filter(timestamp__gte=start_date)
        except ValueError:
            pass
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)  # 50 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique actions for filter dropdown
    actions = AuditLog.ACTION_CHOICES
    
    context = {
        'page_obj': page_obj,
        'actions': actions,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'severity_filter': severity_filter,
        'days_filter': days_filter,
    }
    
    return render(request, 'gym_app/audit_trail.html', context)


# ==================== Plan Management Views ====================

@login_required
def manage_plans_view(request):
    """Manage membership plans and walk-in passes (admin/staff only)"""
    if not request.user.is_staff_or_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        plan_type = request.POST.get('plan_type')
        plan_id = request.POST.get('plan_id')

        if action == 'add':
            name = request.POST.get('name')
            duration_days = request.POST.get('duration_days')
            price = request.POST.get('price')
            description = request.POST.get('description', '')

            if plan_type == 'membership':
                plan = MembershipPlan.objects.create(
                    name=name,
                    duration_days=duration_days,
                    price=price,
                    description=description
                )
                AuditLog.log(
                    action='plan_created',
                    user=request.user,
                    description=f'Created membership plan: {name}',
                    request=request
                )
                messages.success(request, f'Membership plan "{name}" created successfully!')
            else:
                pass_obj = FlexibleAccess.objects.create(
                    name=name,
                    duration_days=duration_days,
                    price=price,
                    description=description
                )
                AuditLog.log(
                    action='plan_created',
                    user=request.user,
                    description=f'Created walk-in pass: {name}',
                    request=request
                )
                messages.success(request, f'Walk-in pass "{name}" created successfully!')

            # Clear chatbot cache when plans are modified
            GymChatbot.clear_cache()
        
        elif action == 'edit':
            name = request.POST.get('name')
            duration_days = request.POST.get('duration_days')
            price = request.POST.get('price')
            description = request.POST.get('description', '')

            if plan_type == 'membership':
                plan = get_object_or_404(MembershipPlan, id=plan_id)
                plan.name = name
                plan.duration_days = duration_days
                plan.price = price
                plan.description = description
                plan.save()
                AuditLog.log(
                    action='plan_updated',
                    user=request.user,
                    description=f'Updated membership plan: {name}',
                    request=request
                )
                messages.success(request, f'Membership plan "{name}" updated successfully!')
            else:
                pass_obj = get_object_or_404(FlexibleAccess, id=plan_id)
                pass_obj.name = name
                pass_obj.duration_days = duration_days
                pass_obj.price = price
                pass_obj.description = description
                pass_obj.save()
                AuditLog.log(
                    action='plan_updated',
                    user=request.user,
                    description=f'Updated walk-in pass: {name}',
                    request=request
                )
                messages.success(request, f'Walk-in pass "{name}" updated successfully!')

            # Clear chatbot cache when plans are modified
            GymChatbot.clear_cache()
        
        elif action == 'toggle':
            if plan_type == 'membership':
                plan = get_object_or_404(MembershipPlan, id=plan_id)
                plan.is_active = not plan.is_active
                plan.save()
                status = 'activated' if plan.is_active else 'deactivated'
                AuditLog.log(
                    action='plan_updated',
                    user=request.user,
                    description=f'Plan "{plan.name}" {status}',
                    request=request
                )
                messages.success(request, f'Plan "{plan.name}" {status}!')
            else:
                pass_obj = get_object_or_404(FlexibleAccess, id=plan_id)
                pass_obj.is_active = not pass_obj.is_active
                pass_obj.save()
                status = 'activated' if pass_obj.is_active else 'deactivated'
                AuditLog.log(
                    action='plan_updated',
                    user=request.user,
                    description=f'Pass "{pass_obj.name}" {status}',
                    request=request
                )
                messages.success(request, f'Pass "{pass_obj.name}" {status}!')

            # Clear chatbot cache when plans are modified
            GymChatbot.clear_cache()
        
        elif action == 'delete':
            if not request.user.is_admin():
                messages.error(request, 'Only admins can delete plans.')
                return redirect('manage_plans')

            if plan_type == 'membership':
                plan = get_object_or_404(MembershipPlan, id=plan_id)
                plan_name = plan.name
                plan.delete()
                AuditLog.log(
                    action='plan_deleted',
                    user=request.user,
                    description=f'Deleted membership plan: {plan_name}',
                    severity='warning',
                    request=request
                )
                messages.success(request, f'Plan "{plan_name}" deleted!')
            else:
                pass_obj = get_object_or_404(FlexibleAccess, id=plan_id)
                pass_name = pass_obj.name
                pass_obj.delete()
                AuditLog.log(
                    action='plan_deleted',
                    user=request.user,
                    description=f'Deleted walk-in pass: {pass_name}',
                    severity='warning',
                    request=request
                )
                messages.success(request, f'Pass "{pass_name}" deleted!')

            # Clear chatbot cache when plans are modified
            GymChatbot.clear_cache()

        return redirect('manage_plans')
    
    context = {
        'membership_plans': MembershipPlan.objects.all().order_by('-duration_days'),
        'walkin_passes': FlexibleAccess.objects.all().order_by('duration_days'),
    }
    
    return render(request, 'gym_app/manage_plans.html', context)


# Add these views to gym_app/views.py

from .models import Attendance
from django.db.models import Q

# ==================== Kiosk Views ====================


def kiosk_login(request):
    """Kiosk login page - PIN-based authentication"""
    if request.method == 'POST':
        kiosk_pin = request.POST.get('kiosk_pin', '').strip()
        
        # Validate PIN format
        if not kiosk_pin or len(kiosk_pin) != 6 or not kiosk_pin.isdigit():
            AuditLog.log(
                action='login_failed',
                description=f'Invalid PIN format attempted: {kiosk_pin}',
                severity='warning',
                request=request
            )
            messages.error(request, 'Invalid PIN. Please enter a 6-digit PIN.')
            return render(request, 'gym_app/kiosk_login.html')
        
        # Find user by PIN
        try:
            user = User.objects.get(kiosk_pin=kiosk_pin, role='member')
        except User.DoesNotExist:
            # Log failed attempt
            AuditLog.log(
                action='login_failed',
                description=f'Kiosk access denied - Invalid PIN: {kiosk_pin}',
                severity='warning',
                request=request
            )
            messages.error(request, 'Invalid PIN. Please check your PIN and try again.')
            return render(request, 'gym_app/kiosk_login.html')
        
        # Check if user has active membership
        active_membership = UserMembership.objects.filter(
            user=user,
            status='active',
            end_date__gte=date.today()
        ).first()
        
        if not active_membership:
            # Log failed check-in attempt
            AuditLog.log(
                action='permission_denied',
                user=user,
                description=f'Check-in denied - No active membership (PIN: {kiosk_pin})',
                severity='warning',
                request=request
            )
            messages.error(
                request, 
                f'Hi {user.first_name}! Your membership has expired. Please renew to access the gym.'
            )
            return render(request, 'gym_app/kiosk_login.html')
        
        # Check if user is already checked in
        current_checkin = Attendance.objects.filter(
            user=user,
            check_out__isnull=True
        ).first()
        
        if current_checkin:
            # User is checking out
            current_checkin.check_out = timezone.now()
            current_checkin.save()
            
            # Log check-out
            AuditLog.log(
                action='user_updated',
                user=user,
                description=f'Checked out via PIN - Duration: {current_checkin.get_duration_display()}',
                severity='info',
                request=request,
                model_name='Attendance',
                object_id=current_checkin.id,
                duration=current_checkin.duration_minutes
            )
            
            return redirect('kiosk_success', 
                          action='checkout', 
                          duration=current_checkin.duration_minutes,
                          user_id=user.id)
        else:
            # User is checking in
            attendance = Attendance.objects.create(user=user)
            
            # Log check-in
            AuditLog.log(
                action='user_updated',
                user=user,
                description=f'Checked in via PIN to gym',
                severity='info',
                request=request,
                model_name='Attendance',
                object_id=attendance.id
            )
            
            return redirect('kiosk_success', 
                          action='checkin', 
                          duration=0,
                          user_id=user.id)
    
    return render(request, 'gym_app/kiosk_login.html')


def kiosk_success(request, action, duration, user_id):
    """Success page after check-in/check-out"""
    user = get_object_or_404(User, id=user_id)
    
    context = {
        'action': action,
        'duration': duration,
        'user': user,
        'now': timezone.now(),
    }
    return render(request, 'gym_app/kiosk_success.html', context)
@login_required
def attendance_report(request):
    """View attendance reports (admin/staff only)"""
    if not request.user.is_staff_or_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Filters
    date_filter = request.GET.get('date', '')
    user_filter = request.GET.get('user', '')
    status_filter = request.GET.get('status', '')
    
    # Base query
    attendances = Attendance.objects.select_related('user').all()
    
    # Apply filters
    if date_filter:
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            attendances = attendances.filter(check_in__date=filter_date)
        except ValueError:
            pass
    
    if user_filter:
        attendances = attendances.filter(
            Q(user__username__icontains=user_filter) |
            Q(user__first_name__icontains=user_filter) |
            Q(user__last_name__icontains=user_filter)
        )
    
    if status_filter == 'in':
        attendances = attendances.filter(check_out__isnull=True)
    elif status_filter == 'out':
        attendances = attendances.filter(check_out__isnull=False)
    
    # Get currently checked in members
    currently_checked_in = Attendance.objects.filter(
        check_out__isnull=True
    ).select_related('user').count()
    
    # Today's total check-ins
    today_checkins = Attendance.objects.filter(
        check_in__date=date.today()
    ).count()
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(attendances, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'date_filter': date_filter,
        'user_filter': user_filter,
        'status_filter': status_filter,
        'currently_checked_in': currently_checked_in,
        'today_checkins': today_checkins,
    }
    
    return render(request, 'gym_app/attendance_report.html', context)

# Add these imports at the top of gym_app/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .chatbot import GymChatbot

# Add these URL patterns to gym_app/urls.py urlpatterns list:
# path('chatbot/', views.chatbot_view, name='chatbot'),
# path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
# path('api/chatbot/suggestions/', views.chatbot_suggestions, name='chatbot_suggestions'),

# Add these views to gym_app/views.py

@login_required
def chatbot_view(request):
    """Chatbot interface page"""
    return render(request, 'gym_app/chatbot.html')


@csrf_exempt
def chatbot_api(request):
    """
    Optimized API endpoint for chatbot with faster response times
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')

        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)

        # Initialize chatbot
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key if not user else None

        if not user and not session_key:
            request.session.create()
            session_key = request.session.session_key

        chatbot = GymChatbot(user=user, conversation_id=conversation_id, session_key=session_key)

        # Get response (now optimized for speed)
        result = chatbot.chat(user_message)

        # Add quick suggestions
        if result['success']:
            result['suggestions'] = chatbot.get_quick_suggestions()

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'response': 'An error occurred. Please try again.'
        }, status=500)
    
    
def chatbot_suggestions(request):
    """Get quick reply suggestions based on user context"""
    user = request.user if request.user.is_authenticated else None
    chatbot = GymChatbot(user=user)
    suggestions = chatbot.get_quick_suggestions()

    return JsonResponse({
        'success': True,
        'suggestions': suggestions
    })


# ==================== Chatbot Configuration Management ====================

@login_required
def chatbot_conversations_list(request):
    """List user's conversation history"""
    from .models import Conversation

    if request.user.is_admin():
        # Admin can see all conversations
        conversations = Conversation.objects.all()[:50]
    else:
        # Users see only their own
        conversations = Conversation.objects.filter(user=request.user)[:50]

    conversations_data = []
    for conv in conversations:
        conversations_data.append({
            'id': conv.conversation_id,
            'title': conv.title or 'Untitled',
            'model': conv.model_used,
            'created_at': conv.created_at.isoformat(),
            'updated_at': conv.updated_at.isoformat(),
            'message_count': conv.messages.count(),
            'user': conv.user.username if conv.user else 'Anonymous'
        })

    return JsonResponse({
        'success': True,
        'conversations': conversations_data
    })


# ==================== Pending Payments Management ====================

@login_required
def pending_payments_view(request):
    """View and manage pending membership payments (Staff/Admin only)"""
    if not request.user.is_staff_or_admin():
        messages.error(request, 'Access denied. Staff/Admin only.')
        return redirect('dashboard')

    # Get all pending payments
    pending_payments = Payment.objects.filter(
        status='pending'
    ).select_related('user', 'membership__plan').order_by('-payment_date')

    context = {
        'pending_payments': pending_payments,
    }

    return render(request, 'gym_app/pending_payments.html', context)


@login_required
def confirm_payment(request, payment_id):
    """Confirm a pending payment (Staff/Admin only)"""
    if not request.user.is_staff_or_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    payment = get_object_or_404(Payment, id=payment_id, status='pending')

    if request.method == 'POST':
        # Confirm payment
        payment.confirm(request.user)

        # Generate kiosk PIN if user doesn't have one
        if not payment.user.kiosk_pin:
            payment.user.generate_kiosk_pin()

        # Log confirmation
        AuditLog.log(
            action='payment_received',
            user=request.user,
            description=f'Payment confirmed for {payment.user.get_full_name()} - ₱{payment.amount} (Ref: {payment.reference_no})',
            severity='info',
            request=request,
            model_name='Payment',
            object_id=payment.id,
            object_repr=str(payment)
        )

        messages.success(
            request,
            f'Payment confirmed for {payment.user.get_full_name()}. '
            f'Membership activated. Kiosk PIN: {payment.user.kiosk_pin}'
        )

        return redirect('pending_payments')

    # Generate QR code for GCash payments
    qr_code_data = None
    gcash_merchant_info = None
    if payment.method == 'gcash':
        qr_code_data = generate_gcash_qr_code(payment.amount, payment.reference_no)
        gcash_merchant_info = get_gcash_merchant_info()

    context = {
        'payment': payment,
        'qr_code_data': qr_code_data,
        'gcash_merchant_info': gcash_merchant_info,
    }

    return render(request, 'gym_app/confirm_payment.html', context)


@login_required
def reject_payment(request, payment_id):
    """Reject a pending payment (Staff/Admin only)"""
    if not request.user.is_staff_or_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    payment = get_object_or_404(Payment, id=payment_id, status='pending')

    if request.method == 'POST':
        reason = request.POST.get('reason', '')

        # Reject payment
        payment.reject(request.user, reason)

        # Log rejection
        AuditLog.log(
            action='payment_refunded',
            user=request.user,
            description=f'Payment rejected for {payment.user.get_full_name()} - ₱{payment.amount} (Ref: {payment.reference_no}). Reason: {reason}',
            severity='warning',
            request=request,
            model_name='Payment',
            object_id=payment.id,
            object_repr=str(payment)
        )

        messages.success(request, f'Payment rejected for {payment.user.get_full_name()}.')

        return redirect('pending_payments')

    context = {
        'payment': payment,
    }

    return render(request, 'gym_app/reject_payment.html', context)


# ==================== Archived Plans Management ====================

@login_required
def archived_plans_view(request):
    """View archived plans (Admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')

    archived_memberships = MembershipPlan.objects.filter(
        is_archived=True
    ).select_related('archived_by').order_by('-archived_at')

    archived_walkin = FlexibleAccess.objects.filter(
        is_archived=True
    ).select_related('archived_by').order_by('-archived_at')

    context = {
        'archived_memberships': archived_memberships,
        'archived_walkin': archived_walkin,
    }

    return render(request, 'gym_app/archived_plans.html', context)


@login_required
def archive_membership_plan(request, plan_id):
    """Archive a membership plan (Admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    plan = get_object_or_404(MembershipPlan, id=plan_id)

    plan.archive(request.user)

    AuditLog.log(
        action='plan_updated',
        user=request.user,
        description=f'Archived membership plan: {plan.name}',
        severity='info',
        request=request
    )

    messages.success(request, f'Membership plan "{plan.name}" archived successfully.')

    return redirect('manage_plans')


@login_required
def archive_walkin_plan(request, plan_id):
    """Archive a walk-in plan (Admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    plan = get_object_or_404(FlexibleAccess, id=plan_id)

    plan.archive(request.user)

    AuditLog.log(
        action='plan_updated',
        user=request.user,
        description=f'Archived walk-in plan: {plan.name}',
        severity='info',
        request=request
    )

    messages.success(request, f'Walk-in plan "{plan.name}" archived successfully.')

    return redirect('manage_plans')


@login_required
def restore_membership_plan(request, plan_id):
    """Restore an archived membership plan (Admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    plan = get_object_or_404(MembershipPlan, id=plan_id, is_archived=True)

    plan.restore()

    AuditLog.log(
        action='plan_updated',
        user=request.user,
        description=f'Restored membership plan: {plan.name}',
        severity='info',
        request=request
    )

    messages.success(request, f'Membership plan "{plan.name}" restored successfully.')

    return redirect('archived_plans')


@login_required
def restore_walkin_plan(request, plan_id):
    """Restore an archived walk-in plan (Admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    plan = get_object_or_404(FlexibleAccess, id=plan_id, is_archived=True)

    plan.restore()

    AuditLog.log(
        action='plan_updated',
        user=request.user,
        description=f'Restored walk-in plan: {plan.name}',
        severity='info',
        request=request
    )

    messages.success(request, f'Walk-in plan "{plan.name}" restored successfully.')

    return redirect('archived_plans')


# ==================== Profile Settings ====================

@login_required
def profile_settings(request):
    """User profile settings"""
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action', 'update_profile')

        if action == 'update_profile':
            # Update profile information
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.mobile_no = request.POST.get('mobile_no', user.mobile_no)
            user.address = request.POST.get('address', user.address)

            birthdate_str = request.POST.get('birthdate')
            if birthdate_str:
                try:
                    from datetime import datetime
                    user.birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'Invalid birthdate format.')
                    return redirect('profile_settings')

            user.save()

            AuditLog.log(
                action='user_updated',
                user=user,
                description=f'Profile updated by {user.get_full_name()}',
                severity='info',
                request=request
            )

            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_settings')

        elif action == 'update_profile_picture':
            # Handle profile picture upload
            profile_image = request.FILES.get('profile_image')

            if profile_image:
                # Delete old profile image if exists
                if user.profile_image:
                    old_image_path = user.profile_image.path
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)

                # Save new profile image
                user.profile_image = profile_image
                user.save()

                AuditLog.log(
                    action='profile_picture_updated',
                    user=user,
                    description=f'Profile picture updated by {user.get_full_name()}',
                    severity='info',
                    request=request
                )

                messages.success(request, 'Profile picture updated successfully!')
            else:
                messages.error(request, 'Please select an image file.')

            return redirect('profile_settings')

        elif action == 'remove_profile_picture':
            # Remove profile picture
            if user.profile_image:
                old_image_path = user.profile_image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

                user.profile_image = None
                user.save()

                AuditLog.log(
                    action='profile_picture_removed',
                    user=user,
                    description=f'Profile picture removed by {user.get_full_name()}',
                    severity='info',
                    request=request
                )

                messages.success(request, 'Profile picture removed successfully!')
            else:
                messages.error(request, 'No profile picture to remove.')

            return redirect('profile_settings')

    # Get recent login activity
    recent_logins = LoginActivity.get_recent_activity(user, limit=10)

    # Determine which base template to use based on user role
    # Admin and staff get the left sidebar, members get the top navbar
    if user.role in ['admin', 'staff']:
        base_template = 'gym_app/base_sidebar.html'
    else:
        base_template = 'gym_app/base.html'

    context = {
        'user': user,
        'recent_logins': recent_logins,
        'base_template': base_template,
    }

    return render(request, 'gym_app/profile_settings.html', context)


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validate current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('change_password')

        # Validate new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')

        # Validate password strength (optional)
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('change_password')

        # Update password
        request.user.set_password(new_password)
        request.user.save()

        # Log password change
        AuditLog.log(
            action='password_changed',
            user=request.user,
            description=f'Password changed by {request.user.username}',
            severity='warning',
            request=request
        )

        # Update session to prevent logout
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)

        messages.success(request, 'Password changed successfully!')
        return redirect('profile_settings')

    return render(request, 'gym_app/change_password.html')


# ==================== Hero Section Management (Admin) ====================

@login_required
def manage_hero_sections(request):
    """Manage hero sections for homepage (admin only)"""
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("dashboard")

    hero_sections = HeroSection.objects.all().order_by("display_order", "-created_at")
    
    context = {
        "hero_sections": hero_sections,
    }
    return render(request, "gym_app/manage_hero_sections.html", context)


@login_required
def create_hero_section(request):
    """Create new hero section (admin only)"""
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("dashboard")

    if request.method == "POST":
        title = request.POST.get("title")
        subtitle = request.POST.get("subtitle")
        description = request.POST.get("description")
        background_image = request.FILES.get("background_image")
        mobile_image = request.FILES.get("mobile_image")
        cta_primary_text = request.POST.get("cta_primary_text", "Join Now")
        cta_primary_link = request.POST.get("cta_primary_link", "/register/")
        cta_secondary_text = request.POST.get("cta_secondary_text")
        cta_secondary_link = request.POST.get("cta_secondary_link")
        is_active = request.POST.get("is_active") == "on"
        display_order = request.POST.get("display_order", 0)
        overlay_opacity = request.POST.get("overlay_opacity", "0.50")

        if not title or not background_image:
            messages.error(request, "Title and background image are required.")
            return redirect("create_hero_section")

        hero_section = HeroSection.objects.create(
            title=title,
            subtitle=subtitle,
            description=description,
            background_image=background_image,
            mobile_image=mobile_image,
            cta_primary_text=cta_primary_text,
            cta_primary_link=cta_primary_link,
            cta_secondary_text=cta_secondary_text,
            cta_secondary_link=cta_secondary_link,
            is_active=is_active,
            display_order=display_order,
            overlay_opacity=overlay_opacity,
            created_by=request.user
        )

        messages.success(request, f"Hero section \"{title}\" created successfully!")
        return redirect("manage_hero_sections")

    return render(request, "gym_app/create_hero_section.html")


@login_required
def edit_hero_section(request, section_id):
    """Edit hero section (admin only)"""
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("dashboard")

    hero_section = get_object_or_404(HeroSection, id=section_id)

    if request.method == "POST":
        hero_section.title = request.POST.get("title", hero_section.title)
        hero_section.subtitle = request.POST.get("subtitle", hero_section.subtitle)
        hero_section.description = request.POST.get("description", hero_section.description)
        hero_section.cta_primary_text = request.POST.get("cta_primary_text", hero_section.cta_primary_text)
        hero_section.cta_primary_link = request.POST.get("cta_primary_link", hero_section.cta_primary_link)
        hero_section.cta_secondary_text = request.POST.get("cta_secondary_text")
        hero_section.cta_secondary_link = request.POST.get("cta_secondary_link")
        hero_section.is_active = request.POST.get("is_active") == "on"
        hero_section.display_order = request.POST.get("display_order", hero_section.display_order)
        hero_section.overlay_opacity = request.POST.get("overlay_opacity", hero_section.overlay_opacity)

        # Handle image uploads
        if request.FILES.get("background_image"):
            if hero_section.background_image:
                old_path = hero_section.background_image.path
                if os.path.exists(old_path):
                    os.remove(old_path)
            hero_section.background_image = request.FILES.get("background_image")

        if request.FILES.get("mobile_image"):
            if hero_section.mobile_image:
                old_path = hero_section.mobile_image.path
                if os.path.exists(old_path):
                    os.remove(old_path)
            hero_section.mobile_image = request.FILES.get("mobile_image")

        hero_section.save()

        messages.success(request, f"Hero section \"{hero_section.title}\" updated successfully!")
        return redirect("manage_hero_sections")

    context = {
        "hero_section": hero_section,
    }
    return render(request, "gym_app/edit_hero_section.html", context)


@login_required
def delete_hero_section(request, section_id):
    """Delete hero section (admin only)"""
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("dashboard")

    hero_section = get_object_or_404(HeroSection, id=section_id)

    if request.method == "POST":
        # Delete associated images
        if hero_section.background_image:
            if os.path.exists(hero_section.background_image.path):
                os.remove(hero_section.background_image.path)
        if hero_section.mobile_image:
            if os.path.exists(hero_section.mobile_image.path):
                os.remove(hero_section.mobile_image.path)

        title = hero_section.title
        hero_section.delete()

        messages.success(request, f"Hero section \"{title}\" deleted successfully!")
        return redirect("manage_hero_sections")

    context = {
        "hero_section": hero_section,
    }
    return render(request, "gym_app/delete_hero_section.html", context)


# ==================== Gallery Management (Admin) ====================

@login_required
def manage_gallery(request):
    """Manage gym gallery (admin only)"""
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("dashboard")

    gallery_images = GymGallery.objects.all().order_by("display_order", "-created_at")
    
    context = {
        "gallery_images": gallery_images,
    }
    return render(request, "gym_app/manage_gallery.html", context)


@login_required
def upload_gallery_image(request):
    """Upload new gallery image (admin only)"""
    if not request.user.is_admin():
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("dashboard")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        image = request.FILES.get("image")
        category = request.POST.get("category", "facility")
        is_featured = request.POST.get("is_featured") == "on"
        is_active = request.POST.get("is_active", "on") == "on"
        display_order = request.POST.get("display_order", 0)

        if not title or not image:
            messages.error(request, "Title and image are required.")
            return redirect("upload_gallery_image")

        gallery_image = GymGallery.objects.create(
            title=title,
            description=description,
            image=image,
            category=category,
            is_featured=is_featured,
            is_active=is_active,
            display_order=display_order,
            uploaded_by=request.user
        )

        messages.success(request, f"Gallery image \"{title}\" uploaded successfully!")
        return redirect("manage_gallery")

    return render(request, "gym_app/upload_gallery_image.html")
