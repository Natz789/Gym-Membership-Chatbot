from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with admin role'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username')
        parser.add_argument('--email', type=str, help='Admin email')
        parser.add_argument('--noinput', action='store_true', help='Non-interactive mode')

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        noinput = options.get('noinput', False)

        if noinput and username and email:
            # Non-interactive mode
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.ERROR(f'✗ User "{username}" already exists')
                )
                return

            user = User.objects.create_superuser(
                username=username,
                email=email,
                password='admin',  # Default password
                role='admin'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Admin user "{username}" created successfully')
            )
            self.stdout.write(
                self.style.WARNING(f'⚠ Default password: admin (Please change immediately!)')
            )
        else:
            # Interactive mode
            self.stdout.write(
                self.style.SUCCESS('Creating admin user with superuser privileges...\n')
            )
            
            # Get username
            while not username:
                username = input('Username: ').strip()
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.ERROR(f'✗ Username "{username}" already exists')
                    )
                    username = None

            # Get email
            while not email:
                email = input('Email address: ').strip()
                if email and User.objects.filter(email=email).exists():
                    self.stdout.write(
                        self.style.ERROR(f'✗ Email "{email}" already exists')
                    )
                    email = None

            # Get first name
            first_name = input('First name (optional): ').strip()

            # Get last name
            last_name = input('Last name (optional): ').strip()

            # Get mobile
            mobile_no = input('Mobile number (optional): ').strip()

            # Get password
            import getpass
            password = None
            while not password:
                password = getpass.getpass('Password: ')
                password_confirm = getpass.getpass('Password (again): ')
                
                if password != password_confirm:
                    self.stdout.write(
                        self.style.ERROR('✗ Passwords do not match')
                    )
                    password = None

            # Create admin user
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                mobile_no=mobile_no if mobile_no else None,
                role='admin'
            )

            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Admin user "{username}" created successfully!')
            )
            self.stdout.write(f'   Role: {user.role}')
            self.stdout.write(f'   Superuser: Yes')
            self.stdout.write(f'   Staff: Yes')