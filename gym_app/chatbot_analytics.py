"""
Advanced Analytics Engine for Gym Chatbot
Generates real-time analytics, reports, and insights
Optimized with aggressive caching and query optimization
"""

from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from django.core.cache import cache
from datetime import date, datetime, timedelta
from decimal import Decimal
from .models import (
    User, UserMembership, Payment, WalkInPayment,
    Attendance, MembershipPlan, FlexibleAccess, Analytics
)
import json


class AnalyticsEngine:
    """
    High-performance analytics engine for gym data
    All queries are optimized with select_related, prefetch_related, only, defer
    Results are aggressively cached with Redis
    """

    # Cache durations (in seconds)
    CACHE_DURATION_SHORT = 120  # 2 minutes for frequently changing data
    CACHE_DURATION_MEDIUM = 600  # 10 minutes for semi-static data
    CACHE_DURATION_LONG = 3600  # 1 hour for mostly static data

    @staticmethod
    def _get_date_range(period='today'):
        """Get start and end dates for a period"""
        today = date.today()

        if period == 'today':
            return today, today
        elif period == 'yesterday':
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif period == 'this_week':
            start = today - timedelta(days=today.weekday())
            return start, today
        elif period == 'last_week':
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            return start, end
        elif period == 'this_month':
            start = today.replace(day=1)
            return start, today
        elif period == 'last_month':
            last_month = today.replace(day=1) - timedelta(days=1)
            start = last_month.replace(day=1)
            return start, last_month
        elif period == 'this_year':
            start = today.replace(month=1, day=1)
            return start, today
        elif isinstance(period, tuple) and len(period) == 2:
            # Custom date range
            return period
        else:
            return today, today

    @classmethod
    def get_revenue_summary(cls, period='today', use_cache=True):
        """
        Get revenue breakdown for a period
        Cached for better performance
        """
        cache_key = f'analytics_revenue_{period}'

        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                return cached

        start_date, end_date = cls._get_date_range(period)

        # Membership revenue (optimized query)
        member_revenue = Payment.objects.filter(
            payment_date__date__gte=start_date,
            payment_date__date__lte=end_date,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Walk-in revenue
        walkin_revenue = WalkInPayment.objects.filter(
            payment_date__date__gte=start_date,
            payment_date__date__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Payment method breakdown
        cash_revenue = Payment.objects.filter(
            payment_date__date__gte=start_date,
            payment_date__date__lte=end_date,
            status='confirmed',
            method='cash'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        gcash_revenue = Payment.objects.filter(
            payment_date__date__gte=start_date,
            payment_date__date__lte=end_date,
            status='confirmed',
            method='gcash'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        walkin_cash = WalkInPayment.objects.filter(
            payment_date__date__gte=start_date,
            payment_date__date__lte=end_date,
            method='cash'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        walkin_gcash = WalkInPayment.objects.filter(
            payment_date__date__gte=start_date,
            payment_date__date__lte=end_date,
            method='gcash'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        total_cash = cash_revenue + walkin_cash
        total_gcash = gcash_revenue + walkin_gcash
        total_revenue = member_revenue + walkin_revenue

        result = {
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_revenue': float(total_revenue),
            'membership_revenue': float(member_revenue),
            'walkin_revenue': float(walkin_revenue),
            'payment_methods': {
                'cash': float(total_cash),
                'gcash': float(total_gcash)
            },
            'currency': 'PHP'
        }

        # Cache result
        cache.set(cache_key, result, cls.CACHE_DURATION_SHORT)
        return result

    @classmethod
    def get_membership_growth(cls, period='this_month', use_cache=True):
        """
        Analyze membership growth and trends
        """
        cache_key = f'analytics_growth_{period}'

        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                return cached

        start_date, end_date = cls._get_date_range(period)

        # New memberships created
        new_memberships = UserMembership.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).count()

        # Active memberships (currently valid)
        active_memberships = UserMembership.objects.filter(
            status='active',
            end_date__gte=date.today()
        ).count()

        # Expired this period
        expired_memberships = UserMembership.objects.filter(
            status='expired',
            end_date__gte=start_date,
            end_date__lte=end_date
        ).count()

        # Cancelled this period
        cancelled_memberships = UserMembership.objects.filter(
            status='cancelled',
            cancelled_at__date__gte=start_date,
            cancelled_at__date__lte=end_date
        ).count()

        # Compare with previous period
        period_days = (end_date - start_date).days + 1
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date - timedelta(days=1)

        prev_new = UserMembership.objects.filter(
            created_at__date__gte=prev_start,
            created_at__date__lte=prev_end
        ).count()

        growth_rate = ((new_memberships - prev_new) / prev_new * 100) if prev_new > 0 else 0

        result = {
            'period': period,
            'new_memberships': new_memberships,
            'active_memberships': active_memberships,
            'expired_memberships': expired_memberships,
            'cancelled_memberships': cancelled_memberships,
            'growth_rate': round(growth_rate, 2),
            'comparison': {
                'current_period': new_memberships,
                'previous_period': prev_new,
                'change': new_memberships - prev_new
            }
        }

        cache.set(cache_key, result, cls.CACHE_DURATION_SHORT)
        return result

    @classmethod
    def get_attendance_trends(cls, period='this_week', use_cache=True):
        """
        Analyze attendance patterns and trends
        """
        cache_key = f'analytics_attendance_{period}'

        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                return cached

        start_date, end_date = cls._get_date_range(period)

        # Total check-ins
        total_checkins = Attendance.objects.filter(
            check_in__date__gte=start_date,
            check_in__date__lte=end_date
        ).count()

        # Unique members who visited
        unique_visitors = Attendance.objects.filter(
            check_in__date__gte=start_date,
            check_in__date__lte=end_date
        ).values('user').distinct().count()

        # Average session duration
        completed_sessions = Attendance.objects.filter(
            check_in__date__gte=start_date,
            check_in__date__lte=end_date,
            check_out__isnull=False
        )

        avg_duration = completed_sessions.aggregate(
            avg=Avg('duration_minutes')
        )['avg'] or 0

        # Peak hours analysis (group by hour of day)
        hourly_checkins = {}
        checkins_by_hour = Attendance.objects.filter(
            check_in__date__gte=start_date,
            check_in__date__lte=end_date
        ).extra(select={'hour': 'CAST(strftime("%%H", check_in) AS INTEGER)'}).values('hour').annotate(count=Count('id')).order_by('hour')

        for entry in checkins_by_hour:
            hour = entry['hour']
            hourly_checkins[hour] = entry['count']

        # Find peak hour
        peak_hour = max(hourly_checkins.items(), key=lambda x: x[1]) if hourly_checkins else (0, 0)

        # Daily breakdown
        daily_checkins = Attendance.objects.filter(
            check_in__date__gte=start_date,
            check_in__date__lte=end_date
        ).extra(
            select={'day': 'date(check_in)'}
        ).values('day').annotate(count=Count('id')).order_by('day')

        result = {
            'period': period,
            'total_checkins': total_checkins,
            'unique_visitors': unique_visitors,
            'average_duration_minutes': round(avg_duration, 2),
            'peak_hour': {
                'hour': peak_hour[0],
                'checkins': peak_hour[1]
            },
            'daily_breakdown': list(daily_checkins),
            'hourly_distribution': hourly_checkins
        }

        cache.set(cache_key, result, cls.CACHE_DURATION_SHORT)
        return result

    @classmethod
    def get_member_retention_analysis(cls, use_cache=True):
        """
        Analyze member retention and churn
        """
        cache_key = 'analytics_retention'

        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                return cached

        today = date.today()

        # Total active members
        active_members = UserMembership.objects.filter(
            status='active',
            end_date__gte=today
        ).count()

        # Members expiring soon
        expiring_7days = UserMembership.objects.filter(
            status='active',
            end_date__gte=today,
            end_date__lte=today + timedelta(days=7)
        ).count()

        expiring_14days = UserMembership.objects.filter(
            status='active',
            end_date__gte=today,
            end_date__lte=today + timedelta(days=14)
        ).count()

        expiring_30days = UserMembership.objects.filter(
            status='active',
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30)
        ).count()

        # Churn rate (last 30 days)
        thirty_days_ago = today - timedelta(days=30)
        expired_last_month = UserMembership.objects.filter(
            status='expired',
            end_date__gte=thirty_days_ago,
            end_date__lt=today
        ).count()

        cancelled_last_month = UserMembership.objects.filter(
            status='cancelled',
            cancelled_at__date__gte=thirty_days_ago,
            cancelled_at__date__lt=today
        ).count()

        total_churn = expired_last_month + cancelled_last_month
        churn_rate = (total_churn / active_members * 100) if active_members > 0 else 0

        # Renewal rate analysis
        # Members who expired and renewed (purchased new membership within 7 days)
        renewed_count = 0
        recent_expired = UserMembership.objects.filter(
            status='expired',
            end_date__gte=thirty_days_ago,
            end_date__lt=today
        ).select_related('user')

        for membership in recent_expired:
            # Check if user has a newer active membership
            has_renewed = UserMembership.objects.filter(
                user=membership.user,
                created_at__gte=membership.end_date,
                created_at__lte=membership.end_date + timedelta(days=7)
            ).exists()
            if has_renewed:
                renewed_count += 1

        renewal_rate = (renewed_count / expired_last_month * 100) if expired_last_month > 0 else 0

        result = {
            'active_members': active_members,
            'expiring_soon': {
                'next_7_days': expiring_7days,
                'next_14_days': expiring_14days,
                'next_30_days': expiring_30days
            },
            'churn_analysis': {
                'churn_rate_30days': round(churn_rate, 2),
                'expired_last_month': expired_last_month,
                'cancelled_last_month': cancelled_last_month,
                'total_churn': total_churn
            },
            'renewal_rate': round(renewal_rate, 2),
            'retention_rate': round(100 - churn_rate, 2)
        }

        cache.set(cache_key, result, cls.CACHE_DURATION_MEDIUM)
        return result

    @classmethod
    def get_plan_popularity(cls, period='this_month', use_cache=True):
        """
        Analyze which membership plans are most popular
        """
        cache_key = f'analytics_plan_popularity_{period}'

        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                return cached

        start_date, end_date = cls._get_date_range(period)

        # Membership plan statistics
        plan_stats = UserMembership.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values(
            'plan__name', 'plan__price', 'plan__duration_days'
        ).annotate(
            count=Count('id'),
            revenue=Sum('plan__price')
        ).order_by('-count')

        # Walk-in pass statistics
        pass_stats = WalkInPayment.objects.filter(
            payment_date__date__gte=start_date,
            payment_date__date__lte=end_date
        ).values(
            'pass_type__name', 'pass_type__price', 'pass_type__duration_days'
        ).annotate(
            count=Count('id'),
            revenue=Sum('amount')
        ).order_by('-count')

        # Conversion rate (plan views to purchases)
        # This would require tracking plan views, placeholder for now

        result = {
            'period': period,
            'membership_plans': [
                {
                    'name': stat['plan__name'],
                    'price': float(stat['plan__price']) if stat['plan__price'] else 0,
                    'duration_days': stat['plan__duration_days'],
                    'purchases': stat['count'],
                    'revenue': float(stat['revenue']) if stat['revenue'] else 0
                }
                for stat in plan_stats
            ],
            'walk_in_passes': [
                {
                    'name': stat['pass_type__name'],
                    'price': float(stat['pass_type__price']) if stat['pass_type__price'] else 0,
                    'duration_days': stat['pass_type__duration_days'],
                    'purchases': stat['count'],
                    'revenue': float(stat['revenue']) if stat['revenue'] else 0
                }
                for stat in pass_stats
            ]
        }

        cache.set(cache_key, result, cls.CACHE_DURATION_MEDIUM)
        return result

    @classmethod
    def get_payment_collection_status(cls, use_cache=True):
        """
        Track payment collection rates and outstanding balances
        """
        cache_key = 'analytics_payment_status'

        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                return cached

        # Pending payments
        pending_payments = Payment.objects.filter(
            status='pending'
        ).aggregate(
            count=Count('id'),
            total_amount=Sum('amount')
        )

        # Confirmed payments (this month)
        today = date.today()
        start_of_month = today.replace(day=1)

        confirmed_this_month = Payment.objects.filter(
            status='confirmed',
            approved_at__date__gte=start_of_month
        ).aggregate(
            count=Count('id'),
            total_amount=Sum('amount')
        )

        # Rejected payments (this month)
        rejected_this_month = Payment.objects.filter(
            status='rejected',
            approved_at__date__gte=start_of_month
        ).count()

        # Collection rate
        total_payments = (confirmed_this_month['count'] or 0) + (pending_payments['count'] or 0) + rejected_this_month
        collection_rate = ((confirmed_this_month['count'] or 0) / total_payments * 100) if total_payments > 0 else 0

        result = {
            'pending': {
                'count': pending_payments['count'] or 0,
                'total_amount': float(pending_payments['total_amount'] or 0)
            },
            'confirmed_this_month': {
                'count': confirmed_this_month['count'] or 0,
                'total_amount': float(confirmed_this_month['total_amount'] or 0)
            },
            'rejected_this_month': rejected_this_month,
            'collection_rate': round(collection_rate, 2)
        }

        cache.set(cache_key, result, cls.CACHE_DURATION_SHORT)
        return result

    @classmethod
    def get_comprehensive_report(cls, period='today'):
        """
        Generate a comprehensive analytics report combining all metrics
        Perfect for admin dashboard summaries
        """
        return {
            'period': period,
            'generated_at': timezone.now().isoformat(),
            'revenue': cls.get_revenue_summary(period),
            'membership_growth': cls.get_membership_growth(period),
            'attendance': cls.get_attendance_trends(period),
            'retention': cls.get_member_retention_analysis(),
            'plan_popularity': cls.get_plan_popularity(period),
            'payment_status': cls.get_payment_collection_status()
        }

    @classmethod
    def format_report_for_chatbot(cls, report_data, report_type='summary'):
        """
        Format analytics data into human-readable text for chatbot responses
        """
        if report_type == 'revenue':
            data = report_data
            text = f"💰 **Revenue Report - {data['period'].replace('_', ' ').title()}**\n\n"
            text += f"📊 Total Revenue: ₱{data['total_revenue']:,.2f}\n"
            text += f"   • Membership Sales: ₱{data['membership_revenue']:,.2f}\n"
            text += f"   • Walk-in Sales: ₱{data['walkin_revenue']:,.2f}\n\n"
            text += f"💳 Payment Methods:\n"
            text += f"   • Cash: ₱{data['payment_methods']['cash']:,.2f}\n"
            text += f"   • GCash: ₱{data['payment_methods']['gcash']:,.2f}\n"
            return text

        elif report_type == 'growth':
            data = report_data
            text = f"📈 **Membership Growth - {data['period'].replace('_', ' ').title()}**\n\n"
            text += f"✅ New Memberships: {data['new_memberships']}\n"
            text += f"🔥 Active Memberships: {data['active_memberships']}\n"
            text += f"⏰ Expired: {data['expired_memberships']}\n"
            text += f"❌ Cancelled: {data['cancelled_memberships']}\n\n"

            growth = data['growth_rate']
            emoji = "📈" if growth > 0 else "📉" if growth < 0 else "➡️"
            text += f"{emoji} Growth Rate: {growth:+.1f}% vs previous period\n"
            text += f"   (Current: {data['comparison']['current_period']}, Previous: {data['comparison']['previous_period']})"
            return text

        elif report_type == 'attendance':
            data = report_data
            text = f"🏋️ **Attendance Report - {data['period'].replace('_', ' ').title()}**\n\n"
            text += f"👥 Total Check-ins: {data['total_checkins']}\n"
            text += f"🧑 Unique Visitors: {data['unique_visitors']}\n"
            text += f"⏱️ Average Session: {data['average_duration_minutes']:.0f} minutes\n\n"

            if data['peak_hour']['checkins'] > 0:
                hour = data['peak_hour']['hour']
                hour_str = f"{hour:02d}:00 - {hour+1:02d}:00"
                text += f"🔥 Peak Hour: {hour_str} ({data['peak_hour']['checkins']} check-ins)"
            return text

        elif report_type == 'retention':
            data = report_data
            text = f"📊 **Member Retention Analysis**\n\n"
            text += f"👤 Active Members: {data['active_members']}\n\n"
            text += f"⚠️ Expiring Soon:\n"
            text += f"   • Next 7 days: {data['expiring_soon']['next_7_days']}\n"
            text += f"   • Next 14 days: {data['expiring_soon']['next_14_days']}\n"
            text += f"   • Next 30 days: {data['expiring_soon']['next_30_days']}\n\n"
            text += f"📉 Churn Rate (30 days): {data['churn_analysis']['churn_rate_30days']}%\n"
            text += f"♻️ Renewal Rate: {data['renewal_rate']}%\n"
            text += f"✅ Retention Rate: {data['retention_rate']}%"
            return text

        elif report_type == 'plans':
            data = report_data
            text = f"🎯 **Plan Popularity - {data['period'].replace('_', ' ').title()}**\n\n"

            if data['membership_plans']:
                text += "**Membership Plans:**\n"
                for i, plan in enumerate(data['membership_plans'][:5], 1):
                    text += f"{i}. {plan['name']} - {plan['purchases']} sales (₱{plan['revenue']:,.0f})\n"

            if data['walk_in_passes']:
                text += "\n**Walk-in Passes:**\n"
                for i, pass_item in enumerate(data['walk_in_passes'][:5], 1):
                    text += f"{i}. {pass_item['name']} - {pass_item['purchases']} sales (₱{pass_item['revenue']:,.0f})\n"

            return text

        elif report_type == 'payments':
            data = report_data
            text = f"💳 **Payment Collection Status**\n\n"
            text += f"⏳ Pending Approvals: {data['pending']['count']} (₱{data['pending']['total_amount']:,.2f})\n"
            text += f"✅ Confirmed (This Month): {data['confirmed_this_month']['count']} (₱{data['confirmed_this_month']['total_amount']:,.2f})\n"
            text += f"❌ Rejected (This Month): {data['rejected_this_month']}\n\n"
            text += f"📊 Collection Rate: {data['collection_rate']}%"
            return text

        else:  # comprehensive summary
            text = "📊 **Comprehensive Performance Summary**\n\n"

            rev = report_data.get('revenue', {})
            text += f"💰 Revenue: ₱{rev.get('total_revenue', 0):,.2f}\n"

            growth = report_data.get('membership_growth', {})
            text += f"📈 New Members: {growth.get('new_memberships', 0)}\n"
            text += f"🔥 Active Members: {growth.get('active_memberships', 0)}\n"

            attend = report_data.get('attendance', {})
            text += f"🏋️ Check-ins: {attend.get('total_checkins', 0)}\n"

            retention = report_data.get('retention', {})
            text += f"✅ Retention Rate: {retention.get('retention_rate', 0)}%\n"

            return text

    @classmethod
    def clear_all_caches(cls):
        """
        Clear all analytics caches
        Call this when data is updated
        """
        periods = ['today', 'yesterday', 'this_week', 'last_week', 'this_month', 'last_month']

        for period in periods:
            cache.delete(f'analytics_revenue_{period}')
            cache.delete(f'analytics_growth_{period}')
            cache.delete(f'analytics_attendance_{period}')
            cache.delete(f'analytics_plan_popularity_{period}')

        cache.delete('analytics_retention')
        cache.delete('analytics_payment_status')
