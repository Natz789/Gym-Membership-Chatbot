from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal


class User(AbstractUser):
    """Custom User model with role-based access and demographics"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('member', 'Member'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    mobile_no = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        help_text="Profile picture"
    )


    kiosk_pin = models.CharField(
        max_length=6, 
        blank=True, 
        null=True, 
        unique=True,
        help_text="6-digit PIN for kiosk check-in/out",
        verbose_name="Kiosk PIN"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def save(self, *args, **kwargs):
        """Auto-calculate age from birthdate before saving"""
        # Auto-assign admin role to superusers
        if self.is_superuser and self.role != 'admin':
            self.role = 'admin'
        
        # Auto-assign staff role to staff users (if not already admin)
        if self.is_staff and self.role == 'member' and not self.is_superuser:
            self.role = 'staff'
        
        if self.birthdate:
            # Handle both date objects and string inputs
            if isinstance(self.birthdate, str):
                from datetime import datetime
                try:
                    self.birthdate = datetime.strptime(self.birthdate, '%Y-%m-%d').date()
                except ValueError:
                    self.birthdate = None
            
            if self.birthdate:
                today = date.today()
                self.age = today.year - self.birthdate.year - (
                    (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
                )
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    def is_admin(self):
        """Check if user is admin (includes superusers)"""
        return self.role == 'admin' or self.is_superuser
    
    def is_staff_or_admin(self):
        """Check if user is staff or admin"""
        return self.role in ['admin', 'staff'] or self.is_superuser or self.is_staff
      # NEW METHOD - Add this method
    def generate_kiosk_pin(self):
        """Generate a unique 6-digit PIN for kiosk access"""
        import random
        while True:
            pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            if not User.objects.filter(kiosk_pin=pin).exists():
                self.kiosk_pin = pin
                self.save()
                return pin
    
    # NEW METHOD - Add this method
    def has_kiosk_access(self):
        """Check if user has kiosk access (active membership)"""
        if self.role != 'member':
            return False
        
        active_membership = UserMembership.objects.filter(
            user=self,
            status='active',
            end_date__gte=date.today()
        ).first()
        
        return active_membership is not None

class MembershipPlan(models.Model):
    """Permanent membership plans (monthly, yearly, etc.)"""

    name = models.CharField(max_length=100)
    duration_days = models.IntegerField(help_text="Duration in days")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False, help_text="Archived plans are hidden but preserved for records")
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_membership_plans'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'membership_plans'
        verbose_name = 'Membership Plan'
        verbose_name_plural = 'Membership Plans'
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - ₱{self.price} ({self.duration_days} days)"

    def archive(self, user=None):
        """Archive this plan"""
        self.is_archived = True
        self.is_active = False
        self.archived_at = timezone.now()
        self.archived_by = user
        self.save()

    def restore(self):
        """Restore archived plan"""
        self.is_archived = False
        self.is_active = True
        self.archived_at = None
        self.archived_by = None
        self.save()


class FlexibleAccess(models.Model):
    """Walk-in passes (1-day, 3-day, weekly, etc.)"""

    name = models.CharField(max_length=100)
    duration_days = models.IntegerField(help_text="Validity in days")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False, help_text="Archived passes are hidden but preserved for records")
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_walk_in_plans'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'flexible_access'
        verbose_name = 'Flexible Access Pass'
        verbose_name_plural = 'Flexible Access Passes'
        ordering = ['duration_days']

    def __str__(self):
        return f"{self.name} - ₱{self.price} ({self.duration_days} days)"

    def archive(self, user=None):
        """Archive this pass"""
        self.is_archived = True
        self.is_active = False
        self.archived_at = timezone.now()
        self.archived_by = user
        self.save()

    def restore(self):
        """Restore archived pass"""
        self.is_archived = False
        self.is_active = True
        self.archived_at = None
        self.archived_by = None
        self.save()


class UserMembership(models.Model):
    """Tracks member subscriptions to plans"""

    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT, related_name='subscriptions')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
     # NEW FIELDS FOR CANCELLATION
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_memberships'
    )
    cancellation_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_memberships'
        verbose_name = 'User Membership'
        verbose_name_plural = 'User Memberships'
        ordering = ['-start_date']
    
    def save(self, *args, **kwargs):
        """Auto-calculate end_date based on plan duration"""
        if not self.end_date and self.start_date and self.plan:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        
        # Auto-update status based on dates
        if self.end_date < date.today():
            self.status = 'expired'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.plan.name} ({self.status})"
    
    def is_active(self):
        """Check if membership is currently active"""
        return self.status == 'active' and self.end_date >= date.today()
    
    def days_remaining(self):
        """Calculate days remaining in membership"""
        if self.end_date >= date.today():
            return (self.end_date - date.today()).days
        return 0

    def cancel(self, user=None, reason=''):
        """Cancel the membership"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancelled_by = user
        self.cancellation_reason = reason
        self.save()

