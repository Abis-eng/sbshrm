"""
Email utility functions for sending emails in the HRM system
"""
import logging
from django.core.mail import send_mail, EmailMessage, get_connection
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import CompanySettings

logger = logging.getLogger(__name__)


def get_email_connection():
    """Get email connection using CompanySettings"""
    connection = None
    try:
        company_settings = CompanySettings.objects.first()
        if not company_settings:
            logger.error("Company settings not found")
            return None
            
        if not company_settings.email_enabled:
            logger.warning("Email is not enabled in company settings")
            return None
        
        if not company_settings.email_host_user:
            logger.error("Email host user not configured")
            return None
            
        if not company_settings.email_host_password:
            logger.error("Email host password not configured")
            return None
        
        # Validate TLS/SSL settings
        if company_settings.email_use_tls and company_settings.email_use_ssl:
            logger.error("Cannot use both TLS and SSL. Please use only one.")
            return None
        
        host = company_settings.email_host or 'smtp.gmail.com'
        port = company_settings.email_port or 587
        username = company_settings.email_host_user
        use_tls = company_settings.email_use_tls
        use_ssl = company_settings.email_use_ssl
        
        logger.info(f"Creating email connection: {host}:{port}, TLS={use_tls}, SSL={use_ssl}, User={username}")
        
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=host,
            port=port,
            username=username,
            password=company_settings.email_host_password,
            use_tls=use_tls,
            use_ssl=use_ssl,
            fail_silently=False,
        )
        
        # Test the connection
        try:
            logger.info(f"Opening email connection to {host}:{port}...")
            connection.open()
            logger.info("Email connection opened successfully")
            
            # Try to authenticate
            try:
                connection.login(username, company_settings.email_host_password)
                logger.info("Email authentication successful")
            except Exception as auth_error:
                error_msg = f"Authentication failed: {str(auth_error)}"
                logger.error(error_msg)
                connection.close()
                # Provide specific error message
                if "535" in str(auth_error) or "534" in str(auth_error) or "authentication" in str(auth_error).lower():
                    raise Exception("Authentication failed. Your email password is incorrect. For Gmail with 2FA, you must use an App Password.")
                else:
                    raise Exception(f"Authentication error: {str(auth_error)}")
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to open email connection: {error_msg}")
            import traceback
            logger.error(traceback.format_exc())
            if connection:
                try:
                    connection.close()
                except:
                    pass
            # Re-raise with better message
            if "authentication" in error_msg.lower() or "535" in error_msg or "534" in error_msg:
                raise Exception("Authentication failed. Your email password is incorrect. For Gmail with 2FA, you must use an App Password.")
            elif "connection" in error_msg.lower() or "refused" in error_msg.lower() or "timeout" in error_msg.lower():
                raise Exception(f"Cannot connect to email server {host}:{port}. Check your network and firewall settings.")
            else:
                raise Exception(f"Connection error: {error_msg}")
            
        return connection
    except Exception as e:
        error_msg = f"Error getting email connection: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        if connection:
            try:
                connection.close()
            except:
                pass
        return None


def send_email(subject, message, recipient_list, html_message=None, from_email=None, fail_silently=False):
    """
    Send email using CompanySettings configuration
    
    Args:
        subject: Email subject
        message: Plain text message
        recipient_list: List of recipient email addresses
        html_message: Optional HTML message
        from_email: Optional from email address
        fail_silently: If True, suppress exceptions
    """
    connection = None
    try:
        company_settings = CompanySettings.objects.first()
        if not company_settings:
            error_msg = "Company settings not found"
            logger.error(error_msg)
            return False
        
        if not company_settings.email_enabled:
            error_msg = "Email is not enabled in company settings"
            logger.warning(error_msg)
            return False
        
        if not recipient_list:
            error_msg = "No recipients provided"
            logger.warning(error_msg)
            return False
        
        # Validate email settings
        if not company_settings.email_host_user:
            error_msg = "Email username not configured"
            logger.error(error_msg)
            return False
            
        if not company_settings.email_host_password:
            error_msg = "Email password not configured"
            logger.error(error_msg)
            return False
        
        # Get from email
        if not from_email:
            from_email = company_settings.email_host_user or company_settings.email or settings.DEFAULT_FROM_EMAIL
        
        logger.info(f"Attempting to send email to {recipient_list} using {company_settings.email_host}:{company_settings.email_port}")
        
        # Get email connection
        connection = get_email_connection()
        if not connection:
            error_msg = "Could not establish email connection. Please check your SMTP settings."
            logger.error(error_msg)
            return False
        
        # Send email
        try:
            from_email_str = f"{company_settings.email_from_name} <{from_email}>"
            logger.info(f"Sending email from: {from_email_str}")
            
            if html_message:
                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email=from_email_str,
                    to=recipient_list,
                    connection=connection,
                )
                email.content_subtype = 'html'
                email.send()
                logger.info(f"HTML email sent successfully to {recipient_list}")
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email_str,
                    recipient_list=recipient_list,
                    fail_silently=fail_silently,
                    connection=connection,
                )
                logger.info(f"Plain text email sent successfully to {recipient_list}")
            
            return True
        except Exception as send_error:
            error_msg = f"Error sending email: {str(send_error)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            # Close connection on error
            if connection:
                try:
                    connection.close()
                except:
                    pass
            if not fail_silently:
                raise Exception(error_msg)
            return False
    except Exception as e:
        error_msg = f"Error in send_email: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        if connection:
            try:
                connection.close()
            except:
                pass
        if not fail_silently:
            raise
        return False


