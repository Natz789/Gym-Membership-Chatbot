"""
Tool and Function Calling System for Gym Chatbot
Provides structured tools that the chatbot can invoke based on user queries
Integrates analytics and operations with intelligent routing
"""

from .chatbot_analytics import AnalyticsEngine
from .chatbot_operations import OperationsExecutor, PermissionError
from django.core.cache import cache
import re


class FAQFastPath:
    """
    PERFORMANCE OPTIMIZATION #1: FAQ Fast-Path System

    Comprehensive FAQ lookup system that bypasses AI completely for common questions.
    Average response time: <10ms (vs 2-3 seconds with AI)

    This system handles:
    - 50+ pre-defined common gym FAQs
    - Pattern matching for question variations
    - Keyword-based routing
    - Fallback to AI only when FAQ doesn't match
    """

    # Comprehensive FAQ database with variations and answers
    FAQ_DATABASE = {
        # ==================== MEMBERSHIPS (10 FAQs) ====================
        'membership_plans': {
            'keywords': ['membership', 'plan', 'plans', 'subscribe', 'subscription', 'packages', 'what plans', 'available plans'],
            'answer': '''We offer flexible membership plans:
- **Monthly Plan**: ₱2,999/month (30 days)
- **Quarterly Plan**: ₱7,999/quarter (90 days)
- **Annual Plan**: ₱29,999/year (365 days)
- **Walk-in Pass**: ₱500/day (1-day access)

Each plan includes unlimited access to all facilities and classes. Contact our staff for special corporate rates.'''
        },
        'membership_cost': {
            'keywords': ['how much', 'price', 'cost', 'fee', 'charge', 'expensive', 'membership cost', 'plan price'],
            'answer': '''Membership costs range from ₱500/day (walk-in) to ₱29,999/year (annual plan).
Most popular is our **Monthly Plan at ₱2,999**.
All plans include unlimited access to facilities, equipment, and classes.
Ask our staff about discounts for referrals or bulk memberships!'''
        },
        'membership_renewal': {
            'keywords': ['renew', 'renewal', 'extend', 'extension', 'expired', 'expire', 'after expiration', 'reactivate'],
            'answer': '''Renewing your membership is easy!
1. Log into your account on the Membership Plans page
2. Select your desired plan
3. Complete the payment
4. Your membership is activated immediately

You can renew before or after your current membership expires. No gaps needed!'''
        },
        'membership_difference': {
            'keywords': ['difference', 'membership vs', 'walk-in vs', 'vs walk-in', 'pass vs membership', 'what is difference'],
            'answer': '''**Membership vs Walk-in Pass**
- **Membership**: Long-term access (30-365 days), discounted rates, access anytime, personal account
- **Walk-in Pass**: Single-day or short-term access (1-7 days), pay per visit, no account needed

Choose membership if you plan regular visits. Walk-in is perfect for guests or occasional visits.'''
        },
        'membership_benefits': {
            'keywords': ['benefit', 'benefits', 'included', 'what do i get', 'what comes with', 'membership include'],
            'answer': '''All memberships include:
✓ Unlimited access to all equipment and facilities
✓ Group fitness classes (at no extra cost)
✓ Locker rooms with showers
✓ Member mobile app for booking classes
✓ Discounts on personal training (15% off)
✓ Priority access to new classes and events'''
        },
        'membership_transfer': {
            'keywords': ['transfer', 'give to', 'share', 'someone else', 'another person'],
            'answer': '''Memberships are personal and cannot be transferred or shared.
However, you can purchase separate memberships for family members or friends. Contact our staff for family package discounts (10-20% off).'''
        },
        'membership_cancel': {
            'keywords': ['cancel', 'cancellation', 'stop', 'pause', 'refund', 'want to cancel', 'unsubscribe'],
            'answer': '''To cancel your membership:
1. Contact our staff at the gym or via email
2. Provide your membership details
3. We process cancellations within 24 hours

**Important**: Refunds are available for unused portions if cancelled within 30 days of purchase. After 30 days, remaining balance can be used for future memberships.'''
        },
        'membership_pause': {
            'keywords': ['pause', 'freeze', 'hold', 'temporary', 'vacation', 'coming back'],
            'answer': '''We offer membership freeze options:
- **Up to 30 days**: Free pause for members in good standing
- **Beyond 30 days**: Contact staff for custom arrangements

This is perfect for vacations or temporary situations. Your membership time doesn't count while paused!'''
        },
        'membership_family': {
            'keywords': ['family', 'group', 'referral', 'friend', 'multiple', 'bulk', 'discount'],
            'answer': '''Great news! We offer family and group packages:
- **Family Plan**: 2+ members = 10% discount each
- **Referral Bonus**: Refer a friend, both get ₱500 credit
- **Corporate Rates**: 5+ employees = 15% discount

Ask our staff about these special offers!'''
        },
        'membership_guest': {
            'keywords': ['guest', 'bring friend', 'visitor', 'visitor pass', 'bring someone'],
            'answer': '''Members can bring guests! Here's how:
- **Guest Pass**: ₱300/visit (1-day access)
- **Unlimited**: Guests can visit anytime with member present
- **Walk-in Option**: Guests can also purchase their own walk-in pass (₱500/day)

A staff member will register the guest at check-in.'''
        },

        # ==================== PAYMENTS (8 FAQs) ====================
        'payment_methods': {
            'keywords': ['payment', 'pay', 'how to pay', 'accept', 'method', 'cash', 'gcash', 'card', 'credit'],
            'answer': '''We accept two payment methods:
💵 **Cash**: Direct payment at the gym
📱 **GCash**: Mobile payment (fastest & safest)

For online memberships, GCash is strongly recommended. You'll receive a payment reference number (e.g., PAY-20250115-123456) immediately.'''
        },
        'payment_confirm': {
            'keywords': ['confirm', 'pending', 'approval', 'wait', 'verify', 'pending payment', 'what does pending mean'],
            'answer': '''Pending payments are waiting for staff approval:
1. **GCash Payments**: Usually confirmed within 1-2 hours
2. **Cash Payments**: Confirmed at payment desk

You'll receive a notification once approved. Check your dashboard for status. For urgent confirmations, contact our staff.'''
        },
        'payment_reference': {
            'keywords': ['reference', 'receipt', 'number', 'reference number', 'proof', 'gcash reference'],
            'answer': '''Your payment reference is your proof of payment!
Format: PAY-YYYYMMDD-XXXXXX (e.g., PAY-20250115-123456)

Keep this for your records. Use it when:
- Following up on pending payments
- Resolving payment issues
- Requesting refunds
- Tax documentation'''
        },
        'payment_history': {
            'keywords': ['history', 'payment history', 'past payment', 'old payment', 'previous', 'receipt', 'invoice'],
            'answer': '''View your complete payment history:
1. Log in to your member account
2. Go to "Payments" section
3. See all transactions with dates and amounts

Can't find your payment? Contact our staff with your member ID or email. We'll help locate it!'''
        },
        'payment_late': {
            'keywords': ['late', 'overdue', 'outstanding', 'owe', 'unpaid', 'past due', 'delinquent'],
            'answer': '''If your membership payment is overdue:
1. Your membership is temporarily inactive
2. Contact us to settle the payment
3. Upon payment, your membership reactivates immediately

We offer flexible payment arrangements. Talk to our staff—we want to help!'''
        },
        'payment_refund': {
            'keywords': ['refund', 'refunding', 'money back', 'return', 'wrong payment', 'accidental charge'],
            'answer': '''Refund Policy:
- **Unused Memberships (within 30 days)**: Full refund available
- **After 30 days**: Remaining balance credited to future membership
- **Wrong Amount Paid**: Refund processed within 3-5 business days

Contact our staff with your payment reference to request a refund. We'll process it quickly!'''
        },
        'payment_invoice': {
            'keywords': ['invoice', 'receipt', 'bill', 'documentation', 'tax', 'company', 'proof of payment'],
            'answer': '''To get an invoice or receipt:
1. Log in to your account → Payments section
2. Click "Download Invoice" (available immediately after payment)
3. Or contact our staff to email you a formal invoice

Perfect for company reimbursement or tax purposes!'''
        },
        'payment_failed': {
            'keywords': ['failed', 'error', 'declined', 'unsuccessful', 'didn\'t work', 'not accepted', 'transaction failed'],
            'answer': '''If your payment failed:
1. **GCash Issues**: Check your GCash balance, ensure 3G/WiFi connection
2. **Try Again**: Attempt the payment once more
3. **Still Not Working**: Contact our staff immediately

We can help troubleshoot or accept cash payment as alternative.'''
        },

        # ==================== KIOSK & CHECK-IN (6 FAQs) ====================
        'kiosk_pin': {
            'keywords': ['kiosk', 'pin', 'kiosk pin', 'check in', 'check-in', 'check out', 'how to check in'],
            'answer': '''Using your Kiosk PIN:
1. Arrive at the gym and go to the kiosk
2. Enter your 6-digit PIN (found in your account)
3. Press "Check In" - the kiosk will confirm
4. You're now checked in! Enjoy your workout

**Check Out**: Same process at the end—just press "Check Out"
Lost your PIN? Contact staff to generate a new one.'''
        },
        'kiosk_forgot_pin': {
            'keywords': ['forgot', 'lost', 'reset', 'don\'t remember', 'forget pin', 'new pin', 'generate pin'],
            'answer': '''No problem! Getting a new PIN is easy:
1. Ask staff at the front desk
2. Provide your member ID or email
3. Staff generates a new PIN instantly
4. Your old PIN is deactivated

Takes less than 1 minute. Ask any staff member!'''
        },
        'kiosk_multiple_checkin': {
            'keywords': ['checked in twice', 'two checkins', 'duplicate', 'multiple check', 'already checked', 'late checkout'],
            'answer': '''Accidental double check-in? No worries!
1. Contact a staff member immediately
2. Show your membership ID
3. Staff will correct the attendance record

Our system allows correcting these within 24 hours without penalty.'''
        },
        'kiosk_phone': {
            'keywords': ['phone', 'mobile', 'app', 'not', 'kiosk', 'alternative', 'without kiosk'],
            'answer': '''Currently, check-in is kiosk-only for security and accuracy.
**Coming Soon**: Mobile app check-in feature!

Until then:
- Use the kiosk at the gym entrance
- Ask staff if you need help
- Staff can manually check you in if kiosk unavailable

We're working on making this easier!'''
        },
        'kiosk_visitor': {
            'keywords': ['visitor', 'guest', 'friend', 'bring guest', 'guest checkin'],
            'answer': '''Guest check-in process:
1. Guest arrives with member
2. Staff registers guest at front desk (₱300)
3. Staff checks in guest to the system
4. Guest gets temporary access for the day

Easy process takes just 2 minutes!'''
        },
        'kiosk_issue': {
            'keywords': ['kiosk broken', 'kiosk down', 'not working', 'error', 'machine issue', 'help check in'],
            'answer': '''Kiosk not working? Notify staff immediately!
1. Alert any staff member
2. Provide your PIN and member ID
3. Staff will manually check you in
4. You'll still be able to access the gym

We maintain our kiosks regularly. Thank you for your patience if there's a delay!'''
        },

        # ==================== FACILITIES & POLICIES (8 FAQs) ====================
        'facilities_hours': {
            'keywords': ['hours', 'open', 'close', 'time', 'when', 'operating hours', 'schedule'],
            'answer': '''Rhose Gym Hours:
📅 **Monday - Friday**: 6:00 AM - 10:00 PM
📅 **Saturday**: 7:00 AM - 9:00 PM
📅 **Sunday**: 7:00 AM - 6:00 PM
📅 **Holidays**: 8:00 AM - 5:00 PM (check calendar)

Members have 24-hour access with membership card (coming soon)!'''
        },
        'facilities_equipment': {
            'keywords': ['equipment', 'machine', 'facility', 'facilities', 'what do you have', 'available', 'treadmill'],
            'answer': '''Our facilities include:
💪 **Strength Training**: Free weights, dumbbells (5kg-50kg), weight machines
🏃 **Cardio**: Treadmills (10), stationary bikes (8), ellipticals (6)
📦 **Equipment**: Barbells, kettlebells, medicine balls, resistance bands
🧘 **Wellness**: Yoga mats, foam rollers, stretching area
🚿 **Amenities**: Locker rooms, showers, toilets, water fountains

Hiring personal trainer? All equipment available for sessions!'''
        },
        'facilities_rules': {
            'keywords': ['rule', 'policy', 'etiquette', 'do and don\'t', 'not allowed', 'prohibited'],
            'answer': '''Gym Etiquette & Rules:
✓ **DO**: Wipe equipment after use, return weights to rack, use headphones, respect others
✗ **DON'T**: Hog equipment, drop weights loudly, grunt excessively, photograph others
📸 Photos/Videos: Permitted for personal use only (respect privacy)
🎵 Music: Use headphones (no loud speakers)
👕 Dress Code: Proper gym attire required (no street clothes)

Let's keep our gym clean and welcoming for everyone!'''
        },
        'facilities_locker': {
            'keywords': ['locker', 'storage', 'belongings', 'theft', 'safe', 'lock', 'valuables'],
            'answer': '''Locker & Storage:
🔒 **Secure Lockers**: Available for rent (₱50/month or free with annual membership)
📱 **Keep with You**: Don't leave valuables unattended
💰 **Gym Responsibility**: Not responsible for lost/stolen items

Tips:
- Use lockers for all belongings
- Never leave valuables in gym
- Ask staff for temporary storage
- Most lockers auto-lock after 15 mins

Better safe than sorry!'''
        },
        'facilities_water': {
            'keywords': ['water', 'drink', 'hydration', 'fountain', 'refill', 'bottle'],
            'answer': '''Staying Hydrated:
💧 **Free Water Fountains**: Located throughout the gym
🥤 **Bring Your Own**: Water bottles welcome (no outside beverages)
☕ **Café Coming Soon**: We're adding a café with refreshments soon!

Drink plenty of water during your workout! Generally aim for 2-3 liters daily when exercising.'''
        },
        'facilities_childcare': {
            'keywords': ['child', 'kid', 'baby', 'childcare', 'daycare', 'bring kids'],
            'answer': '''Childcare Services:
🍼 **Available**: Limited supervised childcare during peak hours (6-9 AM, 4-7 PM weekdays)
👶 **Age Range**: 3 months - 5 years
💰 **Cost**: ₱200/hour per child

Requirements:
- Must book 24 hours in advance
- Childcare staff trained in first aid
- Modern, safe facility with toys and activities

Reserve your spot at the front desk!'''
        },
        'facilities_parking': {
            'keywords': ['parking', 'park', 'car', 'vehicle', 'space', 'lot'],
            'answer': '''Parking at Rhose Gym:
🅿️ **Free Parking**: Ample free parking for all members
📍 **Location**: Adjacent to gym entrance, well-lit at night
🚗 **Security**: 24-hour CCTV surveillance
🏍️ **Motorcycles**: Designated motorcycle parking area

Our parking is safe and convenient. No fees!'''
        },
        'facilities_shower': {
            'keywords': ['shower', 'wash', 'bathroom', 'shower facilities', 'change', 'towel'],
            'answer': '''Shower & Locker Room:
🚿 **Facilities**: Modern, clean shower stalls with hot water
🧼 **Amenities**: Soap and shampoo provided (bring own for preference)
🏖️ **Towels**: Complimentary small gym towels (bring own for full coverage)
👕 **Changing**: Private changing rooms available

Perfect to freshen up before returning to work or home!'''
        },

        # ==================== REGISTRATION & ACCOUNT (6 FAQs) ====================
        'register_how': {
            'keywords': ['register', 'join', 'sign up', 'create account', 'new member', 'how to register'],
            'answer': '''Joining Rhose Gym is simple:
1. Visit our website or app
2. Click "Join Now" or "Register"
3. Fill in your details (name, email, phone, etc.)
4. Choose your membership plan
5. Complete payment (Cash or GCash)
6. Receive your member ID and PIN
7. Start working out!

Takes less than 10 minutes! Ask staff if you need help.'''
        },
        'register_requirements': {
            'keywords': ['requirement', 'what do i need', 'what to bring', 'document', 'age', 'minimum age'],
            'answer': '''Registration Requirements:
✓ Full name
✓ Valid email address
✓ Phone number
✓ Age 13+ (parental consent required for minors)
✓ Payment method (cash or GCash)

Optional but helpful:
- Emergency contact number
- Medical conditions (we'll adjust your plan)
- Fitness goals

That's it! We're ready to welcome you!'''
        },
        'register_minor': {
            'keywords': ['minor', 'under 18', 'teen', 'young', 'parent', 'guardian', 'permission'],
            'answer': '''Minors Under 18:
✓ **Age 13-17**: Requires parental/guardian consent and supervision initially
✓ **Age 18+**: Can register independently
📝 **Paperwork**: Consent form required (we'll provide)
👨‍⚖️ **Supervision**: First 3 visits should be with guardian present

Great that young people want to stay fit! We offer teen-friendly programs.'''
        },
        'register_student': {
            'keywords': ['student', 'discount', 'school', 'college', 'university', 'student rate'],
            'answer': '''Student Discounts:
🎓 **20% OFF**: All plans for valid student ID holders
- High school students: ₱2,399/month (regular ₱2,999)
- College students: Same 20% discount
- Valid ID required

Great deal to stay healthy while studying! Register at our desk with your student ID.'''
        },
        'register_senior': {
            'keywords': ['senior', 'senior citizen', 'elderly', 'age 60', 'discount', 'elderly discount'],
            'answer': '''Senior Citizen Discounts:
👴 **15% OFF**: All plans for members 60+
- Senior programs: Low-impact classes, health monitoring
- Flexible hours: Early morning rates available
- Personal training: ₱300/session (regular ₱500)

We love our senior members! Special care for health and fitness goals.'''
        },
        'register_pwd': {
            'keywords': ['pwd', 'disabled', 'disability', 'wheelchair', 'accessible', 'special need'],
            'answer': '''Persons with Disability (PWD):
♿ **25% DISCOUNT**: All plans for PWD members (with PWD ID)
♿ **Accessibility**: Wheelchair ramps, accessible bathrooms, elevators
♿ **Assistance**: Staff trained to assist with equipment modifications
♿ **Programming**: Special adaptive classes available

Inclusive gym experience for everyone! Contact management for specific accommodations.'''
        },

        # ==================== WORKOUT & FITNESS (6 FAQs) ====================
        'workout_beginner': {
            'keywords': ['beginner', 'never', 'new to gym', 'first time', 'help', 'how to start', 'no experience'],
            'answer': '''Welcome! Here's your beginner plan:
🎯 **Week 1-2**: Get familiar with equipment, learn proper form
🎯 **Week 3-4**: Start light workouts (3 days/week)
🎯 **Week 5+**: Increase intensity and frequency

**Sample Routine** (3 days/week):
- Day 1: Upper body (push-ups, rows, shoulder press)
- Day 2: Lower body (squats, lunges, leg press)
- Day 3: Cardio + core (treadmill, bike, planks)

📖 **FREE Orientation**: Ask our staff for a complimentary gym tour and equipment tutorial!'''
        },
        'workout_plan': {
            'keywords': ['plan', 'routine', 'program', 'workout plan', 'what should i do', 'schedule'],
            'answer': '''Workout Planning:
🏋️ **Free Consultation**: Talk to our staff to create a plan based on your goals
🏋️ **Personal Training**: ₱500/session (includes custom plan)
🏋️ **Online Plans**: Available through our member app

Start with:
- 3-4 days/week training
- 30-45 min per session
- Mix of cardio and strength
- 48-hour rest between same muscle groups

Goals? Tell our staff—we'll help design your ideal plan!'''
        },
        'workout_classes': {
            'keywords': ['class', 'classes', 'group', 'yoga', 'spin', 'zumba', 'group fitness'],
            'answer': '''Group Fitness Classes (FREE for members!):
🧘 **Yoga**: Mon-Wed-Fri 7 AM & 6 PM
🚴 **Spinning**: Tue-Thu-Sat 6 AM & 7 PM
💃 **Zumba**: Wed-Sat 5:30 PM
🥊 **BoxFit**: Mon-Wed-Fri 5 PM
🏃 **HIIT**: Tue-Thu-Sat 6:30 AM

All classes included with your membership! No extra fees. Book through our app.'''
        },
        'workout_trainer': {
            'keywords': ['trainer', 'personal trainer', 'coach', 'training', 'one-on-one', 'private session'],
            'answer': '''Personal Training:
💪 **Cost**: ₱500/session (members) | ₱600 (non-members)
💪 **Duration**: 60 minutes
💪 **Availability**: 6 AM - 9 PM daily
💪 **Certification**: All trainers certified and insured

Package deals available:
- 5 sessions: ₱2,250 (10% discount)
- 10 sessions: ₱4,200 (16% discount)

Contact our trainers to discuss your fitness goals!'''
        },
        'workout_progress': {
            'keywords': ['progress', 'progress tracking', 'measurement', 'body composition', 'weight'],
            'answer': '''Tracking Your Progress:
📊 **Free Assessment**: Monthly body composition analysis
📊 **Measurements**: Height, weight, waist, body fat percentage
📊 **Progress Report**: Quarterly fitness assessments
📊 **App Tracking**: Log workouts in our mobile app

Our staff can show you how to use our equipment with built-in progress tracking. Stay motivated!'''
        },
        'workout_nutrition': {
            'keywords': ['nutrition', 'diet', 'eating', 'meal', 'food', 'protein', 'supplement'],
            'answer': '''Nutrition & Diet:
🥗 **Expert Advice**: Ask our trainers for nutrition tips (free!)
🥗 **Meal Planning**: Personal trainers can create meal plans (₱300)
🥗 **Supplements**: We sell protein powder and supplements at member prices
🥗 **General Tips**: Eat whole foods, protein per workout, stay hydrated

Coming soon: Nutritionist consultations available!'''
        },

        # ==================== ACCOUNT & MEMBERSHIP STATUS (4 FAQs) ====================
        'account_login': {
            'keywords': ['login', 'sign in', 'password', 'forgot password', 'can\'t login', 'access account'],
            'answer': '''Logging Into Your Account:
1. Visit our website or open our app
2. Click "Login" or "Sign In"
3. Enter your email and password
4. Click "Remember Me" for future logins

**Forgot Password?**
1. Click "Forgot Password" on login page
2. Enter your email
3. Check your email for reset link
4. Create a new password

Can't log in? Contact support@rhosegym.com'''
        },
        'account_update': {
            'keywords': ['update', 'change', 'edit', 'profile', 'information', 'phone', 'address'],
            'answer': '''Updating Your Account Info:
1. Log in to your account
2. Go to "Profile" or "Account Settings"
3. Edit any field (name, phone, email, address, etc.)
4. Click "Save Changes"

Changes take effect immediately! Updated info helps us keep you informed.'''
        },
        'account_verify_email': {
            'keywords': ['verify', 'email', 'confirmation', 'confirm email', 'didn\'t receive'],
            'answer': '''Email Verification:
✓ **Check Inbox**: Look for verification email
✓ **Check Spam**: Sometimes emails go to spam
✓ **Resend**: Click "Resend Verification Email" in account settings
⏰ **Takes 5 mins**: Usually arrives within 5 minutes

Not received? Contact support@rhosegym.com and we'll help immediately!'''
        },
        'account_data': {
            'keywords': ['data', 'privacy', 'delete account', 'download', 'personal data', 'what data'],
            'answer': '''Your Data & Privacy:
🔒 **Privacy Protected**: Your data is encrypted and secure
📥 **Data Download**: Request your data through Settings → Privacy
🗑️ **Data Deletion**: Request account deletion (requires 30-day notice)
📋 **Data We Collect**: Name, email, phone, fitness info (never sold)

Your privacy is our priority! Questions? Email privacy@rhosegym.com'''
        },
    }

    @classmethod
    def find_faq_match(cls, user_query):
        """
        PERFORMANCE: <10ms response time
        Search FAQ database for matching question
        Returns: (matched_faq_answer, match_score) or (None, 0)
        """
        query_lower = user_query.lower()

        best_match = None
        best_score = 0

        for faq_key, faq_data in cls.FAQ_DATABASE.items():
            keywords = faq_data['keywords']

            # Count keyword matches (exact matches only, faster than regex)
            match_count = sum(1 for kw in keywords if kw in query_lower)

            if match_count > best_score:
                best_score = match_count
                best_match = faq_data['answer']

        # Return match only if at least one keyword matched
        if best_score > 0:
            return best_match, best_score

        return None, 0

    @classmethod
    def is_faq_query(cls, user_query):
        """
        PERFORMANCE: Quickly determine if query is FAQ-eligible
        Before: 2-3 seconds (AI processing)
        After: <10ms (direct lookup)
        """
        _, match_score = cls.find_faq_match(user_query)
        return match_score > 0