class Payment(models.Model):
    """Payment records for registered members"""

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    membership = models.ForeignKey(UserMembership, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    payment_date = models.DateTimeField(default=timezone.now)
    reference_no = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="Auto-generated payment reference")
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    # Approval tracking
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_payments'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date']

    def save(self, *args, **kwargs):
        """Generate unique reference number if not set"""
        if not self.reference_no:
            self.reference_no = self.generate_reference_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_reference_number():
        """Generate unique payment reference number (format: PAY-YYYYMMDD-XXXXXX)"""
        import random
        from datetime import datetime

        date_str = datetime.now().strftime('%Y%m%d')
        while True:
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            reference = f"PAY-{date_str}-{random_part}"
            if not Payment.objects.filter(reference_no=reference).exists():
                return reference

    def confirm(self, user):
        """Confirm payment and activate membership"""
        self.status = 'confirmed'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()

        # Activate membership
        if self.membership:
            self.membership.status = 'active'
            self.membership.save()

    def reject(self, user, reason=''):
        """Reject payment"""
        self.status = 'rejected'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()

        # Cancel membership if rejected
        if self.membership:
            self.membership.status = 'cancelled'
            self.membership.save()

    def __str__(self):
        return f"{self.user.get_full_name()} - ₱{self.amount} ({self.reference_no})"


class WalkInPayment(models.Model):
    """Payment records for walk-in clients (no account required)"""

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
    ]

    pass_type = models.ForeignKey(FlexibleAccess, on_delete=models.PROTECT, related_name='walk_in_sales')
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    mobile_no = models.CharField(max_length=20, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    payment_date = models.DateTimeField(default=timezone.now)
    reference_no = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="Auto-generated payment reference")
    notes = models.TextField(blank=True, null=True)

    # Track who processed this walk-in sale
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_walkin_sales'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'walk_in_payments'
        verbose_name = 'Walk-in Payment'
        verbose_name_plural = 'Walk-in Payments'
        ordering = ['-payment_date']

    def save(self, *args, **kwargs):
        """Generate unique reference number if not set"""
        if not self.reference_no:
            self.reference_no = self.generate_reference_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_reference_number():
        """Generate unique walk-in payment reference number (format: WLK-YYYYMMDD-XXXXXX)"""
        import random
        from datetime import datetime

        date_str = datetime.now().strftime('%Y%m%d')
        while True:
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            reference = f"WLK-{date_str}-{random_part}"
            if not WalkInPayment.objects.filter(reference_no=reference).exists():
                return reference

    def __str__(self):
        customer = self.customer_name if self.customer_name else "Anonymous"
        return f"{customer} - {self.pass_type.name} - ₱{self.amount} ({self.reference_no})"


