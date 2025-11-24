"""
Test suite for GymFit Pro system with focus on GCash QR code functionality
Tests payment flows, QR code generation, and data integrity
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    User, MembershipPlan, FlexibleAccess, UserMembership, Payment, WalkInPayment,
    AuditLog
)
from .utils import generate_gcash_qr_code, get_gcash_merchant_info

User = get_user_model()


class GCashQRCodeGenerationTest(TestCase):
    """Test QR code generation functionality"""

    def test_qr_code_generation_success(self):
        """Test that QR code is generated successfully"""
        qr_code = generate_gcash_qr_code(1500.00, "PAY-20251122-123456")

        self.assertIsNotNone(qr_code)
        self.assertTrue(qr_code.startswith('data:image/png;base64,'))
        self.assertGreater(len(qr_code), 500)  # QR code should be reasonably large

    def test_qr_code_with_different_amounts(self):
        """Test QR code generation with various amounts"""
        test_amounts = [100.00, 500.00, 1500.00, 4000.00, 14000.00]

        for amount in test_amounts:
            qr_code = generate_gcash_qr_code(amount, f"PAY-20251122-{amount}")
            self.assertIsNotNone(qr_code)
            self.assertTrue(qr_code.startswith('data:image/png;base64,'))

    def test_merchant_info_retrieval(self):
        """Test that merchant info is retrieved correctly"""
        merchant_info = get_gcash_merchant_info()

        self.assertIsNotNone(merchant_info)
        self.assertIn('merchant_name', merchant_info)
        self.assertIn('merchant_id', merchant_info)
        self.assertIn('merchant_account', merchant_info)
        self.assertEqual(merchant_info['merchant_name'], 'GymFit Pro')


class PaymentModelTest(TestCase):
    """Test Payment model functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testmember',
            email='test@gym.com',
            password='testpass123',
            first_name='Test',
            last_name='Member',
            role='member'
        )

        self.plan = MembershipPlan.objects.create(
            name='Test Plan',
            duration_days=30,
            price=Decimal('1500.00'),
            description='Test membership plan'
        )

        self.membership = UserMembership.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            status='pending'
        )

    def test_payment_creation_gcash(self):
        """Test creation of GCash payment"""
        payment = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.plan.price,
            method='gcash',
            payment_date=timezone.now()
        )

        self.assertEqual(payment.method, 'gcash')
        self.assertEqual(payment.status, 'pending')
        self.assertIsNotNone(payment.reference_no)
        self.assertTrue(payment.reference_no.startswith('PAY-'))

    def test_payment_reference_unique(self):
        """Test that payment references are unique"""
        payment1 = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.plan.price,
            method='gcash',
            payment_date=timezone.now()
        )

        payment2 = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.plan.price,
            method='gcash',
            payment_date=timezone.now()
        )

        self.assertNotEqual(payment1.reference_no, payment2.reference_no)

    def test_payment_confirmation(self):
        """Test payment confirmation"""
        staff = User.objects.create_user(
            username='teststaff',
            password='staff123',
            role='staff',
            is_staff=True
        )

        payment = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.plan.price,
            method='gcash',
            payment_date=timezone.now(),
            status='pending'
        )

        # Confirm payment
        payment.confirm(staff)

        # Verify payment status
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'confirmed')
        self.assertEqual(payment.approved_by, staff)
        self.assertIsNotNone(payment.approved_at)

    def test_payment_rejection(self):
        """Test payment rejection"""
        staff = User.objects.create_user(
            username='teststaff2',
            password='staff123',
            role='staff',
            is_staff=True
        )

        payment = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.plan.price,
            method='gcash',
            payment_date=timezone.now(),
            status='pending'
        )

        # Reject payment
        rejection_reason = 'Insufficient funds'
        payment.reject(staff, rejection_reason)

        # Verify payment status
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'rejected')
        self.assertEqual(payment.rejection_reason, rejection_reason)
        self.assertEqual(payment.approved_by, staff)


