from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import pyotp
import qrcode
import io
import base64
import re
from models import db, User, Attendance, LeaveRequest, AdminAction, LoginAttempt, SystemLog
from config import Config
from email_helper import mail, send_password_changed_email, send_password_reset_email, send_account_created_email

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
mail.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def log_activity(action, details, user_id=None):
    """Log system activities"""
    try:
        log = SystemLog(
            action=action,
            details=details,
            user_id=user_id or (current_user.id if current_user.is_authenticated else None),
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Logging error: {e}")

def validate_password_strength(password):
    """Validate password meets security requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"

@app.route('/')
def index():
    if current_user.is_authenticated:
        # Check if user must change password
        if current_user.must_change_password:
            return redirect(url_for('change_password'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.must_change_password:
            return redirect(url_for('change_password'))
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.mfa_enabled:
                session['pre_mfa_user_id'] = user.id
                log_activity('Login attempt - MFA required', f'User: {username}', user.id)
                return redirect(url_for('verify_mfa'))
            else:
                login_user(user)
                user.last_login = datetime.utcnow()
                
                # Log successful login
                login_attempt = LoginAttempt(
                    user_id=user.id,
                    success=True,
                    ip_address=request.remote_addr
                )
                db.session.add(login_attempt)
                db.session.commit()
                
                log_activity('Successful login', f'User: {username}', user.id)
                
                # Check if user must change password
                if user.must_change_password:
                    flash('You must change your password before continuing', 'warning')
                    return redirect(url_for('change_password'))
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
        
        # Log failed login attempt
        if user:
            login_attempt = LoginAttempt(
                user_id=user.id,
                success=False,
                ip_address=request.remote_addr
            )
            db.session.add(login_attempt)
            db.session.commit()
        
        log_activity('Failed login attempt', f'Username: {username}')
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('change_password'))
        
        # Check if new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('change_password'))
        
        # Validate password strength
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            flash(message, 'danger')
            return redirect(url_for('change_password'))
        
        # Update password
        current_user.set_password(new_password)
        current_user.must_change_password = False
        db.session.commit()
        
        # Send confirmation email
        try:
            send_password_changed_email(current_user.email, current_user.username)
        except Exception as e:
            print(f"Email error: {e}")
            flash('Password changed but email notification failed', 'warning')
        
        log_activity('Password changed', f'User: {current_user.username}', current_user.id)
        flash('Password changed successfully! Email confirmation sent.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html', must_change=current_user.must_change_password)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = user.generate_reset_token()
            db.session.commit()
            
            # Create reset link
            reset_link = url_for('reset_password', token=token, _external=True)
            
            # Send reset email
            try:
                send_password_reset_email(user.email, user.username, reset_link)
                flash('Password reset link has been sent to your email', 'success')
            except Exception as e:
                print(f"Email error: {e}")
                flash('Error sending email. Please contact administrator.', 'danger')
                # For testing: show reset link in console
                print(f"Reset link: {reset_link}")
            
            log_activity('Password reset requested', f'Email: {email}')
        else:
            # Don't reveal if email exists (security best practice)
            flash('If that email exists, a reset link has been sent', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Find user with this token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset link', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if passwords match
        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        # Validate password strength
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            flash(message, 'danger')
            return redirect(url_for('reset_password', token=token))
        
        # Update password
        user.set_password(new_password)
        user.must_change_password = False
        user.clear_reset_token()
        db.session.commit()
        
        # Send confirmation email
        try:
            send_password_changed_email(user.email, user.username)
        except Exception as e:
            print(f"Email error: {e}")
        
        log_activity('Password reset completed', f'User: {user.username}', user.id)
        flash('Password reset successfully! You can now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/setup_mfa')
@login_required
def setup_mfa():
    # Check if user must change password first
    if current_user.must_change_password:
        flash('Please change your password first', 'warning')
        return redirect(url_for('change_password'))
    
    if current_user.mfa_enabled:
        flash('MFA is already enabled for your account', 'info')
        return redirect(url_for('dashboard'))
    
    # Generate MFA secret
    secret = pyotp.random_base32()
    current_user.mfa_secret = secret
    db.session.commit()
    
    # Generate QR code
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.username,
        issuer_name='Time & Attendance System'
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code = base64.b64encode(buffer.getvalue()).decode()
    
    log_activity('MFA setup initiated', f'User: {current_user.username}', current_user.id)
    
    return render_template('setup_mfa.html', qr_code=qr_code, secret=secret)

@app.route('/verify_mfa_setup', methods=['POST'])
@login_required
def verify_mfa_setup():
    token = request.form.get('token')
    
    if current_user.verify_totp(token):
        current_user.mfa_enabled = True
        db.session.commit()
        log_activity('MFA enabled successfully', f'User: {current_user.username}', current_user.id)
        flash('MFA has been successfully enabled!', 'success')
        return redirect(url_for('dashboard'))
    
    flash('Invalid MFA code. Please try again.', 'danger')
    return redirect(url_for('setup_mfa'))

@app.route('/verify_mfa', methods=['GET', 'POST'])
def verify_mfa():
    if 'pre_mfa_user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['pre_mfa_user_id'])
    
    if request.method == 'POST':
        token = request.form.get('token')
        
        if user.verify_totp(token):
            session.pop('pre_mfa_user_id')
            login_user(user)
            user.last_login = datetime.utcnow()
            
            # Log successful login
            login_attempt = LoginAttempt(
                user_id=user.id,
                success=True,
                ip_address=request.remote_addr
            )
            db.session.add(login_attempt)
            db.session.commit()
            
            log_activity('Successful login with MFA', f'User: {user.username}', user.id)
            
            # Check if user must change password
            if user.must_change_password:
                flash('You must change your password before continuing', 'warning')
                return redirect(url_for('change_password'))
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        # Log failed MFA attempt
        login_attempt = LoginAttempt(
            user_id=user.id,
            success=False,
            ip_address=request.remote_addr
        )
        db.session.add(login_attempt)
        db.session.commit()
        
        flash('Invalid MFA code', 'danger')
    
    return render_template('verify_mfa.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Check if user must change password
    if current_user.must_change_password:
        return redirect(url_for('change_password'))
    
    # Get today's attendance
    today = datetime.utcnow().date()
    today_attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    # Get recent attendance records
    recent_attendance = Attendance.query.filter_by(
        user_id=current_user.id
    ).order_by(Attendance.date.desc()).limit(7).all()
    
    # Calculate statistics
    total_hours_this_week = 0
    for att in recent_attendance:
        if att.clock_out_time:
            duration = att.clock_out_time - att.clock_in_time
            total_hours_this_week += duration.total_seconds() / 3600
    
    return render_template('dashboard.html',
                         today_attendance=today_attendance,
                         recent_attendance=recent_attendance,
                         total_hours=round(total_hours_this_week, 2))

@app.route('/clock_in', methods=['POST'])
@login_required
def clock_in():
    # Check if user must change password
    if current_user.must_change_password:
        flash('Please change your password first', 'warning')
        return redirect(url_for('change_password'))
    
    today = datetime.utcnow().date()
    existing = Attendance.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    if existing:
        flash('You have already clocked in today', 'warning')
        return redirect(url_for('dashboard'))
    
    attendance = Attendance(
        user_id=current_user.id,
        date=today,
        clock_in_time=datetime.utcnow(),
        ip_address=request.remote_addr
    )
    db.session.add(attendance)
    db.session.commit()
    
    log_activity('Clock In', f'User: {current_user.username}', current_user.id)
    flash('Clocked in successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/clock_out', methods=['POST'])
@login_required
def clock_out():
    # Check if user must change password
    if current_user.must_change_password:
        flash('Please change your password first', 'warning')
        return redirect(url_for('change_password'))
    
    today = datetime.utcnow().date()
    attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    if not attendance:
        flash('You need to clock in first', 'warning')
        return redirect(url_for('dashboard'))
    
    if attendance.clock_out_time:
        flash('You have already clocked out today', 'warning')
        return redirect(url_for('dashboard'))
    
    attendance.clock_out_time = datetime.utcnow()
    
    # Calculate work duration
    duration = attendance.clock_out_time - attendance.clock_in_time
    attendance.work_hours = round(duration.total_seconds() / 3600, 2)
    
    db.session.commit()
    
    log_activity('Clock Out', f'User: {current_user.username}, Hours: {attendance.work_hours}', current_user.id)
    flash(f'Clocked out successfully! Total hours: {attendance.work_hours}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/attendance_history')
@login_required
def attendance_history():
    page = request.args.get('page', 1, type=int)
    attendance_records = Attendance.query.filter_by(
        user_id=current_user.id
    ).order_by(Attendance.date.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('attendance_history.html', records=attendance_records)

@app.route('/leave_request', methods=['GET', 'POST'])
@login_required
def leave_request():
    if request.method == 'POST':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        leave_type = request.form.get('leave_type')
        reason = request.form.get('reason')
        
        if start_date > end_date:
            flash('End date must be after start date', 'danger')
            return redirect(url_for('leave_request'))
        
        leave = LeaveRequest(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_type,
            reason=reason
        )
        db.session.add(leave)
        db.session.commit()
        
        log_activity('Leave request submitted', f'User: {current_user.username}, Type: {leave_type}', current_user.id)
        flash('Leave request submitted successfully', 'success')
        return redirect(url_for('my_leaves'))
    
    return render_template('leave_request.html')

@app.route('/my_leaves')
@login_required
def my_leaves():
    leaves = LeaveRequest.query.filter_by(
        user_id=current_user.id
    ).order_by(LeaveRequest.created_at.desc()).all()
    
    return render_template('my_leaves.html', leaves=leaves)

# Admin Routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_attendance_today = Attendance.query.filter_by(
        date=datetime.utcnow().date()
    ).count()
    pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
    
    # Recent activities
    recent_logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(10).all()
    
    # Users currently clocked in
    today = datetime.utcnow().date()
    clocked_in = Attendance.query.filter_by(
        date=today
    ).filter(Attendance.clock_out_time == None).all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         attendance_today=total_attendance_today,
                         pending_leaves=pending_leaves,
                         recent_logs=recent_logs,
                         clocked_in=clocked_in)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('create_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('create_user'))
        
        # Validate password strength
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            flash(message, 'danger')
            return redirect(url_for('create_user'))
        
        user = User(
            username=username,
            email=email,
            is_admin=is_admin,
            must_change_password=True  # Force password change on first login
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Send account creation email
        try:
            send_account_created_email(user.email, user.username, password)
        except Exception as e:
            print(f"Email error: {e}")
            flash(f'User {username} created but email notification failed', 'warning')
        
        # Log admin action
        admin_action = AdminAction(
            admin_id=current_user.id,
            action='create_user',
            target_user_id=user.id,
            details=f'Created user: {username}'
        )
        db.session.add(admin_action)
        db.session.commit()
        
        log_activity('User created', f'Admin: {current_user.username}, New user: {username}', current_user.id)
        flash(f'User {username} created successfully. Login credentials sent via email.', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('create_user.html')

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin_users'))
    
    username = user.username
    
    # Log admin action before deletion
    admin_action = AdminAction(
        admin_id=current_user.id,
        action='delete_user',
        target_user_id=user.id,
        details=f'Deleted user: {username}'
    )
    db.session.add(admin_action)
    
    db.session.delete(user)
    db.session.commit()
    
    log_activity('User deleted', f'Admin: {current_user.username}, Deleted user: {username}', current_user.id)
    flash(f'User {username} deleted successfully', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/attendance_report')
@login_required
@admin_required
def attendance_report():
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Attendance.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    if start_date:
        query = query.filter(Attendance.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    
    if end_date:
        query = query.filter(Attendance.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    records = query.order_by(Attendance.date.desc()).paginate(page=page, per_page=50, error_out=False)
    users = User.query.filter_by(is_admin=False).all()
    
    return render_template('attendance_report.html', records=records, users=users)

@app.route('/admin/leave_requests')
@login_required
@admin_required
def leave_requests():
    status = request.args.get('status', 'pending')
    leaves = LeaveRequest.query.filter_by(status=status).order_by(LeaveRequest.created_at.desc()).all()
    
    return render_template('leave_requests.html', leaves=leaves, status=status)

@app.route('/admin/process_leave/<int:leave_id>', methods=['POST'])
@login_required
@admin_required
def process_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    action = request.form.get('action')
    
    if action == 'approve':
        leave.status = 'approved'
        leave.approved_by = current_user.id
        leave.processed_at = datetime.utcnow()
        message = 'Leave request approved'
    elif action == 'reject':
        leave.status = 'rejected'
        leave.approved_by = current_user.id
        leave.processed_at = datetime.utcnow()
        message = 'Leave request rejected'
    else:
        flash('Invalid action', 'danger')
        return redirect(url_for('leave_requests'))
    
    db.session.commit()
    
    # Log admin action
    admin_action = AdminAction(
        admin_id=current_user.id,
        action=f'leave_{action}',
        target_user_id=leave.user_id,
        details=f'{action.capitalize()} leave request for {leave.user.username}'
    )
    db.session.add(admin_action)
    db.session.commit()
    
    log_activity(f'Leave {action}', f'Admin: {current_user.username}, User: {leave.user.username}', current_user.id)
    flash(message, 'success')
    return redirect(url_for('leave_requests'))

@app.route('/admin/system_logs')
@login_required
@admin_required
def system_logs():
    page = request.args.get('page', 1, type=int)
    logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).paginate(page=page, per_page=50, error_out=False)
    
    return render_template('system_logs.html', logs=logs)

@app.route('/logout')
@login_required
def logout():
    log_activity('Logout', f'User: {current_user.username}', current_user.id)
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)