class Analytics(models.Model):
    """Daily/weekly aggregated data for dashboard"""
    
    date = models.DateField(unique=True)
    total_members = models.IntegerField(default=0)
    total_passes = models.IntegerField(default=0)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    age_group = models.CharField(max_length=20, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics'
        verbose_name = 'Analytics'
        verbose_name_plural = 'Analytics'
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.date}"
    
    @classmethod
    def generate_daily_report(cls, target_date=None):
        """Generate analytics for a specific date"""
        if target_date is None:
            target_date = date.today()
        
        # Count active memberships
        active_members = UserMembership.objects.filter(
            status='active',
            start_date__lte=target_date,
            end_date__gte=target_date
        ).count()
        
        # Count walk-in passes sold on this date
        passes_sold = WalkInPayment.objects.filter(
            payment_date__date=target_date
        ).count()
        
        # Calculate total sales
        member_sales = Payment.objects.filter(
            payment_date__date=target_date
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        walkin_sales = WalkInPayment.objects.filter(
            payment_date__date=target_date
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        total_sales = member_sales + walkin_sales
        
        # Create or update analytics record
        analytics, created = cls.objects.update_or_create(
            date=target_date,
            defaults={
                'total_members': active_members,
                'total_passes': passes_sold,
                'total_sales': total_sales,
            }
        )
        
        return analytics
    
class AuditLog(models.Model):
    """Audit trail for all system activities and transactions"""
    
    ACTION_CHOICES = [
        # Authentication
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('login_failed', 'Login Failed'),
        ('register', 'User Registration'),
        
        # User Management
        ('user_created', 'User Created'),
        ('user_updated', 'User Updated'),
        ('user_deleted', 'User Deleted'),
        ('role_changed', 'Role Changed'),
        
        # Membership
        ('membership_created', 'Membership Created'),
        ('membership_updated', 'Membership Updated'),
        ('membership_cancelled', 'Membership Cancelled'),
        ('membership_expired', 'Membership Expired'),
        
        # Payments
        ('payment_received', 'Payment Received'),
        ('walkin_sale', 'Walk-in Sale'),
        ('payment_refunded', 'Payment Refunded'),
        
        # Plans
        ('plan_created', 'Plan Created'),
        ('plan_updated', 'Plan Updated'),
        ('plan_deleted', 'Plan Deleted'),
        
        # System
        ('data_export', 'Data Exported'),
        ('report_generated', 'Report Generated'),
        ('settings_changed', 'Settings Changed'),
        
        # Security
        ('unauthorized_access', 'Unauthorized Access Attempt'),
        ('password_changed', 'Password Changed'),
        ('permission_denied', 'Permission Denied'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='info')
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Related objects (optional)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    
    # Additional data in JSON format
    extra_data = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {user_str} - {self.get_action_display()}"
    
    @classmethod
    def log(cls, action, user=None, description='', severity='info', 
            request=None, model_name=None, object_id=None, object_repr=None, **extra_data):
        """
        Create an audit log entry
        
        Usage:
            AuditLog.log('login', user=request.user, description='User logged in successfully')
        """
        ip_address = None
        user_agent = None
        
        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            user=user,
            action=action,
            severity=severity,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            model_name=model_name,
            object_id=str(object_id) if object_id else None,
            object_repr=object_repr,
            extra_data=extra_data
        )
    
    @classmethod
    def get_user_activity(cls, user, days=30):
        """Get recent activity for a specific user"""
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
            user=user,
            timestamp__gte=start_date
        )
    
    @classmethod
    def get_security_events(cls, days=7):
        """Get recent security-related events"""
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        security_actions = ['login_failed', 'unauthorized_access', 'permission_denied']
        return cls.objects.filter(
            action__in=security_actions,
            timestamp__gte=start_date
        )
    
    @classmethod
    def get_financial_transactions(cls, start_date=None, end_date=None):
        """Get all financial transaction logs"""
        financial_actions = ['payment_received', 'walkin_sale', 'payment_refunded']
        logs = cls.objects.filter(action__in=financial_actions)
        
        if start_date:
            logs = logs.filter(timestamp__gte=start_date)
        if end_date:
            logs = logs.filter(timestamp__lte=end_date)
        
        return logs
    



    # Add this to gym_app/models.py (at the end, before the last line)

class Attendance(models.Model):
    """Track member check-ins and check-outs"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='attendances'
    )
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'attendance'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        ordering = ['-check_in']
        indexes = [
            models.Index(fields=['-check_in']),
            models.Index(fields=['user', '-check_in']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.check_in.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """Calculate duration if check_out is set"""
        if self.check_out and self.check_in:
            delta = self.check_out - self.check_in
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)
    
    def is_checked_in(self):
        """Check if user is currently checked in"""
        return self.check_out is None
    
    def get_duration_display(self):
        """Get human-readable duration"""
        if not self.duration_minutes:
            return "In progress"

        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


class LoginActivity(models.Model):
    """Track user login activity for security purposes"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_activities'
    )
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'login_activities'
        verbose_name = 'Login Activity'
        verbose_name_plural = 'Login Activities'
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
        ]

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.user.username} - {status} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def record_login(cls, user, request, success=True, failure_reason=None):
        """Record a login attempt"""
        ip_address = None
        user_agent = None

        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        return cls.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )

    @classmethod
    def get_recent_activity(cls, user, limit=10):
        """Get recent login activity for a user"""
        return cls.objects.filter(user=user)[:limit]


