"""
Auth views for IT Management Platform.
Login, logout, and error views.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView


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

