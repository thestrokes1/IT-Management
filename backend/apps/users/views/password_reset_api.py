"""
Password Reset API views for IT Management Platform.
Provides AJAX-based password reset functionality for the modal flow.
"""

import logging
import threading
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.views import PasswordResetConfirmView

logger = logging.getLogger('logs.security')


User = get_user_model()


class PasswordResetRequestAPI(View):
    """
    Handle password reset request via AJAX.
    Sends reset email or displays link in development mode.
    """
    
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Please enter your email address.'
            })
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether user exists - security best practice
            logger.warning(f"Password reset attempted for non-existent email: {email}")
            return JsonResponse({
                'success': True,
                'message': 'If an account exists with that email, a password reset link has been sent.',
                'development_mode': settings.DEBUG_EMAIL_MODE
            })
        
        # Generate reset token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        # Build reset URL
        reset_url = f"{request.build_absolute_uri('/')[:-1]}/password-reset/{uid}/{token}/"
        
        # Log the reset request
        logger.info(f"Password reset requested for user: {user.username} (email: {email})")
        
        if settings.DEBUG_EMAIL_MODE:
            # Development mode - return the link directly
            logger.debug(f"DEBUG MODE: Password reset link for {email}: {reset_url}")
            return JsonResponse({
                'success': True,
                'message': 'Password reset link generated.',
                'development_mode': True,
                'reset_link': reset_url,
                'email': email
            })
        else:
            # Production mode - send actual email
            try:
                self._send_password_reset_email(user, reset_url)
                return JsonResponse({
                    'success': True,
                    'message': 'If an account exists with that email, a password reset link has been sent.',
                    'development_mode': False
                })
            except Exception as e:
                logger.error(f"Failed to send password reset email: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to send password reset email. Please try again later.'
                })
    
    def _send_password_reset_email(self, user, reset_url):
        """Send password reset email to user."""
        subject = 'Password Reset Request - IT Management Platform'
        
        # Render email template
        context = {
            'user': user,
            'reset_url': reset_url,
            'platform_name': 'IT Management Platform'
        }
        
        html_content = render_to_string('emails/password_reset.html', context)
        text_content = render_to_string('emails/password_reset.txt', context)
        
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)


class PasswordResetValidateAPI(View):
    """
    Validate password reset token.
    Used when user clicks reset link from email.
    """
    
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            logger.warning(f"Invalid password reset token: uidb64={uidb64}")
            return JsonResponse({
                'valid': False,
                'error': 'Invalid or expired reset link.'
            })
        
        if default_token_generator.check_token(user, token):
            return JsonResponse({
                'valid': True,
                'user_id': user.username
            })
        else:
            logger.warning(f"Invalid password reset token for user: {user.username}")
            return JsonResponse({
                'valid': False,
                'error': 'Invalid or expired reset link.'
            })


class PasswordResetConfirmAPI(View):
    """
    Set new password after token validation.
    Used via AJAX from the reset modal.
    """
    
    def post(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired reset link.'
            })
        
        if not default_token_generator.check_token(user, token):
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired reset link.'
            })
        
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')
        
        # Validate passwords match
        if new_password1 != new_password2:
            return JsonResponse({
                'success': False,
                'error': 'Passwords do not match.'
            })
        
        # Validate password strength
        if len(new_password1) < 8:
            return JsonResponse({
                'success': False,
                'error': 'Password must be at least 8 characters long.'
            })
        
        # Set new password
        user.set_password(new_password1)
        user.save()
        
        # Log the successful password reset
        logger.info(f"Password reset completed for user: {user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Your password has been reset successfully.'
        })


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetRequestAPI(View):
    """
    Handle password reset request via AJAX (CSRF exempt for simplicity).
    """
    
    def post(self, request, *args, **kwargs):
        from django.core.exceptions import ValidationError
        from django.contrib.auth.password_validation import validate_password
        
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Please enter your email address.'
            })
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether user exists - security best practice
            logger.warning(f"Password reset attempted for non-existent email: {email}")
            return JsonResponse({
                'success': True,
                'message': 'If an account exists with that email, a password reset link has been sent.',
                'development_mode': settings.DEBUG_EMAIL_MODE
            })
        
        # Generate reset token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        # Build reset URL
        reset_url = f"{request.build_absolute_uri('/')[:-1]}/password-reset/{uid}/{token}/"
        
        # Log the reset request
        logger.info(f"Password reset requested for user: {user.username} (email: {email})")
        
        if settings.DEBUG_EMAIL_MODE:
            # Development mode - return the link directly
            logger.debug(f"DEBUG MODE: Password reset link for {email}: {reset_url}")
            return JsonResponse({
                'success': True,
                'message': 'Password reset link generated.',
                'development_mode': True,
                'reset_link': reset_url,
                'email': email
            })
        else:
            # Production mode - send actual email
            try:
                self._send_password_reset_email(user, reset_url)
                return JsonResponse({
                    'success': True,
                    'message': 'If an account exists with that email, a password reset link has been sent.',
                    'development_mode': False
                })
            except Exception as e:
                logger.error(f"Failed to send password reset email: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to send password reset email. Please try again later.'
                })
    
    def _send_password_reset_email(self, user, reset_url):
        """Send password reset email to user."""
        subject = 'Password Reset Request - IT Management Platform'
        
        # Create plain text email
        text_content = f"""
        Hello {user.username},
        
        You have requested to reset your password for the IT Management Platform.
        
        Please click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you did not request this password reset, please ignore this email.
        
        Best regards,
        IT Management Platform Team
        """
        
        # Create HTML email with better formatting
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border: 1px solid #e2e8f0; }}
                .button {{ display: inline-block; background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                .button:hover {{ background: #1d4ed8; }}
                .footer {{ text-align: center; padding: 20px; color: #64748b; font-size: 12px; }}
                .warning {{ background: #fef3c7; border: 1px solid #f59e0b; padding: 15px; border-radius: 8px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset</h1>
                    <p>IT Management Platform</p>
                </div>
                <div class="content">
                    <p>Hello <strong>{user.username}</strong>,</p>
                    <p>You have requested to reset your password for the IT Management Platform.</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #f1f5f9; padding: 10px; border-radius: 5px; font-family: monospace;">
                        {reset_url}
                    </p>
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong><br>
                        This link will expire in 1 hour for your security.<br>
                        If you did not request this password reset, please ignore this email.
                    </div>
                </div>
                <div class="footer">
                    <p>© {2024} IT Management Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)

