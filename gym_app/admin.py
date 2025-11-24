from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, MembershipPlan, FlexibleAccess, UserMembership, Payment, WalkInPayment,
    Analytics, Attendance, Conversation, ConversationMessage
)
from .models import AuditLog

# Update the UserAdmin in gym_app/admin.py
# Replace the entire UserAdmin class

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with additional fields"""
    
    list_display = ['username', 'email', 'get_full_name', 'role', 'kiosk_pin', 'is_superuser', 'is_staff', 'age', 'mobile_no', 'is_active']
    list_filter = ['role', 'is_superuser', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'mobile_no', 'kiosk_pin']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Permissions', {
            'fields': ('role',),
            'description': 'Note: Superusers are automatically assigned admin role'
        }),
        ('Kiosk Access', {
            'fields': ('kiosk_pin',),
            'description': '6-digit PIN for kiosk check-in/out. Leave blank to auto-generate.'
        }),
        ('Additional Info', {
            'fields': ('mobile_no', 'address', 'birthdate', 'age')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Assignment', {
            'fields': ('role',),
        }),
        ('Additional Info', {
            'fields': ('mobile_no', 'address', 'birthdate', 'email', 'first_name', 'last_name')
        }),
    )
    
    readonly_fields = ['age', 'date_joined', 'last_login']
    
    actions = ['generate_pins_action']
    
    def save_model(self, request, obj, form, change):
        """Override save to sync role with Django permissions"""
        # If making someone a superuser, make them admin
        if obj.is_superuser:
            obj.role = 'admin'
        # If making someone staff (but not superuser), make them staff role
        elif obj.is_staff and obj.role == 'member':
            obj.role = 'staff'
        
        super().save_model(request, obj, form, change)
    
    def generate_pins_action(self, request, queryset):
        """Generate PINs for selected users"""
        count = 0
        for user in queryset:
            if user.role == 'member' and not user.kiosk_pin:
                user.generate_kiosk_pin()
                count += 1
        
        self.message_user(request, f'Generated PINs for {count} member(s)')
    generate_pins_action.short_description = 'Generate Kiosk PINs for selected members'

@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    """Admin interface for Membership Plans"""
    
    list_display = ['name', 'duration_days', 'price', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['price']
    
    fieldsets = (
        ('Plan Details', {
            'fields': ('name', 'duration_days', 'price', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(FlexibleAccess)
class FlexibleAccessAdmin(admin.ModelAdmin):
    """Admin interface for Walk-in Passes"""
    
    list_display = ['name', 'duration_days', 'price', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['duration_days']
    
    fieldsets = (
        ('Pass Details', {
            'fields': ('name', 'duration_days', 'price', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    """Admin interface for User Memberships"""
    
    list_display = ['user', 'plan', 'start_date', 'end_date', 'status', 'days_remaining', 'cancelled_display']
    list_filter = ['status', 'start_date', 'end_date', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at', 'cancelled_at']
    
    fieldsets = (
        ('Membership Details', {
            'fields': ('user', 'plan', 'start_date', 'end_date', 'status')
        }),
        ('Cancellation Info', {
            'fields': ('cancelled_by', 'cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',),
            'description': 'Shows cancellation details if membership was cancelled'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['cancel_memberships_action', 'reactivate_memberships_action']
    
    def days_remaining(self, obj):
        """Display days remaining in membership"""
        days = obj.days_remaining()
        if days > 0:
            return f"{days} days"
        return "Expired"
    days_remaining.short_description = 'Days Left'
    
    def cancelled_display(self, obj):
        """Display cancellation status"""
        if obj.status == 'cancelled':
            return f"<i class='fas fa-check-circle' style='color: red;'></i> Cancelled"
        return "-"
    cancelled_display.short_description = 'Cancelled'
    cancelled_display.allow_tags = True
    
    def cancel_memberships_action(self, request, queryset):
        """Admin action to cancel memberships"""
        count = 0
        for membership in queryset:
            if membership.status == 'active':
                membership.cancel(user=request.user, reason='Cancelled by admin')
                count += 1
        
        self.message_user(request, f'Cancelled {count} membership(s)')
    cancel_memberships_action.short_description = 'Cancel selected memberships'
    
    def reactivate_memberships_action(self, request, queryset):
        """Admin action to reactivate cancelled memberships"""
        count = 0
        for membership in queryset:
            if membership.status == 'cancelled':
                membership.status = 'active'
                membership.cancelled_at = None
                membership.cancelled_by = None
                membership.cancellation_reason = ''
                membership.save()
                count += 1
        
        self.message_user(request, f'Reactivated {count} membership(s)')
    reactivate_memberships_action.short_description = 'Reactivate selected memberships'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Member Payments"""
    
    list_display = ['user', 'amount', 'method', 'payment_date', 'reference_no', 'membership']
    list_filter = ['method', 'payment_date']
    search_fields = ['user__username', 'user__email', 'reference_no', 'user__first_name', 'user__last_name']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('user', 'membership', 'amount', 'method', 'payment_date')
        }),
        ('Additional Info', {
            'fields': ('reference_no', 'notes')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WalkInPayment)
class WalkInPaymentAdmin(admin.ModelAdmin):
    """Admin interface for Walk-in Payments"""
    
    list_display = ['customer_name', 'pass_type', 'amount', 'method', 'payment_date', 'mobile_no']
    list_filter = ['method', 'payment_date', 'pass_type']
    search_fields = ['customer_name', 'mobile_no', 'reference_no']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Customer Info', {
            'fields': ('customer_name', 'mobile_no')
        }),
        ('Payment Details', {
            'fields': ('pass_type', 'amount', 'method', 'payment_date')
        }),
        ('Additional Info', {
            'fields': ('reference_no', 'notes')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for Analytics"""
    
    list_display = ['date', 'total_members', 'total_passes', 'total_sales', 'age_group']
    list_filter = ['date']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Report Date', {
            'fields': ('date',)
        }),
        ('Metrics', {
            'fields': ('total_members', 'total_passes', 'total_sales', 'age_group')
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual addition - analytics should be auto-generated"""
        return False


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin interface for Attendance tracking"""
    
    list_display = ['user', 'check_in', 'check_out', 'duration_display', 'status']
    list_filter = ['check_in', 'check_out']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    date_hierarchy = 'check_in'
    
    fieldsets = (
        ('Member', {
            'fields': ('user',)
        }),
        ('Time', {
            'fields': ('check_in', 'check_out', 'duration_minutes')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ['duration_minutes', 'check_in']
    
    def duration_display(self, obj):
        """Display duration in human-readable format"""
        return obj.get_duration_display()
    duration_display.short_description = 'Duration'
    
    def status(self, obj):
        """Display check-in status"""
        if obj.is_checked_in():
            return "🟢 Checked In"
        return "🔴 Checked Out"
    status.short_description = 'Status'




@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface for Chatbot Conversations"""

    list_display = ['conversation_id', 'user_display', 'title', 'model_used', 'message_count', 'created_at', 'updated_at']
    list_filter = ['model_used', 'created_at', 'updated_at']
    search_fields = ['conversation_id', 'title', 'user__username', 'user__email', 'session_key']
    date_hierarchy = 'created_at'
    readonly_fields = ['conversation_id', 'created_at', 'updated_at']

    fieldsets = (
        ('Conversation Info', {
            'fields': ('conversation_id', 'user', 'title', 'model_used')
        }),
        ('Session', {
            'fields': ('session_key',),
            'description': 'Session key for anonymous users'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def user_display(self, obj):
        """Display user or session info"""
        if obj.user:
            return f"{obj.user.username} ({obj.user.get_full_name()})"
        return f"Anonymous ({obj.session_key[:8]}...)" if obj.session_key else "Anonymous"
    user_display.short_description = 'User'

    def message_count(self, obj):
        """Count messages in conversation"""
        return obj.messages.count()
    message_count.short_description = '# Messages'


@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    """Admin interface for Conversation Messages"""

    list_display = ['id', 'conversation_link', 'role', 'content_preview', 'response_time_display', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['conversation__conversation_id', 'content']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

    fieldsets = (
        ('Message Info', {
            'fields': ('conversation', 'role', 'content')
        }),
        ('Performance', {
            'fields': ('tokens_used', 'response_time_ms'),
            'description': 'Performance metrics for assistant responses'
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )

    def conversation_link(self, obj):
        """Link to parent conversation"""
        return obj.conversation.conversation_id[:16] + "..."
    conversation_link.short_description = 'Conversation'

    def content_preview(self, obj):
        """Show preview of message content"""
        return obj.content[:80] + "..." if len(obj.content) > 80 else obj.content
    content_preview.short_description = 'Content'

    def response_time_display(self, obj):
        """Display response time in readable format"""
        if obj.response_time_ms:
            if obj.response_time_ms >= 1000:
                return f"{obj.response_time_ms / 1000:.2f}s"
            return f"{obj.response_time_ms}ms"
        return "-"
    response_time_display.short_description = 'Response Time'






# Customize admin site headers
admin.site.site_header = "Gym Management System"
admin.site.site_title = "Gym Admin"
admin.site.index_title = "Welcome to Gym Management System"


