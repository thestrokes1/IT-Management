# Generated migration for adding contact_type field to Ticket model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0008_ticketnote_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='contact_type',
            field=models.CharField(blank=True, choices=[('CLIENT', 'Client'), ('TECHNICIAN', 'Technician')], max_length=20),
        ),
    ]

