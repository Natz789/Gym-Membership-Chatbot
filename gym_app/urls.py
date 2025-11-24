# Replace gym_app/urls.py with this:

from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),  # Legacy redirect
    path('register/step1/', views.register_step1, name='register_step1'),
    path('register/step2/', views.register_step2, name='register_step2'),
    path('register/step3/', views.register_step3, name='register_step3'),
    path('register/review/', views.register_review, name='register_review'),

    # Dashboard (role-based)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Membership management
    path('plans/', views.membership_plans_view, name='membership_plans'),
    path('plans/subscribe/<int:plan_id>/', views.subscribe_plan, name='subscribe_plan'),
    
    # Walk-in management (staff/admin)
    path('walkin/', views.walkin_purchase, name='walkin_purchase'),
    path('walkin/confirm/', views.walkin_confirm, name='walkin_confirm'),
    
    # Reports & Analytics (admin)
    path('reports/', views.reports_view, name='reports'),
    path('audit-trail/', views.audit_trail_view, name='audit_trail'),
    path('manage-plans/', views.manage_plans_view, name='manage_plans'),

    # Pending Payments (staff/admin)
    path('pending-payments/', views.pending_payments_view, name='pending_payments'),
    path('pending-payments/confirm/<int:payment_id>/', views.confirm_payment, name='confirm_payment'),
    path('pending-payments/reject/<int:payment_id>/', views.reject_payment, name='reject_payment'),

    # Archived Plans (admin)
    path('archived-plans/', views.archived_plans_view, name='archived_plans'),
    path('archive-membership/<int:plan_id>/', views.archive_membership_plan, name='archive_membership_plan'),
    path('archive-walkin/<int:plan_id>/', views.archive_walkin_plan, name='archive_walkin_plan'),
    path('restore-membership/<int:plan_id>/', views.restore_membership_plan, name='restore_membership_plan'),
    path('restore-walkin/<int:plan_id>/', views.restore_walkin_plan, name='restore_walkin_plan'),

    # Member management (admin/staff)
    path('members/', views.members_list, name='members_list'),
    path('members/<int:user_id>/', views.member_detail, name='member_detail'),
    path('create-staff/', views.create_staff_view, name='create_staff'),
    path('staff/<int:user_id>/', views.staff_detail, name='staff_detail'),
    path('staff/<int:user_id>/edit/', views.edit_staff, name='edit_staff'),

    path('membership/<int:membership_id>/cancel/', views.cancel_membership, name='cancel_membership'),
    path('cancel-membership/<int:membership_id>/', 
     views.cancel_membership_confirm, 
     name='cancel_membership_confirm'),

    # Profile Settings
    path('profile/', views.profile_settings, name='profile_settings'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Kiosk (no authentication required)
    path('kiosk/', views.kiosk_login, name='kiosk_login'),
    path('kiosk/success/<str:action>/<int:duration>/<int:user_id>/', views.kiosk_success, name='kiosk_success'),
    
    # Attendance reports (staff/admin)
    path('attendance/', views.attendance_report, name='attendance_report'),
    
    # Chatbot
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('api/chatbot/suggestions/', views.chatbot_suggestions, name='chatbot_suggestions'),
    path('api/chatbot/conversations/', views.chatbot_conversations_list, name='chatbot_conversations_list'),

    # Hero Section Management (Admin)
    path('admin/hero-sections/', views.manage_hero_sections, name='manage_hero_sections'),
    path('admin/hero-sections/create/', views.create_hero_section, name='create_hero_section'),
    path('admin/hero-sections/<int:section_id>/edit/', views.edit_hero_section, name='edit_hero_section'),
    path('admin/hero-sections/<int:section_id>/delete/', views.delete_hero_section, name='delete_hero_section'),

    # Gallery Management (Admin)
    path('admin/gallery/', views.manage_gallery, name='manage_gallery'),
    path('admin/gallery/upload/', views.upload_gallery_image, name='upload_gallery_image'),
]