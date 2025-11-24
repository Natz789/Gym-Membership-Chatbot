"""
Operations Executor for Gym Chatbot
Handles member lookup, staff operations, and administrative tasks
All operations have strict permission checking and audit logging
"""

from django.db.models import Q, Prefetch
from django.utils import timezone
from django.core.cache import cache
from datetime import date, datetime, timedelta
from decimal import Decimal
from .models import (
    User, UserMembership, Payment, WalkInPayment,
    Attendance, MembershipPlan, FlexibleAccess, AuditLog
)
import re


class PermissionError(Exception):
    """Raised when user doesn't have permission for an operation"""
    pass


class OperationsExecutor:
    """
    Execute gym operations via chatbot with permission checks
    All operations are logged for audit trail
    """

    def __init__(self, user):
        """
        Initialize operations executor for a specific user

        Args:
            user: The User object performing the operation
        """
        self.user = user
        self.is_admin = user.is_admin() if user else False
        self.is_staff_or_admin = user.is_staff_or_admin() if user else False

    def _check_permission(self, required_role='staff'):
        """
        Check if user has required permission level

        Args:
            required_role: 'admin' or 'staff'

        Raises:
            PermissionError: If user doesn't have permission
        """
        if required_role == 'admin' and not self.is_admin:
            raise PermissionError("This operation requires admin privileges")
        elif required_role == 'staff' and not self.is_staff_or_admin:
            raise PermissionError("This operation requires staff or admin privileges")

    def _log_operation(self, action, description, severity='info', **extra_data):
        """
        Log operation to audit trail

        Args:
            action: Action type (from AuditLog.ACTION_CHOICES)
            description: Human-readable description
            severity: Severity level (info, warning, error, critical)
            **extra_data: Additional data to log
        """
        AuditLog.log(
            action=action,
            user=self.user,
            description=description,
            severity=severity,
            **extra_data
        )

    # ==================== Member Search and Lookup ====================

    def search_members(self, query):
        """
        Search for members by name, email, or membership ID
        Requires: staff or admin

        Args:
            query: Search string

        Returns:
            List of member dictionaries
        """
        self._check_permission('staff')

        # Build search query (optimized with select_related)
        members = User.objects.filter(
            role='member'
        ).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        ).select_related().prefetch_related(
            Prefetch(
                'memberships',
                queryset=UserMembership.objects.filter(
                    status='active'
                ).select_related('plan')
            )
        )[:10]  # Limit to 10 results for performance

        results = []
        for member in members:
            active_membership = member.memberships.filter(
                status='active',
                end_date__gte=date.today()
            ).first()

            results.append({
                'id': member.id,
                'name': member.get_full_name(),
                'email': member.email,
                'mobile': member.mobile_no,
                'membership_status': 'Active' if active_membership else 'Inactive',
                'membership_plan': active_membership.plan.name if active_membership else None,
                'expiry_date': active_membership.end_date.isoformat() if active_membership else None,
                'days_remaining': active_membership.days_remaining() if active_membership else 0
            })

        self._log_operation(
            'data_export',
            f'Member search performed for query: {query}',
            member_count=len(results)
        )

        return results

    def get_member_details(self, member_identifier):
        """
        Get complete profile for a specific member
        Requires: staff or admin

        Args:
            member_identifier: Member name, email, or ID

        Returns:
            Dictionary with complete member information
        """
        self._check_permission('staff')

        # Try to find member by ID, email, or name
        try:
            if str(member_identifier).isdigit():
                member = User.objects.get(id=int(member_identifier), role='member')
            elif '@' in str(member_identifier):
                member = User.objects.get(email=member_identifier, role='member')
            else:
                # Search by name - handle full names (first + last)
                name_parts = member_identifier.strip().split()

                if len(name_parts) >= 2:
                    # Full name provided (e.g., "Angelina Torres" or "Joshua Reyes")
                    first_name = name_parts[0]
                    last_name = ' '.join(name_parts[1:])  # Handle middle names

                    member = User.objects.filter(
                        role='member',
                        first_name__icontains=first_name,
                        last_name__icontains=last_name
                    ).first()
                else:
                    # Single name provided - search first, last, or username
                    member = User.objects.filter(
                        role='member'
                    ).filter(
                        Q(first_name__icontains=member_identifier) |
                        Q(last_name__icontains=member_identifier) |
                        Q(username=member_identifier)
                    ).first()

                if not member:
                    return {'error': f'Member not found: {member_identifier}'}

        except User.DoesNotExist:
            return {'error': f'Member not found: {member_identifier}'}

        # Get member's memberships (optimized)
        memberships = UserMembership.objects.filter(
            user=member
        ).select_related('plan').order_by('-created_at')

        active_membership = memberships.filter(
            status='active',
            end_date__gte=date.today()
        ).first()

        # Get payment history (optimized)
        payments = Payment.objects.filter(
            user=member
        ).select_related('membership').order_by('-payment_date')[:10]

        # Get attendance history (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        attendance_records = Attendance.objects.filter(
            user=member,
            check_in__gte=thirty_days_ago
        ).order_by('-check_in')[:20]

        result = {
            'id': member.id,
            'personal_info': {
                'name': member.get_full_name(),
                'email': member.email,
                'mobile': member.mobile_no or 'Not provided',
                'address': member.address or 'Not provided',
                'age': member.age,
                'birthdate': member.birthdate.isoformat() if member.birthdate else None,
                'joined_date': member.created_at.date().isoformat()
            },
            'membership_status': {
                'is_active': bool(active_membership),
                'plan': active_membership.plan.name if active_membership else None,
                'start_date': active_membership.start_date.isoformat() if active_membership else None,
                'end_date': active_membership.end_date.isoformat() if active_membership else None,
                'days_remaining': active_membership.days_remaining() if active_membership else 0,
                'kiosk_pin': member.kiosk_pin if member.kiosk_pin else 'Not set'
            },
            'membership_history': [
                {
                    'plan': m.plan.name,
                    'status': m.status,
                    'start_date': m.start_date.isoformat(),
                    'end_date': m.end_date.isoformat(),
                    'created_at': m.created_at.date().isoformat()
                }
                for m in memberships
            ],
            'payment_history': [
                {
                    'amount': float(p.amount),
                    'method': p.method,
                    'status': p.status,
                    'date': p.payment_date.date().isoformat(),
                    'reference': p.reference_no
                }
                for p in payments
            ],
            'attendance_summary': {
                'total_visits_30days': attendance_records.count(),
                'recent_visits': [
                    {
                        'check_in': a.check_in.strftime('%Y-%m-%d %H:%M'),
                        'check_out': a.check_out.strftime('%Y-%m-%d %H:%M') if a.check_out else 'Still in gym',
                        'duration': a.get_duration_display()
                    }
                    for a in attendance_records[:5]
                ]
            }
        }

        self._log_operation(
            'data_export',
            f'Member details accessed: {member.get_full_name()} (ID: {member.id})',
            severity='info',
            member_id=member.id
        )

        return result

    def find_expiring_memberships(self, days=7):
        """
        Find members with memberships expiring soon
        Requires: staff or admin

        Args:
            days: Number of days to look ahead (default 7)

        Returns:
            List of members with expiring memberships
        """
        self._check_permission('staff')

        today = date.today()
        end_date = today + timedelta(days=days)

        expiring = UserMembership.objects.filter(
            status='active',
            end_date__gte=today,
            end_date__lte=end_date
        ).select_related('user', 'plan').order_by('end_date')

        results = []
        for membership in expiring:
            results.append({
                'member_name': membership.user.get_full_name(),
                'member_email': membership.user.email,
                'member_mobile': membership.user.mobile_no,
                'plan': membership.plan.name,
                'expiry_date': membership.end_date.isoformat(),
                'days_remaining': membership.days_remaining()
            })

        self._log_operation(
            'report_generated',
            f'Expiring memberships report: {len(results)} members expiring in {days} days'
        )

        return results

    def find_inactive_members(self, days=30):
        """
        Find members who haven't visited recently
        Requires: staff or admin

        Args:
            days: Number of days to check (default 30)

        Returns:
            List of inactive members
        """
        self._check_permission('staff')

        cutoff_date = timezone.now() - timedelta(days=days)

        # Get all active members
        active_members = User.objects.filter(
            role='member',
            memberships__status='active',
            memberships__end_date__gte=date.today()
        ).distinct()

        # Find those who haven't checked in recently
        inactive = []
        for member in active_members:
            last_visit = Attendance.objects.filter(
                user=member
            ).order_by('-check_in').first()

            if not last_visit or last_visit.check_in < cutoff_date:
                active_membership = member.memberships.filter(
                    status='active',
                    end_date__gte=date.today()
                ).first()

                inactive.append({
                    'member_name': member.get_full_name(),
                    'member_email': member.email,
                    'member_mobile': member.mobile_no,
                    'last_visit': last_visit.check_in.date().isoformat() if last_visit else 'Never',
                    'days_since_visit': (timezone.now() - last_visit.check_in).days if last_visit else days + 1,
                    'membership_plan': active_membership.plan.name if active_membership else None
                })

        self._log_operation(
            'report_generated',
            f'Inactive members report: {len(inactive)} members inactive for {days}+ days'
        )

        return inactive

    def find_pending_payments(self):
        """
        Get all pending payment approvals
        Requires: staff or admin

        Returns:
            List of pending payments
        """
        self._check_permission('staff')

        pending = Payment.objects.filter(
            status='pending'
        ).select_related('user', 'membership__plan').order_by('-payment_date')

        results = []
        for payment in pending:
            results.append({
                'payment_id': payment.id,
                'reference': payment.reference_no,
                'member_name': payment.user.get_full_name(),
                'member_email': payment.user.email,
                'amount': float(payment.amount),
                'method': payment.method,
                'plan': payment.membership.plan.name if payment.membership else None,
                'payment_date': payment.payment_date.date().isoformat(),
                'days_pending': (timezone.now().date() - payment.payment_date.date()).days
            })

        self._log_operation(
            'report_generated',
            f'Pending payments report: {len(results)} payments awaiting approval'
        )

        return results

    # ==================== Member Operations ====================

    def confirm_payment(self, payment_reference):
        """
        Confirm a pending payment
        Requires: staff or admin

        Args:
            payment_reference: Payment reference number

        Returns:
            Success message or error
        """
        self._check_permission('staff')

        try:
            payment = Payment.objects.get(reference_no=payment_reference)

            if payment.status != 'pending':
                return {'error': f'Payment {payment_reference} is already {payment.status}'}

            # Confirm payment (this also activates the membership)
            payment.confirm(self.user)

            self._log_operation(
                'payment_received',
                f'Payment confirmed: {payment.reference_no} - ₱{payment.amount} for {payment.user.get_full_name()}',
                severity='info',
                payment_id=payment.id,
                amount=float(payment.amount)
            )

            return {
                'success': True,
                'message': f'✅ Payment {payment_reference} confirmed successfully',
                'member': payment.user.get_full_name(),
                'amount': float(payment.amount),
                'membership_activated': True
            }

        except Payment.DoesNotExist:
            return {'error': f'Payment not found: {payment_reference}'}

    def generate_kiosk_pin(self, member_identifier):
        """
        Generate or regenerate kiosk PIN for a member
        Requires: staff or admin

        Args:
            member_identifier: Member name, email, or ID

        Returns:
            New PIN or error
        """
        self._check_permission('staff')

        # Find member
        try:
            if str(member_identifier).isdigit():
                member = User.objects.get(id=int(member_identifier), role='member')
            else:
                member = User.objects.filter(
                    role='member'
                ).filter(
                    Q(email=member_identifier) |
                    Q(first_name__icontains=member_identifier) |
                    Q(last_name__icontains=member_identifier)
                ).first()

                if not member:
                    return {'error': f'Member not found: {member_identifier}'}

        except User.DoesNotExist:
            return {'error': f'Member not found: {member_identifier}'}

        # Generate new PIN
        old_pin = member.kiosk_pin
        new_pin = member.generate_kiosk_pin()

        self._log_operation(
            'user_updated',
            f'Kiosk PIN {"regenerated" if old_pin else "generated"} for {member.get_full_name()}',
            severity='info',
            member_id=member.id,
            old_pin=old_pin,
            new_pin=new_pin
        )

        return {
            'success': True,
            'message': f'✅ Kiosk PIN generated for {member.get_full_name()}',
            'member': member.get_full_name(),
            'pin': new_pin,
            'action': 'regenerated' if old_pin else 'generated'
        }

    def get_todays_checkins(self):
        """
        Get list of members who checked in today
        Requires: staff or admin

        Returns:
            List of check-ins
        """
        self._check_permission('staff')

        today = date.today()
        checkins = Attendance.objects.filter(
            check_in__date=today
        ).select_related('user').order_by('-check_in')

        results = []
        for checkin in checkins:
            results.append({
                'member_name': checkin.user.get_full_name(),
                'check_in_time': checkin.check_in.strftime('%H:%M'),
                'check_out_time': checkin.check_out.strftime('%H:%M') if checkin.check_out else 'Still in gym',
                'duration': checkin.get_duration_display(),
                'status': 'Checked out' if checkin.check_out else 'In gym'
            })

        return {
            'date': today.isoformat(),
            'total_checkins': len(results),
            'currently_in_gym': sum(1 for r in results if r['status'] == 'In gym'),
            'checkins': results
        }

    def create_walkin_sale(self, pass_name, amount, customer_name=None, mobile_no=None, method='cash'):
        """
        Record a walk-in pass sale
        Requires: staff or admin

        Args:
            pass_name: Name of the walk-in pass
            amount: Amount paid
            customer_name: Optional customer name
            mobile_no: Optional mobile number
            method: Payment method (cash or gcash)

        Returns:
            Sale confirmation or error
        """
        self._check_permission('staff')

        # Find the pass type
        try:
            pass_type = FlexibleAccess.objects.get(name__iexact=pass_name, is_active=True)
        except FlexibleAccess.DoesNotExist:
            return {'error': f'Walk-in pass not found: {pass_name}'}

        # Validate amount
        try:
            amount = Decimal(str(amount))
        except:
            return {'error': f'Invalid amount: {amount}'}

        # Create sale record
        sale = WalkInPayment.objects.create(
            pass_type=pass_type,
            customer_name=customer_name or 'Walk-in Customer',
            mobile_no=mobile_no,
            amount=amount,
            method=method,
            processed_by=self.user
        )

        self._log_operation(
            'walkin_sale',
            f'Walk-in sale recorded: {pass_type.name} - ₱{amount}',
            severity='info',
            sale_id=sale.id,
            amount=float(amount)
        )

        return {
            'success': True,
            'message': f'✅ Walk-in sale recorded: {pass_type.name}',
            'reference': sale.reference_no,
            'amount': float(amount),
            'pass_type': pass_type.name,
            'customer': customer_name or 'Walk-in Customer'
        }

    # ==================== Bulk Operations ====================

    def send_renewal_reminders(self, days=7):
        """
        Prepare list of members to send renewal reminders
        Requires: staff or admin

        Note: This prepares the list. Actual sending would be done by email system.

        Args:
            days: Number of days before expiry to remind

        Returns:
            List of members to remind
        """
        self._check_permission('staff')

        members = self.find_expiring_memberships(days)

        self._log_operation(
            'report_generated',
            f'Renewal reminder list generated: {len(members)} members',
            severity='info',
            reminder_count=len(members),
            days_ahead=days
        )

        return {
            'success': True,
            'message': f'📧 Prepared renewal reminders for {len(members)} members',
            'members': members,
            'note': 'Please use the email system to send these reminders'
        }

    # ==================== Formatting Helpers ====================

    @staticmethod
    def format_member_list(members, title="Members"):
        """Format list of members for chatbot display"""
        if not members:
            return f"No {title.lower()} found."

        text = f"**{title}** ({len(members)} total)\n\n"

        for i, member in enumerate(members[:10], 1):  # Show max 10
            text += f"{i}. **{member.get('member_name', member.get('name', 'Unknown'))}**\n"

            if 'member_email' in member:
                text += f"   📧 {member['member_email']}\n"
            if 'member_mobile' in member:
                text += f"   📱 {member['member_mobile']}\n"

            if 'membership_status' in member:
                text += f"   Status: {member['membership_status']}\n"
            if 'expiry_date' in member:
                text += f"   Expires: {member['expiry_date']} ({member.get('days_remaining', 0)} days)\n"
            if 'last_visit' in member:
                text += f"   Last Visit: {member['last_visit']}\n"

            text += "\n"

        if len(members) > 10:
            text += f"... and {len(members) - 10} more\n"

        return text

    @staticmethod
    def format_member_details(details):
        """Format complete member details for chatbot display"""
        if 'error' in details:
            return f"❌ {details['error']}"

        info = details['personal_info']
        status = details['membership_status']

        text = f"👤 **Member Profile: {info['name']}**\n\n"

        text += "**Personal Information:**\n"
        text += f"📧 Email: {info['email']}\n"
        text += f"📱 Mobile: {info['mobile']}\n"
        if info['age']:
            text += f"🎂 Age: {info['age']} years\n"
        text += f"📅 Joined: {info['joined_date']}\n\n"

        text += "**Membership Status:**\n"
        if status['is_active']:
            text += f"✅ **Active** - {status['plan']}\n"
            text += f"📅 Valid until: {status['end_date']} ({status['days_remaining']} days left)\n"
            text += f"🔑 Kiosk PIN: {status['kiosk_pin']}\n"
        else:
            text += "❌ **No Active Membership**\n"

        # Attendance summary
        attend = details['attendance_summary']
        text += f"\n**Attendance (Last 30 Days):**\n"
        text += f"🏋️ Total Visits: {attend['total_visits_30days']}\n"

        if attend['recent_visits']:
            text += "\nRecent Visits:\n"
            for visit in attend['recent_visits'][:3]:
                text += f"• {visit['check_in']} - {visit['duration']}\n"

        return text

    @staticmethod
    def format_payment_list(payments, title="Pending Payments"):
        """Format list of payments for chatbot display"""
        if not payments:
            return "No pending payments."

        text = f"💳 **{title}** ({len(payments)} total)\n\n"

        for i, payment in enumerate(payments[:10], 1):
            text += f"{i}. **{payment['member_name']}**\n"
            text += f"   Amount: ₱{payment['amount']:,.2f}\n"
            text += f"   Method: {payment['method'].upper()}\n"
            text += f"   Reference: {payment['reference']}\n"
            if 'plan' in payment and payment['plan']:
                text += f"   Plan: {payment['plan']}\n"
            if 'days_pending' in payment:
                text += f"   Pending: {payment['days_pending']} days\n"
            text += "\n"

        if len(payments) > 10:
            text += f"... and {len(payments) - 10} more\n"

        return text

    @staticmethod
    def format_operation_result(result):
        """Format operation result for chatbot display"""
        if 'error' in result:
            return f"❌ **Error:** {result['error']}"

        if 'success' in result and result['success']:
            return f"{result.get('message', '✅ Operation completed successfully')}"

        return "Operation completed"
