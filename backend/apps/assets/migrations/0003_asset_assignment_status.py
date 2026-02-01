from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('assets', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='assignment_status',
            field=models.CharField(
                choices=[('UNASSIGNED', 'Unassigned'), ('ASSIGNED', 'Assigned')],
                default='UNASSIGNED',
                max_length=20
            ),
        ),
    ]