def send_welcome_email(employee, username, password):
    """Send welcome email to new employee"""
    try:
        company_settings = CompanySettings.objects.first()
        if not company_settings or not company_settings.email_enabled:
            return False
        
        employee_email = employee.user.email
        if not employee_email:
            logger.warning(f"No email address for employee {employee.user.username}")
            return False
        
        context = {
            'employee': employee,
            'username': username,
            'password': password,
            'company_name': company_settings.company_name,
            'company_email': company_settings.email,
            'login_url': f"{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'}/",
        }
        
        html_message = render_to_string('core/emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        subject = f"Welcome to {company_settings.company_name} - Your Account Details"
        
        return send_email(
            subject=subject,
            message=plain_message,
            recipient_list=[employee_email],
            html_message=html_message,
        )
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        return False


def send_test_email(recipient_email):
    """Send test email to verify email configuration"""
    try:
        company_settings = CompanySettings.objects.first()
        if not company_settings:
            return False, "Company settings not found"
        
        if not company_settings.email_enabled:
            return False, "Email is not enabled in settings. Please enable it and save first."
        
        # Validate settings
        if not company_settings.email_host_user:
            return False, "Email username is not configured. Please enter your email address."
        
        if not company_settings.email_host_password:
            return False, "Email password is not configured. Please enter your email password."
        
        # Test connection first
        try:
            connection = get_email_connection()
            if not connection:
                return False, "Cannot connect to email server. Please check: 1) SMTP host and port are correct, 2) Email username and password are correct, 3) For Gmail, use App Password if 2FA is enabled."
        except Exception as conn_err:
            error_str = str(conn_err).lower()
            if "authentication" in error_str or "password" in error_str or "535" in str(conn_err) or "534" in str(conn_err):
                return False, f"Authentication failed. Your email password is incorrect. For Gmail with 2FA enabled, you MUST use an App Password instead of your regular password. Error: {str(conn_err)}"
            elif "connection" in error_str or "refused" in error_str:
                return False, f"Cannot connect to email server. Check your SMTP settings (Host: {company_settings.email_host}, Port: {company_settings.email_port}). Error: {str(conn_err)}"
            else:
                return False, f"Connection error: {str(conn_err)}"
        
        context = {
            'company_name': company_settings.company_name,
            'email_host': company_settings.email_host,
            'email_port': company_settings.email_port,
        }
        
        html_message = render_to_string('core/emails/test_email.html', context)
        plain_message = strip_tags(html_message)
        
        subject = f"Test Email from {company_settings.company_name} HRM System"
        
        # Try to send with detailed error handling
        try:
            success = send_email(
                subject=subject,
                message=plain_message,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,  # Don't fail silently so we can catch the error
            )
            
            if success:
                return True, "Test email sent successfully!"
            else:
                return False, "Failed to send email. Check your password and SMTP settings."
        except Exception as send_err:
            error_str = str(send_err).lower()
            if "authentication" in error_str or "login" in error_str or "535" in error_str or "534" in error_str:
                return False, f"Authentication failed. Your email password is incorrect. For Gmail with 2FA, you must use an App Password. Error: {str(send_err)}"
            elif "connection" in error_str or "timeout" in error_str or "refused" in error_str:
                return False, f"Cannot connect to email server. Check your SMTP host ({company_settings.email_host}) and port ({company_settings.email_port}). Error: {str(send_err)}"
            elif "tls" in error_str or "ssl" in error_str:
                return False, f"TLS/SSL error. Make sure 'Use TLS' is checked for port 587, or 'Use SSL' is checked for port 465. Error: {str(send_err)}"
            else:
                return False, f"Email sending failed: {str(send_err)}"
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending test email: {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        return False, f"Error: {error_msg}"


def send_notification_email(recipient_email, subject, message, html_message=None):
    """Send general notification email"""
    return send_email(
        subject=subject,
        message=message,
        recipient_list=[recipient_email],
        html_message=html_message,
    )

