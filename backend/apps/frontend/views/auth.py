"""
Auth views for IT Management Platform.
Login, logout, and error views.
"""

import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


class LoginView(TemplateView):
    """
    User login view.
    """
    template_name = 'frontend/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get and clear logout message from session
        if 'logout_message' in self.request.session:
            context['logout_message'] = self.request.session.pop('logout_message')
        return context
    
    def post(self, request, *args, **kwargs):
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Store success message in session to display only on dashboard
                request.session['login_success'] = f'Welcome back, {user.username}!'
                return redirect('frontend:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
        
        return render(request, self.template_name, self.get_context_data())


class LogoutView(TemplateView):
    """
    User logout view.
    """
    def get(self, request, *args, **kwargs):
        from django.contrib.auth import logout
        logout(request)
        # Store logout message in session to display on login page
        request.session['logout_message'] = 'You have been logged out successfully.'
        return redirect('frontend:login')


class Error404View(TemplateView):
    """
    Custom 404 error page.
    """
    template_name = 'frontend/errors/404.html'


class Error500View(TemplateView):
    """
    Custom 500 error page.
    """
    template_name = 'frontend/errors/500.html'


class MaintenanceView(TemplateView):
    """
    Maintenance page view.
    """
    template_name = 'frontend/maintenance.html'


# Wrapper functions for URL patterns
def login_view(request):
    """User login view."""
    view = LoginView.as_view()
    return view(request)


def logout_view(request):
    """User logout view."""
    view = LogoutView.as_view()
    return view(request)


@csrf_exempt
@require_POST
def setup_admin(request):
    """One-time admin setup — only works when SETUP_TOKEN env var is set."""
    import json
    from django.contrib.auth import get_user_model
    User = get_user_model()

    token = os.environ.get('SETUP_TOKEN', '')
    if not token:
        return JsonResponse({'error': 'Not available'}, status=404)

    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if body.get('token') != token:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    username = body.get('username', 'admin')
    password = body.get('password', '')
    if not password:
        return JsonResponse({'error': 'password required'}, status=400)

    user, created = User.objects.get_or_create(username=username)
    user.is_staff = True
    user.is_superuser = True
    user.role = 'SUPERADMIN'
    user.set_password(password)
    user.save()

    verified = user.check_password(password)
    return JsonResponse({'action': 'created' if created else 'updated', 'username': username, 'verified': verified})

