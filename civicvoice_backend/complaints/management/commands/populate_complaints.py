from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from django.core.files.base import ContentFile
import os

from civicvoice_backend.complaints.models import (
    ComplaintCategory, ComplaintSubCategory, ComplaintTag, Location,
    Complaint, ComplaintComment, ComplaintReaction, ComplaintStatus,
    ComplaintPriority, ComplaintPrivacy, ComplaintAttachment, ComplaintShare,
    ComplaintFollower, ComplaintReport, ComplaintStatusHistory
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate the database with sample complaint data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of sample users to create',
        )
        parser.add_argument(
            '--complaints',
            type=int,
            default=50,
            help='Number of sample complaints to create',
        )
        parser.add_argument(
            '--skip-related',
            action='store_true',
            help='Skip creating related data (attachments, shares, etc.)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting to populate complaint data...')
        )

        # Create categories and subcategories
        self.create_categories()
        
        # Create tags
        self.create_tags()
        
        # Create locations
        self.create_locations()
        
        # Create sample users if they don't exist
        self.create_users(options['users'])
        
        # Create complaints
        self.create_complaints(options['complaints'])
        
        # Create additional data for all tables (unless skipped)
        if not options['skip_related']:
            self.create_complaint_attachments()
            self.create_complaint_shares()
            self.create_complaint_followers()
            self.create_complaint_reports()
            self.create_status_history()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated complaint data!')
        )

    def create_categories(self):
        """Create complaint categories and subcategories"""
        categories_data = [
            {
                'name': 'Police Services',
                'description': 'Issues related to police services and law enforcement',
                'icon': 'fas fa-shield-alt',
                'color': '#007bff',
                'department_email': 'police@government.bd',
                'department_phone': '+880-2-9123456',
                'subcategories': [
                    'Theft/Robbery Report',
                    'Traffic Violation',
                    'Domestic Violence',
                    'Cybercrime',
                    'Missing Person',
                    'Police Misconduct',
                    'Emergency Response'
                ]
            },
            {
                'name': 'Municipal Services',
                'description': 'City services like water, electricity, waste management',
                'icon': 'fas fa-city',
                'color': '#28a745',
                'department_email': 'municipal@citycouncil.bd',
                'department_phone': '+880-2-9234567',
                'subcategories': [
                    'Water Supply Issues',
                    'Electricity Problems',
                    'Garbage Collection',
                    'Street Lighting',
                    'Road Maintenance',
                    'Sewerage Problems',
                    'Building Permits'
                ]
            },
            {
                'name': 'Healthcare',
                'description': 'Public health services and medical facilities',
                'icon': 'fas fa-hospital',
                'color': '#dc3545',
                'department_email': 'health@ministry.gov.bd',
                'department_phone': '+880-2-9345678',
                'subcategories': [
                    'Hospital Services',
                    'Medicine Shortage',
                    'Doctor Availability',
                    'Medical Equipment',
                    'Vaccination Issues',
                    'Emergency Services',
                    'Health Insurance'
                ]
            },
            {
                'name': 'Education',
                'description': 'Schools, colleges, and educational institutions',
                'icon': 'fas fa-graduation-cap',
                'color': '#ffc107',
                'department_email': 'education@ministry.gov.bd',
                'department_phone': '+880-2-9456789',
                'subcategories': [
                    'School Infrastructure',
                    'Teacher Quality',
                    'Admission Issues',
                    'Scholarship Problems',
                    'Educational Materials',
                    'Examination Issues',
                    'Student Safety'
                ]
            },
            {
                'name': 'Transportation',
                'description': 'Public transport and traffic management',
                'icon': 'fas fa-bus',
                'color': '#6610f2',
                'department_email': 'transport@ministry.gov.bd',
                'department_phone': '+880-2-9567890',
                'subcategories': [
                    'Public Bus Services',
                    'Traffic Management',
                    'Road Conditions',
                    'Parking Issues',
                    'Transport Safety',
                    'Fare Issues',
                    'Schedule Problems'
                ]
            },
            {
                'name': 'Environment',
                'description': 'Environmental issues and pollution',
                'icon': 'fas fa-leaf',
                'color': '#20c997',
                'department_email': 'environment@ministry.gov.bd',
                'department_phone': '+880-2-9678901',
                'subcategories': [
                    'Air Pollution',
                    'Water Pollution',
                    'Noise Pollution',
                    'Waste Management',
                    'Tree Cutting',
                    'Industrial Pollution',
                    'Environmental Violations'
                ]
            },
            {
                'name': 'Government Services',
                'description': 'General government services and administration',
                'icon': 'fas fa-landmark',
                'color': '#6c757d',
                'department_email': 'admin@government.bd',
                'department_phone': '+880-2-9789012',
                'subcategories': [
                    'Document Processing',
                    'License Issues',
                    'Tax Problems',
                    'Pension Issues',
                    'Land Records',
                    'Corruption Report',
                    'Service Delays'
                ]
            }
        ]

        for cat_data in categories_data:
            subcategories_data = cat_data.pop('subcategories')
            category, created = ComplaintCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            
            if created:
                self.stdout.write(f'Created category: {category.name}')
            
            # Create subcategories
            for subcat_name in subcategories_data:
                subcat, sub_created = ComplaintSubCategory.objects.get_or_create(
                    category=category,
                    name=subcat_name,
                    defaults={'description': f'{subcat_name} related issues'}
                )
                if sub_created:
                    self.stdout.write(f'  Created subcategory: {subcat.name}')

    def create_tags(self):
        """Create complaint tags"""
        tags_data = [
            {'name': 'urgent', 'color': '#dc3545'},
            {'name': 'resolved', 'color': '#28a745'},
            {'name': 'pending', 'color': '#ffc107'},
            {'name': 'duplicate', 'color': '#6c757d'},
            {'name': 'important', 'color': '#fd7e14'},
            {'name': 'feedback', 'color': '#20c997'},
            {'name': 'suggestion', 'color': '#6f42c1'},
            {'name': 'complaint', 'color': '#e83e8c'},
            {'name': 'public-safety', 'color': '#dc3545'},
            {'name': 'infrastructure', 'color': '#007bff'},
            {'name': 'service-quality', 'color': '#17a2b8'},
            {'name': 'corruption', 'color': '#343a40'},
        ]

        for tag_data in tags_data:
            tag, created = ComplaintTag.objects.get_or_create(
                name=tag_data['name'],
                defaults=tag_data
            )
            if created:
                self.stdout.write(f'Created tag: {tag.name}')

    def create_locations(self):
        """Create sample locations"""
        locations_data = [
            {
                'country': 'Bangladesh',
                'state': 'Dhaka Division',
                'city': 'Dhaka',
                'area': 'Dhanmondi',
                'postal_code': '1205',
                'address': 'Road 27, Dhanmondi, Dhaka',
                'latitude': 23.7461,
                'longitude': 90.3742
            },
            {
                'country': 'Bangladesh',
                'state': 'Dhaka Division',
                'city': 'Dhaka',
                'area': 'Gulshan',
                'postal_code': '1212',
                'address': 'Gulshan Avenue, Gulshan-1, Dhaka',
                'latitude': 23.7925,
                'longitude': 90.4077
            },
            {
                'country': 'Bangladesh',
                'state': 'Dhaka Division',
                'city': 'Dhaka',
                'area': 'Uttara',
                'postal_code': '1230',
                'address': 'Sector 7, Uttara, Dhaka',
                'latitude': 23.8759,
                'longitude': 90.3795
            },
            {
                'country': 'Bangladesh',
                'state': 'Dhaka Division',
                'city': 'Dhaka',
                'area': 'Mirpur',
                'postal_code': '1216',
                'address': 'Mirpur-1, Dhaka',
                'latitude': 23.8103,
                'longitude': 90.3594
            },
            {
                'country': 'Bangladesh',
                'state': 'Dhaka Division',
                'city': 'Dhaka',
                'area': 'Old Dhaka',
                'postal_code': '1100',
                'address': 'Lalbagh, Old Dhaka',
                'latitude': 23.7104,
                'longitude': 90.4074
            },
            {
                'country': 'Bangladesh',
                'state': 'Chittagong Division',
                'city': 'Chittagong',
                'area': 'Nasirabad',
                'postal_code': '4000',
                'address': 'Nasirabad Housing Society, Chittagong',
                'latitude': 22.3569,
                'longitude': 91.7832
            },
            {
                'country': 'Bangladesh',
                'state': 'Chittagong Division',
                'city': 'Chittagong',
                'area': 'Agrabad',
                'postal_code': '4100',
                'address': 'Agrabad Commercial Area, Chittagong',
                'latitude': 22.3288,
                'longitude': 91.8052
            },
            {
                'country': 'Bangladesh',
                'state': 'Sylhet Division',
                'city': 'Sylhet',
                'area': 'Zindabazar',
                'postal_code': '3100',
                'address': 'Zindabazar, Sylhet',
                'latitude': 24.8949,
                'longitude': 91.8687
            },
            {
                'country': 'Bangladesh',
                'state': 'Khulna Division',
                'city': 'Khulna',
                'area': 'Shibbari',
                'postal_code': '9000',
                'address': 'Shibbari More, Khulna',
                'latitude': 22.8456,
                'longitude': 89.5403
            },
            {
                'country': 'Bangladesh',
                'state': 'Rajshahi Division',
                'city': 'Rajshahi',
                'area': 'Saheb Bazar',
                'postal_code': '6000',
                'address': 'Saheb Bazar Zero Point, Rajshahi',
                'latitude': 24.3745,
                'longitude': 88.6042
            },
            {
                'country': 'Bangladesh',
                'state': 'Rangpur Division',
                'city': 'Rangpur',
                'area': 'Modern More',
                'postal_code': '5400',
                'address': 'Modern More, Rangpur',
                'latitude': 25.7439,
                'longitude': 89.2752
            },
            {
                'country': 'Bangladesh',
                'state': 'Barisal Division',
                'city': 'Barisal',
                'area': 'Band Road',
                'postal_code': '8200',
                'address': 'Band Road, Barisal',
                'latitude': 22.7010,
                'longitude': 90.3535
            }
        ]

        for loc_data in locations_data:
            location, created = Location.objects.get_or_create(
                country=loc_data['country'],
                city=loc_data['city'],
                area=loc_data['area'],
                defaults=loc_data
            )
            if created:
                self.stdout.write(f'Created location: {location}')

    def create_users(self, count):
        """Create sample users with realistic data"""
        # Sample realistic user data for Bangladesh
        user_data = [
            {'name': 'Md. Abdul Rahman', 'email': 'abdul.rahman@email.com', 'phone': '+8801711123456'},
            {'name': 'Fatima Khatun', 'email': 'fatima.khatun@gmail.com', 'phone': '+8801912345678'},
            {'name': 'Mohammad Hasan', 'email': 'mohammad.hasan@yahoo.com', 'phone': '+8801555666777'},
            {'name': 'Rashida Begum', 'email': 'rashida.begum@hotmail.com', 'phone': '+8801777888999'},
            {'name': 'Karim Uddin Ahmed', 'email': 'karim.ahmed@outlook.com', 'phone': '+8801888999000'},
            {'name': 'Nasreen Akter', 'email': 'nasreen.akter@email.com', 'phone': '+8801999000111'},
            {'name': 'Dr. Shahidul Islam', 'email': 'dr.shahidul@gmail.com', 'phone': '+8801666777888'},
            {'name': 'Salma Khatun', 'email': 'salma.khatun@yahoo.com', 'phone': '+8801444555666'},
            {'name': 'Md. Rafiqul Islam', 'email': 'rafiqul.islam@hotmail.com', 'phone': '+8801333444555'},
            {'name': 'Sultana Razia', 'email': 'sultana.razia@gmail.com', 'phone': '+8801222333444'},
            {'name': 'Prof. Abdul Karim', 'email': 'prof.karim@university.edu.bd', 'phone': '+8801111222333'},
            {'name': 'Rokeya Khatun', 'email': 'rokeya.khatun@email.com', 'phone': '+8801234567890'},
            {'name': 'Md. Aminul Haque', 'email': 'aminul.haque@gmail.com', 'phone': '+8801345678901'},
            {'name': 'Marium Begum', 'email': 'marium.begum@yahoo.com', 'phone': '+8801456789012'},
            {'name': 'Golam Mostafa', 'email': 'golam.mostafa@outlook.com', 'phone': '+8801567890123'},
            {'name': 'Hasina Akter', 'email': 'hasina.akter@hotmail.com', 'phone': '+8801678901234'},
            {'name': 'Md. Shahjahan Ali', 'email': 'shahjahan.ali@gmail.com', 'phone': '+8801789012345'},
            {'name': 'Khaleda Rahman', 'email': 'khaleda.rahman@email.com', 'phone': '+8801890123456'},
            {'name': 'Abdul Majid', 'email': 'abdul.majid@yahoo.com', 'phone': '+8801901234567'},
            {'name': 'Ruma Khatun', 'email': 'ruma.khatun@gmail.com', 'phone': '+8801012345678'},
        ]
        
        existing_count = User.objects.count()
        if existing_count >= count:
            self.stdout.write(f'Enough users exist ({existing_count})')
            return

        created_count = 0
        for i in range(count):
            if i < len(user_data):
                user_info = user_data[i]
                email = user_info['email']
                name = user_info['name']
                phone = user_info.get('phone', f'+88017{random.randint(10000000, 99999999)}')
            else:
                email = f'user{i+1}@example.com'
                name = f'User {i+1}'
                phone = f'+88017{random.randint(10000000, 99999999)}'
            
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    name=name,
                    password='testpass123'
                )
                # If the User model has a phone field, set it
                if hasattr(user, 'phone'):
                    user.phone = phone
                    user.save()
                
                created_count += 1
                self.stdout.write(f'Created user: {user.name} ({user.email})')
        
        self.stdout.write(f'Created {created_count} new users')

    def create_complaints(self, count):
        """Create sample complaints"""
        categories = list(ComplaintCategory.objects.all())
        tags = list(ComplaintTag.objects.all())
        locations = list(Location.objects.all())
        users = list(User.objects.all())

        if not categories or not users:
            self.stdout.write(
                self.style.ERROR('Need categories and users to create complaints')
            )
            return

        complaint_templates = [
            {
                'title': 'Street lights not working in {}',
                'description': 'The street lights in {} have not been working for the past {} days. This is causing safety concerns for residents, especially during night time. The area becomes very dark and unsafe for pedestrians and vehicles.',
                'priority': ComplaintPriority.HIGH,
                'privacy': ComplaintPrivacy.PUBLIC
            },
            {
                'title': 'Water supply disruption in {}',
                'description': 'There has been no water supply in {} for the last {} days. Residents are facing severe difficulties and have to buy water from outside sources. This is affecting daily life and hygiene.',
                'priority': ComplaintPriority.URGENT,
                'privacy': ComplaintPrivacy.PUBLIC
            },
            {
                'title': 'Garbage collection irregular in {}',
                'description': 'Garbage collection in {} has been very irregular for the past {} weeks. Waste is accumulating on the streets, creating health hazards and bad smell in the neighborhood.',
                'priority': ComplaintPriority.MEDIUM,
                'privacy': ComplaintPrivacy.PUBLIC
            },
            {
                'title': 'Road condition very poor in {}',
                'description': 'The road condition in {} is extremely poor with many potholes. It has been like this for {} months. Vehicles get damaged and it causes traffic jams. Urgent repair needed.',
                'priority': ComplaintPriority.HIGH,
                'privacy': ComplaintPrivacy.PUBLIC
            },
            {
                'title': 'Noise pollution from construction in {}',
                'description': 'There is excessive noise pollution from construction activities in {} going on for {} weeks. It continues even during night time and early morning, disturbing residents sleep and daily activities.',
                'priority': ComplaintPriority.MEDIUM,
                'privacy': ComplaintPrivacy.PUBLIC
            }
        ]

        for i in range(count):
            template = random.choice(complaint_templates)
            location = random.choice(locations) if locations else None
            area_name = location.area if location else 'the area'
            duration = random.randint(3, 30)
            category = random.choice(categories)
            
            # Get subcategories for the selected category
            subcategories = list(category.subcategories.all())
            subcategory = random.choice(subcategories) if subcategories else None
            
            # Set due date based on priority
            if template['priority'] == ComplaintPriority.URGENT:
                due_days = random.randint(1, 3)
            elif template['priority'] == ComplaintPriority.HIGH:
                due_days = random.randint(3, 7)
            else:
                due_days = random.randint(7, 30)
            
            created_date = timezone.now() - timedelta(days=random.randint(1, 30))
            due_date = created_date + timedelta(days=due_days)
            
            complaint = Complaint.objects.create(
                title=template['title'].format(area_name),
                description=template['description'].format(area_name, area_name, duration),
                category=category,
                subcategory=subcategory,
                priority=template['priority'],
                privacy=template['privacy'],
                status=ComplaintStatus.SUBMITTED,  # Start with submitted status
                location=location,
                created_by=random.choice(users),
                allow_comments=True,
                allow_sharing=True,
                incident_date=timezone.now() - timedelta(days=random.randint(1, 30)),
                due_date=due_date,
                view_count=random.randint(0, 100),
                reaction_count=0,  # Will be updated when reactions are created
                comment_count=0,   # Will be updated when comments are created
                created_at=created_date,
                updated_at=created_date
            )

            # Add random tags
            complaint.tags.set(random.sample(tags, random.randint(1, 3)))

            # Create some comments
            comment_count = 0
            for j in range(random.randint(0, 5)):
                comment_content = random.choice([
                    f'This is indeed a serious issue in {area_name}. I have also faced similar problems.',
                    'Thank you for raising this concern. Hope authorities take quick action.',
                    'I live in the same area and can confirm this problem exists.',
                    'This issue needs immediate attention from the concerned department.',
                    'I support this complaint. Similar situation in our locality too.',
                    'Authorities should prioritize this type of civic issues.',
                ])
                
                comment = ComplaintComment.objects.create(
                    complaint=complaint,
                    content=comment_content,
                    created_by=random.choice(users),
                    is_official=random.choice([True, False]) if random.random() > 0.8 else False,
                    is_anonymous=random.choice([True, False]) if random.random() > 0.7 else False,
                    created_at=created_date + timedelta(days=random.randint(0, 15))
                )
                comment_count += 1

            # Create some reactions
            reaction_count = 0
            for k in range(random.randint(0, 10)):
                user = random.choice(users)
                if not ComplaintReaction.objects.filter(complaint=complaint, user=user).exists():
                    ComplaintReaction.objects.create(
                        complaint=complaint,
                        user=user,
                        reaction_type=random.choice([r[0] for r in ComplaintReaction.ReactionType.choices]),
                        created_at=created_date + timedelta(days=random.randint(0, 20))
                    )
                    reaction_count += 1
            
            # Update counts
            complaint.comment_count = comment_count
            complaint.reaction_count = reaction_count
            complaint.save()

            if i % 10 == 0:
                self.stdout.write(f'Created {i+1} complaints...')

        self.stdout.write(f'Created {count} complaints successfully!')

    def create_complaint_attachments(self):
        """Create sample complaint attachments"""
        complaints = Complaint.objects.all()[:20]  # Add attachments to first 20 complaints
        
        attachment_types = [
            {'name': 'photo_evidence.jpg', 'file_type': 'image/jpeg', 'size': 2048000},
            {'name': 'document.pdf', 'file_type': 'application/pdf', 'size': 512000},
            {'name': 'video_proof.mp4', 'file_type': 'video/mp4', 'size': 10240000},
            {'name': 'location_map.png', 'file_type': 'image/png', 'size': 1024000},
            {'name': 'official_letter.pdf', 'file_type': 'application/pdf', 'size': 256000},
        ]
        
        for complaint in complaints:
            # Add 1-3 attachments per complaint
            num_attachments = random.randint(1, 3)
            for i in range(num_attachments):
                attachment_data = random.choice(attachment_types)
                
                # Create a dummy file content
                dummy_content = f"Dummy content for {attachment_data['name']}"
                
                attachment = ComplaintAttachment.objects.create(
                    complaint=complaint,
                    original_name=attachment_data['name'],
                    file_size=attachment_data['size'],
                    file_type=attachment_data['file_type'],
                    description=f"Supporting document {i+1} for complaint {complaint.complaint_number}"
                )
                self.stdout.write(f'Created attachment: {attachment.original_name} for complaint {complaint.complaint_number}')

    def create_complaint_shares(self):
        """Create complaint shares data"""
        complaints = Complaint.objects.filter(allow_sharing=True)[:15]
        users = list(User.objects.all())
        
        platforms = ['email', 'facebook', 'twitter', 'whatsapp', 'telegram', 'messenger']
        
        for complaint in complaints:
            # Create 1-5 shares per complaint
            num_shares = random.randint(1, 5)
            for i in range(num_shares):
                shared_by = random.choice(users)
                
                # Avoid duplicate shares by same user
                if not ComplaintShare.objects.filter(complaint=complaint, shared_by=shared_by).exists():
                    share = ComplaintShare.objects.create(
                        complaint=complaint,
                        shared_by=shared_by,
                        platform=random.choice(platforms),
                        created_at=timezone.now() - timedelta(days=random.randint(0, 30))
                    )
                    self.stdout.write(f'Created share for complaint {complaint.complaint_number} by {shared_by.name}')

    def create_complaint_followers(self):
        """Create complaint followers"""
        complaints = Complaint.objects.all()[:20]
        users = list(User.objects.all())
        
        for complaint in complaints:
            # Each complaint gets 2-8 followers
            num_followers = random.randint(2, 8)
            selected_users = random.sample(users, min(num_followers, len(users)))
            
            for user in selected_users:
                if not ComplaintFollower.objects.filter(complaint=complaint, user=user).exists():
                    follower = ComplaintFollower.objects.create(
                        complaint=complaint,
                        user=user,
                        notify_status_change=random.choice([True, False]),
                        notify_new_comment=random.choice([True, False]),
                        notify_resolution=random.choice([True, False]),
                        created_at=timezone.now() - timedelta(days=random.randint(0, 20))
                    )
                    self.stdout.write(f'User {user.name} is now following complaint {complaint.complaint_number}')

    def create_complaint_reports(self):
        """Create complaint reports (reports about inappropriate complaints)"""
        complaints = Complaint.objects.all()[:10]  # Add reports to first 10 complaints
        users = list(User.objects.all())
        
        report_reasons = [r[0] for r in ComplaintReport.ReportReason.choices]
        
        for complaint in complaints:
            # Some complaints get reported 1-2 times
            if random.random() > 0.5:  # 50% chance of being reported
                num_reports = random.randint(1, 2)
                for i in range(num_reports):
                    reporter = random.choice(users)
                    
                    # Avoid duplicate reports by same user
                    if not ComplaintReport.objects.filter(complaint=complaint, reported_by=reporter).exists():
                        report = ComplaintReport.objects.create(
                            complaint=complaint,
                            reason=random.choice(report_reasons),
                            description=f"This complaint seems inappropriate because of {random.choice(['spam content', 'false information', 'inappropriate language', 'duplicate complaint'])}",
                            reported_by=reporter,
                            is_resolved=random.choice([True, False]),
                            created_at=timezone.now() - timedelta(days=random.randint(1, 15))
                        )
                        
                        # If resolved, add resolution details
                        if report.is_resolved:
                            report.resolved_by = random.choice(users)
                            report.resolved_at = report.created_at + timedelta(days=random.randint(1, 7))
                            report.save()
                        
                        self.stdout.write(f'Created report for complaint {complaint.complaint_number} by {reporter.name}')

    def create_status_history(self):
        """Create complaint status history"""
        complaints = Complaint.objects.all()
        users = list(User.objects.all())
        
        for complaint in complaints:
            # Create 2-4 status changes per complaint
            num_changes = random.randint(2, 4)
            current_date = complaint.created_at
            current_status = ComplaintStatus.SUBMITTED
            
            for i in range(num_changes):
                # Choose next status progression
                if current_status == ComplaintStatus.SUBMITTED:
                    next_status = random.choice([ComplaintStatus.UNDER_REVIEW, ComplaintStatus.IN_PROGRESS])
                elif current_status == ComplaintStatus.UNDER_REVIEW:
                    next_status = random.choice([ComplaintStatus.IN_PROGRESS, ComplaintStatus.PENDING_INFO])
                elif current_status == ComplaintStatus.IN_PROGRESS:
                    next_status = random.choice([ComplaintStatus.RESOLVED, ComplaintStatus.PENDING_INFO, ComplaintStatus.ESCALATED])
                elif current_status == ComplaintStatus.PENDING_INFO:
                    next_status = random.choice([ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED])
                else:
                    break  # No more status changes after resolved/rejected/escalated/closed
                
                change_date = current_date + timedelta(days=random.randint(1, 7))
                
                # Create status history entry
                history = ComplaintStatusHistory.objects.create(
                    complaint=complaint,
                    previous_status=current_status,
                    new_status=next_status,
                    reason=self.get_status_change_reason(current_status, next_status),
                    changed_by=random.choice(users),
                    created_at=change_date
                )
                
                current_status = next_status
                current_date = change_date
                
                self.stdout.write(f'Status changed for complaint {complaint.complaint_number}: {history.previous_status} → {history.new_status}')
            
            # Update complaint's final status
            complaint.status = current_status
            if current_status == ComplaintStatus.RESOLVED:
                complaint.resolved_at = current_date
            complaint.save()

    def get_status_change_reason(self, previous_status, new_status):
        """Get appropriate reason for status change"""
        reasons = {
            (ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW): "Initial review started by admin team",
            (ComplaintStatus.UNDER_REVIEW, ComplaintStatus.IN_PROGRESS): "Complaint assigned to relevant department",
            (ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED): "Issue has been successfully resolved",
            (ComplaintStatus.IN_PROGRESS, ComplaintStatus.PENDING_INFO): "Additional information or resources needed",
            (ComplaintStatus.PENDING_INFO, ComplaintStatus.IN_PROGRESS): "Required information obtained, resuming work",
            (ComplaintStatus.IN_PROGRESS, ComplaintStatus.ESCALATED): "Issue requires higher authority intervention",
            (ComplaintStatus.SUBMITTED, ComplaintStatus.IN_PROGRESS): "Complaint directly assigned to department",
            (ComplaintStatus.UNDER_REVIEW, ComplaintStatus.PENDING_INFO): "More details needed from complainant",
            (ComplaintStatus.PENDING_INFO, ComplaintStatus.RESOLVED): "Issue resolved with provided information",
        }
        
        return reasons.get((previous_status, new_status), "Status updated as per standard procedure")
