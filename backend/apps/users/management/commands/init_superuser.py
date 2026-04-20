import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update superuser from environment variables'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        FALLBACK_PASSWORD = 'Deploy2026!IT'

        if not username:
            username = 'admin'
        if not password:
            password = FALLBACK_PASSWORD
            self.stdout.write(f'WARNING: DJANGO_SUPERUSER_PASSWORD not set — using fallback password')

        user, created = User.objects.get_or_create(username=username)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.role = 'SUPERADMIN'
        user.set_password(password)
        user.save()

        user.refresh_from_db()
        verified = user.check_password(password)

        action = 'Created' if created else 'Updated'
        self.stdout.write(f'===> {action} superuser: "{username}" password_length={len(password)} verified={verified} <===')
        if not verified:
            self.stdout.write('ERROR: password was NOT saved correctly to DB!')

