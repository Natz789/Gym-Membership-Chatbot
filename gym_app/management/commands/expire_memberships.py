from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from gym_app.models import UserMembership, Analytics


class Command(BaseCommand):
    help = 'Expire memberships that have passed their end date and generate daily analytics'

    def handle(self, *args, **kwargs):
        today = date.today()
        
        # Find and expire old memberships
        expired_count = UserMembership.objects.filter(
            status='active',
            end_date__lt=today
        ).update(status='expired')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully expired {expired_count} memberships')
        )
        
        # Generate daily analytics
        try:
            analytics = Analytics.generate_daily_report(today)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Analytics generated for {today}: '
                    f'{analytics.total_members} active members, '
                    f'₱{analytics.total_sales} in sales'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating analytics: {str(e)}')
            )