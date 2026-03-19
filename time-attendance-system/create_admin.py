from app import app, db
from models import User

def create_admin():
    """Create default admin user"""
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print("=" * 60)
            print("Admin user already exists!")
            print("=" * 60)
            print("You can login with:")
            print("Username: admin")
            print("Password: Admin123#")
            print("=" * 60)
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@attendance.com',
            is_admin=True
        )
        admin.set_password('Admin123#')
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("✓ ADMIN USER CREATED SUCCESSFULLY!")
        print("=" * 60)
        print("\nLogin Credentials:")
        print("-" * 60)
        print("  Username: admin")
        print("  Password: Admin123#")
        print("-" * 60)
        print("\n⚠️  IMPORTANT: Change this password after first login!")
        print("\n✓ Next step: Run 'python app.py' to start the application")
        print("=" * 60 + "\n")

if __name__ == '__main__':
    create_admin()