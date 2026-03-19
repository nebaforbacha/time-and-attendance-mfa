from flask_mail import Mail, Message
from flask import render_template_string
from datetime import datetime, timedelta

mail = Mail()

def send_password_changed_email(user_email, username):
    """Send email confirmation after password change"""
    try:
        msg = Message(
            subject='Password Changed Successfully',
            recipients=[user_email]
        )
        
        msg.html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #2c3e50;">Password Changed Successfully</h2>
                    <p>Hello <strong>{username}</strong>,</p>
                    <p>Your password has been changed successfully.</p>
                    <p><strong>Date & Time:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                        <p style="margin: 0;"><strong>⚠️ Security Notice:</strong></p>
                        <p style="margin: 5px 0 0 0;">If you did not make this change, please contact your administrator immediately.</p>
                    </div>
                    <p>Best regards,<br>Time & Attendance System</p>
                </div>
            </body>
        </html>
        """
        
        msg.body = f"""
        Password Changed Successfully
        
        Hello {username},
        
        Your password has been changed successfully.
        
        If you did not make this change, please contact your administrator immediately.
        
        Best regards,
        Time & Attendance System
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


def send_password_reset_email(user_email, username, reset_link):
    """Send password reset email"""
    try:
        msg = Message(
            subject='Password Reset Request',
            recipients=[user_email]
        )
        
        msg.html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #2c3e50;">Password Reset Request</h2>
                    <p>Hello <strong>{username}</strong>,</p>
                    <p>We received a request to reset your password. Click the button below to reset it:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background-color: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    <p style="color: #666;">Or copy and paste this link into your browser:</p>
                    <p style="background-color: #e9ecef; padding: 10px; word-break: break-all; font-size: 12px;">
                        {reset_link}
                    </p>
                    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                        <p style="margin: 0;"><strong>⚠️ Security Notice:</strong></p>
                        <ul style="margin: 5px 0 0 0; padding-left: 20px;">
                            <li>This link will expire in 1 hour</li>
                            <li>If you didn't request this, ignore this email</li>
                            <li>Never share this link with anyone</li>
                        </ul>
                    </div>
                    <p>Best regards,<br>Time & Attendance System</p>
                </div>
            </body>
        </html>
        """
        
        msg.body = f"""
        Password Reset Request
        
        Hello {username},
        
        We received a request to reset your password. Click the link below to reset it:
        
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Time & Attendance System
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


def send_account_created_email(user_email, username, temp_password):
    """Send email when new account is created"""
    try:
        msg = Message(
            subject='Your Account Has Been Created',
            recipients=[user_email]
        )
        
        msg.html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #2c3e50;">Welcome to Time & Attendance System</h2>
                    <p>Hello <strong>{username}</strong>,</p>
                    <p>Your account has been created successfully. Here are your login credentials:</p>
                    <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Username:</strong> {username}</p>
                        <p><strong>Temporary Password:</strong> <code style="background-color: #e9ecef; padding: 5px 10px;">{temp_password}</code></p>
                    </div>
                    <div style="background-color: #d1ecf1; padding: 15px; border-left: 4px solid #0c5460; margin: 20px 0;">
                        <p style="margin: 0;"><strong>🔒 Important:</strong></p>
                        <p style="margin: 5px 0 0 0;">You must change this password on your first login for security reasons.</p>
                    </div>
                    <p>Best regards,<br>Time & Attendance System</p>
                </div>
            </body>
        </html>
        """
        
        msg.body = f"""
        Welcome to Time & Attendance System
        
        Hello {username},
        
        Your account has been created successfully.
        
        Username: {username}
        Temporary Password: {temp_password}
        
        IMPORTANT: You must change this password on your first login for security reasons.
        
        Best regards,
        Time & Attendance System
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False