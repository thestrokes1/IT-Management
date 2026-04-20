# Generated migration for adding contact fields to Asset model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_asset_assignment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='contact_type',
            field=models.CharField(blank=True, choices=[('CLIENT', 'Client'), ('TECHNICIAN', 'Technician')], max_length=20),
        ),
        migrations.AddField(
            model_name='asset',
            name='contact_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='asset',
            name='contact_phone',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]

