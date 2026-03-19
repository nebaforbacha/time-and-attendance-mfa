import unittest
import pyotp
from datetime import datetime, timedelta
from app import app, db
from models import User, Attendance, LeaveRequest, LoginAttempt, AdminAction, SystemLog

class TimeAttendanceSystemTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test users
        self.create_test_users()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_users(self):
        """Create test users for testing"""
        # Create admin user
        admin = User(
            username='testadmin',
            email='admin@test.com',
            is_admin=True
        )
        admin.set_password('Admin123#')
        
        # Create regular user
        user = User(
            username='testuser',
            email='user@test.com',
            is_admin=False
        )
        user.set_password('User123#')
        
        # Create user with MFA
        mfa_user = User(
            username='mfauser',
            email='mfa@test.com',
            is_admin=False,
            mfa_enabled=True,
            mfa_secret=pyotp.random_base32()
        )
        mfa_user.set_password('Mfa123#')
        
        db.session.add_all([admin, user, mfa_user])
        db.session.commit()
    
    # Authentication Tests
    def test_user_login_success(self):
        """Test successful user login"""
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'User123#'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testuser', response.data)
    
    def test_user_login_failure(self):
        """Test failed user login with wrong password"""
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)
    
    def test_mfa_setup(self):
        """Test MFA setup process"""
        # Login first
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'User123#'
        })
        
        # Access MFA setup
        response = self.app.get('/setup_mfa', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'qr_code', response.data.lower())
    
    def test_mfa_verification(self):
        """Test MFA token verification"""
        mfa_user = User.query.filter_by(username='mfauser').first()
        totp = pyotp.TOTP(mfa_user.mfa_secret)
        valid_token = totp.now()
        
        # Set pre-MFA session
        with self.app.session_transaction() as sess:
            sess['pre_mfa_user_id'] = mfa_user.id
        
        response = self.app.post('/verify_mfa', data={
            'token': valid_token
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
    
    def test_invalid_mfa_token(self):
        """Test MFA with invalid token"""
        mfa_user = User.query.filter_by(username='mfauser').first()
        
        with self.app.session_transaction() as sess:
            sess['pre_mfa_user_id'] = mfa_user.id
        
        response = self.app.post('/verify_mfa', data={
            'token': '000000'
        }, follow_redirects=True)
        
        self.assertIn(b'Invalid MFA code', response.data)
    
    # Attendance Tests
    def test_clock_in(self):
        """Test clock in functionality"""
        # Login first
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'User123#'
        })
        
        response = self.app.post('/clock_in', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Clocked in successfully', response.data)
        
        # Verify attendance record was created
        user = User.query.filter_by(username='testuser').first()
        attendance = Attendance.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(attendance)
        self.assertIsNotNone(attendance.clock_in_time)
        self.assertIsNone(attendance.clock_out_time)
    
    def test_clock_out(self):
        """Test clock out functionality"""
        # Login and clock in first
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'User123#'
        })
        self.app.post('/clock_in')
        
        # Clock out
        response = self.app.post('/clock_out', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Clocked out successfully', response.data)
        
        # Verify attendance record was updated
        user = User.query.filter_by(username='testuser').first()
        attendance = Attendance.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(attendance.clock_out_time)
        self.assertIsNotNone(attendance.work_hours)
    
    def test_duplicate_clock_in(self):
        """Test prevention of duplicate clock in"""
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'User123#'
        })
        self.app.post('/clock_in')
        
        # Try to clock in again
        response = self.app.post('/clock_in', follow_redirects=True)
        self.assertIn(b'already clocked in', response.data)
    
    def test_clock_out_without_clock_in(self):
        """Test clock out without clocking in"""
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'User123#'
        })
        
        response = self.app.post('/clock_out', follow_redirects=True)
        self.assertIn(b'need to clock in first', response.data)
    
    # Leave Request Tests
    def test_leave_request_creation(self):
        """Test creating a leave request"""
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'User123#'
        })
        
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        next_week = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        response = self.app.post('/leave_request', data={
            'start_date': tomorrow,
            'end_date': next_week,
            'leave_type': 'vacation',
            'reason': 'Family trip'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Leave request submitted', response.data)
        
        # Verify leave request was created
        user = User.query.filter_by(username='testuser').first()
        leave = LeaveRequest.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(leave)
        self.assertEqual(leave.status, 'pending')
    
    def test_invalid_leave_dates(self):
        """Test leave request with invalid dates"""
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'User123#'
        })
        
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = self.app.post('/leave_request', data={
            'start_date': tomorrow,
            'end_date': yesterday,
            'leave_type': 'vacation',
            'reason': 'Invalid dates'
        }, follow_redirects=True)
        
        self.assertIn(b'End date must be after start date', response.data)
    
    # Admin Tests
    def test_admin_access(self):
        """Test admin dashboard access"""
        self.app.post('/login', data={
            'username': 'testadmin',
            'password': 'Admin123#'
        })
        
        response = self.app.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)
    
    def test_non_admin_access_denied(self):
        """Test non-admin cannot access admin pages"""
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'User123#'
        })
        
        response = self.app.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', response.data)
    
    def test_admin_create_user(self):
        """Test admin creating a new user"""
        self.app.post('/login', data={
            'username': 'testadmin',
            'password': 'Admin123#'
        })
        
        response = self.app.post('/admin/create_user', data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'NewUser123#',
            'is_admin': ''
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify user was created
        new_user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.email, 'newuser@test.com')
    
    def test_admin_delete_user(self):
        """Test admin deleting a user"""
        self.app.post('/login', data={
            'username': 'testadmin',
            'password': 'Admin123#'
        })
        
        user = User.query.filter_by(username='testuser').first()
        response = self.app.post(f'/admin/delete_user/{user.id}', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify user was deleted
        deleted_user = User.query.filter_by(username='testuser').first()
        self.assertIsNone(deleted_user)
    
    def test_admin_approve_leave(self):
        """Test admin approving leave request"""
        # Create leave request first
        user = User.query.filter_by(username='testuser').first()
        leave = LeaveRequest(
            user_id=user.id,
            start_date=datetime.utcnow().date(),
            end_date=(datetime.utcnow() + timedelta(days=3)).date(),
            leave_type='sick',
            reason='Medical appointment'
        )
        db.session.add(leave)
        db.session.commit()
        
        # Admin login and approve
        self.app.post('/login', data={
            'username': 'testadmin',
            'password': 'Admin123#'
        })
        
        response = self.app.post(f'/admin/process_leave/{leave.id}', data={
            'action': 'approve'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify leave was approved
        updated_leave = LeaveRequest.query.get(leave.id)
        self.assertEqual(updated_leave.status, 'approved')
    
    # Security Tests
    def test_login_attempt_logging(self):
        """Test that login attempts are logged"""
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'WrongPassword'
        })
        
        user = User.query.filter_by(username='testuser').first()
        attempts = LoginAttempt.query.filter_by(user_id=user.id).all()
        
        self.assertTrue(len(attempts) > 0)
        self.assertFalse(attempts[0].success)
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        user = User.query.filter_by(username='testuser').first()
        
        # Password should not be stored in plain text
        self.assertNotEqual(user.password_hash, 'User123#')
        
        # But should verify correctly
        self.assertTrue(user.check_password('User123#'))
        self.assertFalse(user.check_password('WrongPassword'))
    
    def test_system_logging(self):
        """Test system activity logging"""
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'User123#'
        })
        
        logs = SystemLog.query.all()
        self.assertTrue(len(logs) > 0)
    
    def test_unauthorized_access(self):
        """Test that protected routes require login"""
        response = self.app.get('/dashboard', follow_redirects=True)
        self.assertIn(b'login', response.data.lower())
    
    # Model Tests
    def test_user_model(self):
        """Test User model methods"""
        user = User(username='modeltest', email='model@test.com')
        user.set_password('Test123#')
        
        self.assertTrue(user.check_password('Test123#'))
        self.assertFalse(user.check_password('WrongPassword'))
    
    def test_attendance_relationship(self):
        """Test User-Attendance relationship"""
        user = User.query.filter_by(username='testuser').first()
        
        attendance = Attendance(
            user_id=user.id,
            date=datetime.utcnow().date(),
            clock_in_time=datetime.utcnow()
        )
        db.session.add(attendance)
        db.session.commit()
        
        self.assertEqual(len(user.attendance_records), 1)
        self.assertEqual(user.attendance_records[0].user, user)

def run_tests():
    """Run all tests and generate report"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TimeAttendanceSystemTestCase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result

if __name__ == '__main__':
    run_tests()