class Conversation(models.Model):
    """Persistent conversation storage for chatbot"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='conversations'
    )
    conversation_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique identifier for this conversation"
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Auto-generated conversation title"
    )
    model_used = models.CharField(
        max_length=50,
        help_text="Ollama model used for this conversation"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Session info
    session_key = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Session key for anonymous users"
    )

    class Meta:
        db_table = 'conversations'
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['conversation_id']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else f"Anonymous ({self.session_key[:8]})"
        return f"{user_str} - {self.title or 'Untitled'}"

    def generate_title(self):
        """Generate a title from the first message"""
        first_message = self.messages.filter(role='user').first()
        if first_message:
            # Take first 50 chars of first user message
            self.title = first_message.content[:50] + ('...' if len(first_message.content) > 50 else '')
            self.save()


class ConversationMessage(models.Model):
    """Individual messages in a conversation"""

    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    tokens_used = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Response generation time in milliseconds"
    )

    class Meta:
        db_table = 'conversation_messages'
        verbose_name = 'Conversation Message'
        verbose_name_plural = 'Conversation Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


# ==================== Home Page Hero Section ====================

class HeroSection(models.Model):
    """Hero section for homepage with images and content"""

    title = models.CharField(
        max_length=200,
        help_text="Main headline for the hero section"
    )
    subtitle = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Subheading or tagline"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional detailed description"
    )

    # Images
    background_image = models.ImageField(
        upload_to='hero_images/',
        help_text="Main background image for hero section (Recommended: 1920x1080px)"
    )
    mobile_image = models.ImageField(
        upload_to='hero_images/mobile/',
        blank=True,
        null=True,
        help_text="Optional mobile-optimized image (Recommended: 768x1024px)"
    )

    # Call-to-action buttons
    cta_primary_text = models.CharField(
        max_length=100,
        default="Join Now",
        help_text="Text for primary CTA button"
    )
    cta_primary_link = models.CharField(
        max_length=200,
        default="/register/",
        help_text="URL for primary CTA button"
    )
    cta_secondary_text = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Text for secondary CTA button (optional)"
    )
    cta_secondary_link = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="URL for secondary CTA button"
    )

    # Display settings
    is_active = models.BooleanField(
        default=True,
        help_text="Show this hero section on homepage"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Order of display (lower numbers appear first)"
    )
    overlay_opacity = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.50,
        help_text="Overlay darkness (0.0 = transparent, 1.0 = full black)"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hero_sections_created'
    )

    class Meta:
        db_table = 'hero_sections'
        verbose_name = 'Hero Section'
        verbose_name_plural = 'Hero Sections'
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"


class GymGallery(models.Model):
    """Gallery of gym photos to showcase facilities"""

    CATEGORY_CHOICES = [
        ('equipment', 'Equipment'),
        ('facility', 'Facility'),
        ('classes', 'Classes'),
        ('members', 'Members'),
        ('events', 'Events'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to='gallery/',
        help_text="Gallery image (Recommended: 800x600px)"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='facility'
    )

    is_featured = models.BooleanField(
        default=False,
        help_text="Feature on homepage"
    )
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'gym_gallery'
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.category})"