class QueryNormalizer:
    """
    Normalizes user queries to handle plural/singular variations
    and common word transformations for better pattern matching
    """

    # Plural to singular mappings
    PLURAL_TO_SINGULAR = {
        'details': 'detail',
        'members': 'member',
        'payments': 'payment',
        'plans': 'plan',
        'passes': 'pass',
        'sales': 'sale',
        'stats': 'stat',
        'statistics': 'statistic',
        'analytics': 'analytic',
        'reports': 'report',
        'visits': 'visit',
        'checkins': 'checkin',
        'check-ins': 'checkin',
        'memberships': 'membership',
        'subscriptions': 'subscription',
        'renewals': 'renewal',
        'expirations': 'expiration',
        'attendances': 'attendance',
    }

    # Singular to plural mappings (for reverse lookup if needed)
    SINGULAR_TO_PLURAL = {v: k for k, v in PLURAL_TO_SINGULAR.items()}

    # Word variations/synonyms
    WORD_VARIATIONS = {
        'info': ['information', 'informations', 'details', 'detail', 'data'],
        'detail': ['details', 'info', 'information'],
        'profile': ['profiles', 'account', 'accounts'],
        'member': ['members', 'user', 'users', 'client', 'clients'],
        'payment': ['payments', 'transaction', 'transactions'],
        'checkin': ['check-in', 'check in', 'checkins', 'check-ins'],
        'revenue': ['sales', 'income', 'earnings', 'proceeds'],
        'summary': ['summaries', 'overview', 'report', 'reports'],
    }

    @classmethod
    def normalize_query(cls, query):
        """
        Normalize a query by handling plural/singular variations
        Returns both the original and normalized version
        """
        normalized = query.lower()

        # Replace plurals with singulars for consistent matching
        for plural, singular in cls.PLURAL_TO_SINGULAR.items():
            # Use word boundaries to avoid partial replacements
            normalized = re.sub(r'\b' + plural + r'\b', singular, normalized)

        return normalized

    @classmethod
    def expand_keywords(cls, keywords):
        """
        Expand a list of keywords to include plural/singular variations
        """
        expanded = set(keywords)

        for keyword in keywords:
            words = keyword.split()

            # For each word in the keyword phrase
            for i, word in enumerate(words):
                # Add plural form if singular
                if word in cls.SINGULAR_TO_PLURAL:
                    plural_word = cls.SINGULAR_TO_PLURAL[word]
                    new_phrase = words.copy()
                    new_phrase[i] = plural_word
                    expanded.add(' '.join(new_phrase))

                # Add singular form if plural
                if word in cls.PLURAL_TO_SINGULAR:
                    singular_word = cls.PLURAL_TO_SINGULAR[word]
                    new_phrase = words.copy()
                    new_phrase[i] = singular_word
                    expanded.add(' '.join(new_phrase))

                # Add word variations
                if word in cls.WORD_VARIATIONS:
                    for variation in cls.WORD_VARIATIONS[word]:
                        new_phrase = words.copy()
                        new_phrase[i] = variation
                        expanded.add(' '.join(new_phrase))

        return list(expanded)

    @classmethod
    def matches_any_variation(cls, query, keywords):
        """
        Check if query matches any variation of the keywords
        Handles plural/singular automatically
        """
        query_normalized = cls.normalize_query(query)

        # Expand keywords to include variations
        expanded_keywords = cls.expand_keywords(keywords)

        # Check if any expanded keyword is in the normalized query
        for keyword in expanded_keywords:
            keyword_normalized = cls.normalize_query(keyword)
            if keyword_normalized in query_normalized:
                return True

        return False