class WalkInPaymentTest(TestCase):
    """Test WalkInPayment model"""

    def setUp(self):
        """Set up test data"""
        self.staff = User.objects.create_user(
            username='teststaff',
            password='staff123',
            role='staff',
            is_staff=True
        )

        self.pass_type = FlexibleAccess.objects.create(
            name='Day Pass',
            duration_days=1,
            price=Decimal('100.00'),
            description='One day pass'
        )

    def test_walkin_payment_creation_gcash(self):
        """Test creation of GCash walk-in payment"""
        walkin = WalkInPayment.objects.create(
            pass_type=self.pass_type,
            customer_name='John Doe',
            mobile_no='09123456789',
            amount=self.pass_type.price,
            method='gcash',
            payment_date=timezone.now()
        )

        self.assertEqual(walkin.method, 'gcash')
        self.assertEqual(walkin.customer_name, 'John Doe')
        self.assertIsNotNone(walkin.reference_no)
        self.assertTrue(walkin.reference_no.startswith('WLK-'))

    def test_walkin_payment_without_customer_info(self):
        """Test anonymous walk-in payment"""
        walkin = WalkInPayment.objects.create(
            pass_type=self.pass_type,
            amount=self.pass_type.price,
            method='gcash',
            payment_date=timezone.now()
        )

        self.assertIsNone(walkin.customer_name)
        self.assertIsNone(walkin.mobile_no)
        self.assertIsNotNone(walkin.reference_no)

    def test_walkin_payment_reference_format(self):
        """Test walk-in reference number format"""
        walkin = WalkInPayment.objects.create(
            pass_type=self.pass_type,
            amount=self.pass_type.price,
            method='gcash',
            payment_date=timezone.now()
        )

        # Format should be WLK-YYYYMMDD-XXXXXX
        parts = walkin.reference_no.split('-')
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], 'WLK')
        self.assertEqual(len(parts[1]), 8)  # YYYYMMDD
        self.assertEqual(len(parts[2]), 6)  # Random numbers


class IntegrationTest(TestCase):
    """Integration tests for complete payment flows"""

    def setUp(self):
        """Set up test data"""
        self.staff = User.objects.create_user(
            username='staff_test',
            password='staff123',
            role='staff',
            is_staff=True
        )

        self.member = User.objects.create_user(
            username='member_test',
            password='member123',
            role='member'
        )

        self.plan = MembershipPlan.objects.create(
            name='Monthly',
            duration_days=30,
            price=Decimal('1500.00')
        )

    def test_complete_gcash_membership_flow(self):
        """Test complete flow: create member -> subscribe -> pay -> confirm"""
        # Member subscribes
        membership = UserMembership.objects.create(
            user=self.member,
            plan=self.plan,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            status='pending'
        )

        # Member pays with GCash
        payment = Payment.objects.create(
            user=self.member,
            membership=membership,
            amount=self.plan.price,
            method='gcash',
            payment_date=timezone.now(),
            status='pending'
        )

        # Verify QR code can be generated
        qr_code = generate_gcash_qr_code(payment.amount, payment.reference_no)
        self.assertIsNotNone(qr_code)

        # Staff confirms payment
        payment.confirm(self.staff)
        membership.status = 'active'
        membership.save()

        # Verify final state
        payment.refresh_from_db()
        membership.refresh_from_db()

        self.assertEqual(payment.status, 'confirmed')
        self.assertEqual(membership.status, 'active')

    def test_complete_gcash_walkin_flow(self):
        """Test complete walk-in GCash flow"""
        pass_type = FlexibleAccess.objects.create(
            name='Day Pass',
            duration_days=1,
            price=Decimal('100.00')
        )

        # Create walk-in payment
        walkin = WalkInPayment.objects.create(
            pass_type=pass_type,
            customer_name='Anonymous Customer',
            amount=pass_type.price,
            method='gcash',
            payment_date=timezone.now()
        )

        # Verify QR code can be generated
        qr_code = generate_gcash_qr_code(walkin.amount, walkin.reference_no)
        self.assertIsNotNone(qr_code)

        # Verify payment is recorded
        walkin.refresh_from_db()
        self.assertEqual(walkin.method, 'gcash')
        self.assertEqual(walkin.amount, Decimal('100.00'))

