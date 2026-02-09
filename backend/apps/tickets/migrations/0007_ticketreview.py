"""
Migration: Create TicketReview model (Phase 3C)

This migration creates the TicketReview model for client/requester ticket reviews.
The model enforces:
- One review per ticket (unique constraint)
- Append-only behavior (overridden in model save/delete)
- Immutable audit trail
"""

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0006_ticketstatushistory'),
        ('users', '__latest__'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('comment', models.TextField(blank=True, max_length=2000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ticket_reviews_submitted', to='users.user')),
                ('ticket', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='client_review', to='tickets.ticket')),
            ],
            options={
                'db_table': 'ticket_reviews',
                'verbose_name': 'Ticket Review',
                'verbose_name_plural': 'Ticket Reviews',
                'ordering': ['created_at'],
                'indexes': [
                    models.Index(fields=['ticket', 'created_at'], name='ticket_review_ticket_created'),
                    models.Index(fields=['author', 'created_at'], name='ticket_review_author_created'),
                ],
                'constraints': [
                    models.UniqueConstraint(fields=['ticket'], name='unique_ticket_review'),
                ],
            },
        ),
    ]

