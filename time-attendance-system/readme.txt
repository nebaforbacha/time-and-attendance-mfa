Overview
This Time and Attendance Management System is a Flask-based web application that combines TOTP-based Multi-Factor Authentication with comprehensive time tracking capabilities to prevent workplace time theft and buddy punching. The system ensures that only authorized personnel can clock in/out for themselves through mandatory MFA verification, IP address logging, and comprehensive audit trails.
Key Highlights:
•	Force password change on first login
•	TOTP-based MFA (Google Authenticator compatible)
•	Real-time clock in/out tracking with IP logging
•	Automated work hours calculation
•	Leave request management with admin approval workflow
•	Email notifications for security events
•	Comprehensive system logging and audit trails
•	Admin dashboard for monitoring and reporting
________________________________________
Features
Security & Authentication
•	Multi-Factor Authentication (MFA): TOTP-based using Google Authenticator
•	Password Security: PBKDF2 hashing, complexity requirements, force change on first login
•	Password Reset: Secure token-based password reset via email
•	Session Management: Secure HTTP-only cookies with 8-hour timeout
•	IP Logging: Every login and attendance action logs IP address
•	Audit Trails: Comprehensive logging of all system activities
Time Tracking
•	Clock In/Out: Simple one-click time tracking
•	Automatic Calculations: Work hours calculated automatically
•	Duplicate Prevention: Cannot clock in twice on the same day
•	Attendance History: Complete record of all clock in/out events
•	Weekly Reports: View total hours worked per week
•	IP Address Verification: Location tracking for security
Leave Management
•	Leave Requests: Submit vacation, sick, or personal leave
•	Approval Workflow: Admin approval/rejection system
•	Status Tracking: Pending, approved, or rejected status
•	Leave History: Complete record of all leave requests
•	Email Notifications: Automated updates on request status
Admin Functions
•	User Management: Create, delete, and manage user accounts
•	Real-time Monitoring: See who is currently clocked in
•	Attendance Reports: Generate reports filtered by user and date
•	Leave Approvals: Review and process leave requests
•	System Logs: View all system activities and security events
•	Security Monitoring: Track failed login attempts and anomalies
Email Notifications
•	Account Creation: New users receive credentials via email
•	Password Changes: Confirmation emails for password updates
•	Password Reset: Secure reset links sent via email
•	Security Alerts: Notifications for suspicious activities
________________________________________
Problem Statement
Organizations face significant financial losses due to:
1.	Time Theft: Employees claiming payment for hours not worked
2.	Buddy Punching: Co-workers clocking in/out for absent colleagues
3.	Lack of Verification: Traditional systems rely solely on passwords
4.	Poor Audit Trails: Difficulty tracking and investigating time discrepancies
5.	Manual Calculations: Time-consuming and error-prone work hour tracking
________________________________________
Solution
This system addresses these problems through:
1. Multi-Factor Authentication
•	Requires physical device (phone) in addition to password
•	TOTP codes refresh every 30 seconds
•	Prevents password sharing and unauthorized access
2. IP Address Logging
•	Every clock in/out records IP address
•	Enables location-based anomaly detection
•	Creates verifiable audit trail
3. Force Password Change
•	New users must change temporary password
•	Prevents credential sharing
•	Enhances account security
4. Real-time Monitoring
•	Admins see who is currently working
•	Immediate detection of suspicious patterns
•	Comprehensive activity dashboards
5. Automated Calculations
•	Server-side timestamp recording (tamper-proof)
•	Automatic work hours calculation
•	Eliminates manual entry errors
________________________________________
 Technology Stack
Backend
•	Python 3.8+ - Core programming language
•	Flask 2.3.0 - Web framework
•	SQLAlchemy - ORM for database operations
•	SQLite - Lightweight embedded database
•	Flask-Login - User session management
•	Werkzeug - Password hashing (PBKDF2)
Security
•	PyOTP - TOTP implementation for MFA
•	QRCode - QR code generation for MFA setup
•	Secrets - Secure token generation
•	Flask-Mail - Email notifications
Frontend
•	HTML5 - Structure
•	Bootstrap 5 - Responsive UI framework
•	Font Awesome - Icon library
•	JavaScript - Client-side validation
Development Tools
•	Visual Studio Code - IDE
•	Git - Version control
•	Python unittest - Testing framework
Install Dependencies
pip install -r requirements.txt
python update_db.py
python create_admin.py
python app.py
Security Features
Authentication Security
•	TOTP-based Multi-Factor Authentication
•	Password complexity requirements (8+ chars, uppercase, lowercase, number, special char)
•	Password hashing using PBKDF2
•	Force password change on first login
•	Secure password reset via email tokens
•	Session timeout after 8 hours
•	HTTP-only secure cookies
Attendance Security
•	IP address logging for every clock in/out
•	Server-side timestamps (tamper-proof)
•	One clock-in per day limit
•	Immutable historical records
•	Real-time admin monitoring
Audit & Logging
•	All login attempts logged (success/failure)
•	All clock in/out events recorded
•	Admin actions tracked
•	System-wide activity logging
•	IP address captured for all events
Email Security
•	Password change confirmations
•	Password reset links (1-hour expiry)
•	New account notifications
•	Security event alerts




