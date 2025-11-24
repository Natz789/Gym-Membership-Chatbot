"""
Utility functions for the gym management system
"""
import base64
import qrcode
from io import BytesIO
from django.conf import settings


def generate_gcash_qr_code(amount, reference_no, merchant_name="GymFit Pro"):
    """
    Generate a dynamic QR code for GCash payments.

    Args:
        amount: Payment amount (decimal)
        reference_no: Payment reference number
        merchant_name: Name of the merchant (default: GymFit Pro)

    Returns:
        Base64 encoded PNG image string that can be used in img src
    """
    try:
        # GCash QR data format: merchant_name|amount|reference_no
        qr_data = f"{merchant_name}|₱{amount}|{reference_no}"

        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert image to bytes
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)

        # Encode to base64
        img_base64 = base64.b64encode(img_io.getvalue()).decode()

        # Return as data URI
        return f"data:image/png;base64,{img_base64}"

    except Exception as e:
        print(f"Error generating QR code: {e}")
        # Return empty string if generation fails
        return None


def get_gcash_merchant_info():
    """
    Get GCash merchant information from settings.

    Returns:
        Dictionary with merchant details
    """
    return {
        'merchant_name': getattr(settings, 'GCASH_MERCHANT_NAME', 'GymFit Pro'),
        'merchant_id': getattr(settings, 'GCASH_MERCHANT_ID', '09XX-XXX-XXXX'),
        'merchant_account': getattr(settings, 'GCASH_MERCHANT_ACCOUNT', 'GymFit Pro'),
    }
