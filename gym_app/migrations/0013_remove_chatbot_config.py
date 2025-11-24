# Generated manually - Remove ChatbotConfig model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gym_app', '0012_remove_analytics_analytics_date_sales_idx_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ChatbotConfig',
        ),
    ]
