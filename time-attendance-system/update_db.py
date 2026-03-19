from app import app, db

def init_database():
    """Initialize database with all tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        print("\n" + "=" * 70)
        print(" " * 15 + "DATABASE INITIALIZATION COMPLETE")
        print("=" * 70)
        print("\n✓ Database file created: attendance_system.db")
        print("\n✓ The following tables were created successfully:\n")
        print("  1. user              - Stores user accounts and credentials")
        print("  2. attendance        - Records clock in/out times")
        print("  3. leave_request     - Manages leave applications")
        print("  4. login_attempt     - Tracks login security")
        print("  5. admin_action      - Logs admin activities")
        print("  6. system_log        - System-wide activity logging")
        print("\n" + "=" * 70)
        print("✓ Database is ready to use!")
        print("=" * 70)
        print("\n✓ Next step: Run 'python create_admin.py' to create admin user")
        print("=" * 70 + "\n")

if __name__ == '__main__':
    init_database()