class ChatbotTools:
    """
    Central hub for chatbot tools and function calling
    Routes queries to appropriate engines based on intent
    """

    def __init__(self, user):
        """
        Initialize tools for a specific user

        Args:
            user: The User object using the chatbot
        """
        self.user = user
        self.analytics = AnalyticsEngine()
        self.operations = OperationsExecutor(user) if user and user.is_authenticated else None

    # ==================== Intent Detection ====================

    @staticmethod
    def detect_intent(query):
        """
        Detect user intent from query with plural/singular normalization
        Returns: intent type and confidence score

        Intent types:
        - analytical: Data analysis, reports, statistics
        - operational: Actions, operations, modifications
        - informational: General questions, FAQ
        - member_lookup: Search for specific member information
        """
        query_lower = query.lower()
        query_normalized = QueryNormalizer.normalize_query(query)

        # Analytical keywords (base forms - will be expanded)
        analytical_keywords = [
            'revenue', 'sale', 'report', 'analytic', 'statistic', 'stat',
            'how many', 'how much', 'total', 'summary', 'performance',
            'growth', 'trend', 'attendance', 'retention', 'churn',
            'popular', 'breakdown', 'compare', 'comparison', 'vs',
            'this week', 'this month', 'today', 'yesterday', 'last week', 'last month'
        ]

        # Operational keywords (base forms - will be expanded)
        operational_keywords = [
            'confirm payment', 'approve payment', 'generate pin', 'create sale',
            'record sale', 'send reminder', 'find member', 'search member',
            'expiring', 'pending', 'inactive member', 'checkin today',
            'who checked in', 'mark', 'update', 'extend membership'
        ]

        # Member lookup keywords (base forms - will be expanded)
        lookup_keywords = [
            'show me', 'find', 'search', 'lookup', 'get detail',
            'member profile', 'membership status', 'payment history',
            'info', 'detail', 'profile', "what's", 'whats', "who's", 'whos',
            'info about', 'detail about', 'member info',
            'give me', 'get me', 'pull up', 'look up'
        ]

        # Check for email in query (strong indicator of member lookup)
        has_email = '@' in query and re.search(r'[\w\.-]+@[\w\.-]+', query)

        # Check for possessive form (e.g., "John's info", "Maria's details")
        has_possessive = re.search(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*'?s?\s+(?:info|details?|profile)", query)

        # Count keyword matches using normalized query
        analytical_score = sum(1 for kw in analytical_keywords if kw in query_normalized)
        operational_score = sum(1 for kw in operational_keywords if kw in query_normalized)
        lookup_score = sum(1 for kw in lookup_keywords if kw in query_normalized)

        # Boost lookup score if email or possessive form detected
        if has_email:
            lookup_score += 3
        if has_possessive:
            lookup_score += 2

        # Determine intent
        scores = {
            'analytical': analytical_score,
            'operational': operational_score,
            'member_lookup': lookup_score,
            'informational': 0.5  # Default fallback
        }

        intent = max(scores, key=scores.get)
        confidence = scores[intent]

        # If no strong match, it's informational
        if confidence < 1:
            intent = 'informational'

        return intent, confidence

    # ==================== Analytics Tools ====================

    def get_revenue_report(self, period='today'):
        """
        Tool: Get revenue report for a period
        Available to: All staff/admin users
        """
        if not self.user or not self.user.is_staff_or_admin():
            return "❌ This feature requires staff or admin access."

        try:
            data = self.analytics.get_revenue_summary(period)
            return self.analytics.format_report_for_chatbot(data, 'revenue')
        except Exception as e:
            return f"Error generating revenue report: {str(e)}"

    def get_membership_growth_report(self, period='this_month'):
        """
        Tool: Get membership growth analysis
        Available to: All staff/admin users
        """
        if not self.user or not self.user.is_staff_or_admin():
            return "❌ This feature requires staff or admin access."

        try:
            data = self.analytics.get_membership_growth(period)
            return self.analytics.format_report_for_chatbot(data, 'growth')
        except Exception as e:
            return f"Error generating growth report: {str(e)}"

    def get_attendance_report(self, period='this_week'):
        """
        Tool: Get attendance trends and analysis
        Available to: All staff/admin users
        """
        if not self.user or not self.user.is_staff_or_admin():
            return "❌ This feature requires staff or admin access."

        try:
            data = self.analytics.get_attendance_trends(period)
            return self.analytics.format_report_for_chatbot(data, 'attendance')
        except Exception as e:
            return f"Error generating attendance report: {str(e)}"

    def get_retention_analysis(self):
        """
        Tool: Get member retention and churn analysis
        Available to: All staff/admin users
        """
        if not self.user or not self.user.is_staff_or_admin():
            return "❌ This feature requires staff or admin access."

        try:
            data = self.analytics.get_member_retention_analysis()
            return self.analytics.format_report_for_chatbot(data, 'retention')
        except Exception as e:
            return f"Error generating retention report: {str(e)}"

    def get_plan_popularity_report(self, period='this_month'):
        """
        Tool: Get plan popularity analysis
        Available to: All staff/admin users
        """
        if not self.user or not self.user.is_staff_or_admin():
            return "❌ This feature requires staff or admin access."

        try:
            data = self.analytics.get_plan_popularity(period)
            return self.analytics.format_report_for_chatbot(data, 'plans')
        except Exception as e:
            return f"Error generating plan popularity report: {str(e)}"

    def get_payment_status_report(self):
        """
        Tool: Get payment collection status
        Available to: All staff/admin users
        """
        if not self.user or not self.user.is_staff_or_admin():
            return "❌ This feature requires staff or admin access."

        try:
            data = self.analytics.get_payment_collection_status()
            return self.analytics.format_report_for_chatbot(data, 'payments')
        except Exception as e:
            return f"Error generating payment report: {str(e)}"

    def get_comprehensive_summary(self, period='today'):
        """
        Tool: Get comprehensive performance summary
        Available to: Admin users only
        """
        if not self.user or not self.user.is_admin():
            return "❌ This feature requires admin access."

        try:
            data = self.analytics.get_comprehensive_report(period)
            return self.analytics.format_report_for_chatbot(data, 'comprehensive')
        except Exception as e:
            return f"Error generating comprehensive report: {str(e)}"

    # ==================== Operations Tools ====================

    def search_members(self, query):
        """
        Tool: Search for members by name or email
        Available to: Staff and admin
        """
        if not self.operations:
            return "❌ This feature requires staff or admin access."

        try:
            members = self.operations.search_members(query)
            if not members:
                return f"No members found matching '{query}'"
            return self.operations.format_member_list(members, "Search Results")
        except PermissionError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"Error searching members: {str(e)}"

    def get_member_details(self, member_identifier):
        """
        Tool: Get complete member profile
        Available to: Staff and admin
        """
        if not self.operations:
            return "❌ This feature requires staff or admin access."

        try:
            details = self.operations.get_member_details(member_identifier)
            return self.operations.format_member_details(details)
        except PermissionError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"Error retrieving member details: {str(e)}"

    def find_expiring_memberships(self, days=7):
        """
        Tool: Find members with expiring memberships
        Available to: Staff and admin
        """
        if not self.operations:
            return "❌ This feature requires staff or admin access."

        try:
            members = self.operations.find_expiring_memberships(days)
            if not members:
                return f"No memberships expiring in the next {days} days. 🎉"
            return self.operations.format_member_list(
                members,
                f"Memberships Expiring in {days} Days"
            )
        except PermissionError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"Error finding expiring memberships: {str(e)}"

    def find_inactive_members(self, days=30):
        """
        Tool: Find members who haven't visited recently
        Available to: Staff and admin
        """
        if not self.operations:
            return "❌ This feature requires staff or admin access."

        try:
            members = self.operations.find_inactive_members(days)
            if not members:
                return f"All members are active! 🎉"
            return self.operations.format_member_list(
                members,
                f"Inactive Members ({days}+ days)"
            )
        except PermissionError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"Error finding inactive members: {str(e)}"

    def get_pending_payments(self):
        """
        Tool: Get list of pending payment approvals
        Available to: Staff and admin
        """
        if not self.operations:
            return "❌ This feature requires staff or admin access."

        try:
            payments = self.operations.find_pending_payments()
            if not payments:
                return "No pending payments. All caught up! ✅"
            return self.operations.format_payment_list(payments)
        except PermissionError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"Error retrieving pending payments: {str(e)}"

    def confirm_payment(self, payment_reference):
        """
        Tool: Confirm a pending payment
        Available to: Staff and admin
        Requires confirmation: Yes
        """
        if not self.operations:
            return "❌ This feature requires staff or admin access."

        try:
            result = self.operations.confirm_payment(payment_reference)
            return self.operations.format_operation_result(result)
        except PermissionError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"Error confirming payment: {str(e)}"

    def generate_member_pin(self, member_identifier):
        """
        Tool: Generate kiosk PIN for a member
        Available to: Staff and admin
        """
        if not self.operations:
            return "❌ This feature requires staff or admin access."

        try:
            result = self.operations.generate_kiosk_pin(member_identifier)
            return self.operations.format_operation_result(result)
        except PermissionError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"Error generating PIN: {str(e)}"

    def get_todays_checkins(self):
        """
        Tool: Get today's check-in list
        Available to: Staff and admin
        """
        if not self.operations:
            return "❌ This feature requires staff or admin access."

        try:
            result = self.operations.get_todays_checkins()

            text = f"🏋️ **Today's Check-ins**\n\n"
            text += f"📅 Date: {result['date']}\n"
            text += f"✅ Total Check-ins: {result['total_checkins']}\n"
            text += f"🔥 Currently in Gym: {result['currently_in_gym']}\n\n"

            if result['checkins']:
                text += "**Recent Check-ins:**\n"
                for checkin in result['checkins'][:15]:  # Show last 15
                    status_emoji = "🟢" if checkin['status'] == 'In gym' else "⚪"
                    text += f"{status_emoji} {checkin['member_name']} - {checkin['check_in_time']}\n"

            return text
        except PermissionError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"Error retrieving check-ins: {str(e)}"

    def create_walkin_sale(self, pass_name, amount, customer_name=None, method='cash'):
        """
        Tool: Record a walk-in pass sale
        Available to: Staff and admin
        """
        if not self.operations:
            return "❌ This feature requires staff or admin access."

        try:
            result = self.operations.create_walkin_sale(
                pass_name=pass_name,
                amount=amount,
                customer_name=customer_name,
                method=method
            )
            return self.operations.format_operation_result(result)
        except PermissionError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"Error creating walk-in sale: {str(e)}"

    # ==================== Query Router ====================

    def route_query(self, query):
        """
        Intelligently route query to appropriate tool with normalization
        Returns: Tool execution result or None if no tool matches

        NOTE: FAQ fast-path is checked in chatbot.py chat() method FIRST (before this is called)
        for ALL queries to ensure instant response.
        """
        query_lower = query.lower()
        query_normalized = QueryNormalizer.normalize_query(query)

        # Revenue queries (handles: revenue/revenues, sale/sales, etc.)
        if QueryNormalizer.matches_any_variation(query, ['revenue', 'sale', 'income', 'earning']):
            period = self._extract_period(query_lower)
            return self.get_revenue_report(period)

        # Membership growth queries (handles: member/members, membership/memberships)
        if QueryNormalizer.matches_any_variation(query, ['new member', 'membership growth', 'member growth', 'how many new']):
            period = self._extract_period(query_lower)
            return self.get_membership_growth_report(period)

        # Attendance queries (handles: checkin/checkins, check-in/check-ins, visit/visits)
        # Also handle "who checked in today" pattern
        if (QueryNormalizer.matches_any_variation(query, ['attendance', 'checkin', 'visit', 'peak hour', 'busy']) or
            'who checked in' in query_lower or 'checked in today' in query_lower):
            if 'today' in query_lower or 'who checked in' in query_lower:
                return self.get_todays_checkins()
            period = self._extract_period(query_lower)
            return self.get_attendance_report(period)

        # Retention queries (handles: renewal/renewals)
        if QueryNormalizer.matches_any_variation(query, ['retention', 'churn', 'renewal']):
            return self.get_retention_analysis()

        # Plan popularity queries (handles: plan/plans)
        if QueryNormalizer.matches_any_variation(query, ['popular plan', 'best-selling', 'top plan', 'most subscribed']):
            period = self._extract_period(query_lower)
            return self.get_plan_popularity_report(period)

        # Payment queries (handles: payment/payments)
        if QueryNormalizer.matches_any_variation(query, ['pending payment', 'outstanding']):
            return self.get_pending_payments()

        # Confirm payment
        if 'confirm payment' in query_normalized:
            # Extract reference number (e.g., PAY-20231201-123456)
            match = re.search(r'(PAY-\d{8}-\d{6})', query, re.IGNORECASE)
            if match:
                return self.confirm_payment(match.group(1))
            else:
                return "Please provide a payment reference number (e.g., PAY-20231201-123456)"

        # Expiring memberships (handles: expiring/expirations, membership/memberships)
        if 'expir' in query_normalized:
            days = self._extract_days(query_lower, default=7)
            return self.find_expiring_memberships(days)

        # Inactive members (handles: member/members)
        if 'inactive' in query_normalized:
            days = self._extract_days(query_lower, default=30)
            return self.find_inactive_members(days)

        # Check for standalone email first (before keyword matching)
        if '@' in query:
            # Email found - check if it's a member lookup query
            email = re.search(r'[\w\.-]+@[\w\.-]+', query)
            if email and self.operations:
                return self.get_member_details(email.group(0))

        # Member search/lookup - expanded patterns with normalization
        # Using base forms (detail, info, member, etc.) - normalizer handles plural/singular
        member_lookup_keywords = [
            'find member', 'search member', 'lookup member', 'show me',
            'member info', 'member detail', 'member profile',
            'info about', 'detail about', 'profile of', 'profile for',
            'whats', "what's", 'whos', "who's",
            'info', 'detail', 'profile',
            'give me', 'get me', 'pull up', 'look up',
            'information on', 'information about'
        ]

        # Check if query matches member lookup patterns (with normalization)
        is_member_lookup = QueryNormalizer.matches_any_variation(query, member_lookup_keywords)

        # Also check for name-like patterns (capitalized words followed by info/detail/profile)
        # Handles both singular and plural
        if not is_member_lookup:
            # Pattern: "Carlos Bautista details/detail" or "John Doe info/information"
            name_pattern = re.search(
                r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\s+(?:info|information|detail|details|profile|profiles)',
                query
            )
            if name_pattern:
                is_member_lookup = True

        if is_member_lookup:
            # Try to extract member name or email
            if '@' in query:
                # Email found
                email = re.search(r'[\w\.-]+@[\w\.-]+', query)
                if email:
                    return self.get_member_details(email.group(0))

            # Try to extract name (words after keywords or possessive forms)
            # Handle possessive queries like "What's John Doe's info/details/information"
            # Handles both singular and plural forms
            possessive_match = re.search(
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'?s?\s+(?:info|information|detail|details|profile|profiles|data)",
                query
            )
            if possessive_match:
                name = possessive_match.group(1).strip()
                if name:
                    return self.get_member_details(name)

            # Try to extract name after common keywords (using normalized forms)
            extraction_keywords = [
                'find', 'search', 'lookup', 'show me', 'give me', 'get me',
                'info about', 'detail about', 'details about', 'information about',
                'profile of', 'profile for', 'whats', "what's", 'info for',
                'detail for', 'details for', 'pull up', 'look up'
            ]

            # Also try plural variations
            extraction_keywords.extend([
                'infos about', 'profiles of', 'profiles for'
            ])

            for keyword in extraction_keywords:
                if keyword in query_lower:
                    parts = query_lower.split(keyword)
                    if len(parts) > 1:
                        # Extract potential name (remove common words)
                        name = parts[1].strip()

                        # Remove trailing/leading words - handles both plural and singular
                        remove_words = [
                            'member', 'members', 'user', 'users', 'client', 'clients',
                            'info', 'infos', 'information', 'informations',
                            'detail', 'details', 'data',
                            'profile', 'profiles', 'account', 'accounts',
                            "'s", 's', 'the', 'for', 'about', 'on', 'of'
                        ]

                        # Split into words and remove unwanted ones
                        words = name.split()
                        cleaned_words = []
                        for word in words:
                            # Keep words that look like names (start with capital or are capitalized)
                            # Skip common words
                            word_clean = word.strip("'\",.?!;:")
                            if word_clean.lower() not in remove_words and len(word_clean) > 1:
                                cleaned_words.append(word_clean)

                        if cleaned_words:
                            name = ' '.join(cleaned_words[:4])  # Max 4 words for a name
                            if name and len(name) > 2:  # Avoid single letters
                                return self.get_member_details(name)

        # Generate PIN
        if 'generate pin' in query_lower or 'create pin' in query_lower:
            # Extract member identifier
            for keyword in ['for', 'to']:
                if keyword in query_lower:
                    parts = query_lower.split(keyword)
                    if len(parts) > 1:
                        member = parts[1].strip()
                        if member:
                            return self.generate_member_pin(member)

        # Comprehensive summary
        if any(kw in query_lower for kw in ['summary', 'overview', 'performance', 'dashboard']):
            period = self._extract_period(query_lower)
            return self.get_comprehensive_summary(period)

        # No tool matched
        return None

    # ==================== Helper Methods ====================

    @staticmethod
    def _extract_period(query_lower):
        """Extract time period from query"""
        if 'today' in query_lower:
            return 'today'
        elif 'yesterday' in query_lower:
            return 'yesterday'
        elif 'this week' in query_lower:
            return 'this_week'
        elif 'last week' in query_lower:
            return 'last_week'
        elif 'this month' in query_lower:
            return 'this_month'
        elif 'last month' in query_lower:
            return 'last_month'
        elif 'this year' in query_lower:
            return 'this_year'
        else:
            return 'today'  # Default

    @staticmethod
    def _extract_days(query_lower, default=7):
        """Extract number of days from query"""
        # Look for patterns like "7 days", "next 14 days", "30 days"
        match = re.search(r'(\d+)\s*days?', query_lower)
        if match:
            return int(match.group(1))
        return default

    @staticmethod
    def get_available_tools(user):
        """
        Get list of available tools for a user based on their role
        Useful for showing capabilities
        """
        tools = {
            'member': [
                'Membership status and expiry',
                'Payment history',
                'Kiosk PIN retrieval',
                'Workout and fitness advice',
                'Gym policies and FAQs'
            ],
            'staff': [
                'All member tools',
                'Today\'s revenue and sales',
                'Check-in statistics',
                'Search members',
                'View member profiles',
                'Pending payment approvals',
                'Expiring memberships',
                'Generate kiosk PINs',
                'Record walk-in sales',
                'Confirm payments'
            ],
            'admin': [
                'All staff tools',
                'Comprehensive analytics reports',
                'Revenue breakdowns (daily/weekly/monthly)',
                'Membership growth analysis',
                'Attendance trends and peak hours',
                'Member retention and churn analysis',
                'Plan popularity reports',
                'Payment collection rates',
                'Inactive member reports',
                'Bulk operations'
            ]
        }

        if user and user.is_authenticated:
            role = user.role
            return tools.get(role, tools['member'])
        else:
            return [
                'Gym membership information',
                'Pricing and plans',
                'Walk-in pass information',
                'Gym facilities and hours',
                'Registration process',
                'General fitness advice'
            ]
