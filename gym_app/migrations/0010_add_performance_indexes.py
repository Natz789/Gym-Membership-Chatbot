# Generated migration for performance optimization
# Adds database indexes for chatbot analytics and operations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gym_app', '0009_usermembership_cancellation_reason_and_more'),
    ]

    operations = [
        # Add indexes for Payment queries (used in analytics)
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(
                fields=['status', '-payment_date'],
                name='payment_status_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(
                fields=['method', 'status'],
                name='payment_method_status_idx'
            ),
        ),

        # Add indexes for UserMembership queries (frequently used)
        migrations.AddIndex(
            model_name='usermembership',
            index=models.Index(
                fields=['status', 'end_date'],
                name='membership_status_end_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='usermembership',
            index=models.Index(
                fields=['user', 'status', 'end_date'],
                name='membership_user_status_idx'
            ),
        ),

        # Add indexes for WalkInPayment queries
        migrations.AddIndex(
            model_name='walkinpayment',
            index=models.Index(
                fields=['-payment_date', 'method'],
                name='walkin_date_method_idx'
            ),
        ),

        # Add composite index for Analytics date-based queries
        migrations.AddIndex(
            model_name='analytics',
            index=models.Index(
                fields=['-date', 'total_sales'],
                name='analytics_date_sales_idx'
            ),
        ),

        # Add index for User role-based queries
        migrations.AddIndex(
            model_name='user',
            index=models.Index(
                fields=['role', 'is_active'],
                name='user_role_active_idx'
            ),
        ),

        # Conversation queries optimization
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(
                fields=['user', '-updated_at'],
                name='conv_user_updated_idx'
            ),
        ),
    ]
