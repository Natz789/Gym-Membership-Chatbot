"""
Enhanced AI Chatbot Engine for Rhose Gym
Advanced capabilities: Analytics, Operations, Member Management
Configured with HuggingFace Inference API for cloud-based LLM access
Performance optimized with caching for faster response times

Version 4.0 - HuggingFace Integration:
- Uses HuggingFace Inference API (Mistral-7B or other models)
- No local Ollama dependency required
- Works seamlessly on Render and other cloud platforms
- Intent detection and intelligent routing
- Advanced analytics and reporting
- Member lookup and management
- Staff/admin operations
- Permission-based access control
- Audit logging for all operations
"""

import uuid
import time
from huggingface_hub import InferenceClient
from django.conf import settings
from django.core.cache import cache
from decouple import config
from .models import (
    User, MembershipPlan, FlexibleAccess, UserMembership, Payment, Attendance,
    Conversation, ConversationMessage, AuditLog
)
from .chatbot_tools import ChatbotTools
from .chatbot_analytics import AnalyticsEngine
from datetime import date, timedelta
import json


class GymChatbot:
    """AI-powered chatbot for gym assistance - Using HuggingFace Inference API"""

    # HuggingFace Inference API Configuration
    # Default to Mistral-7B (free tier available)
    MODEL = config('HF_MODEL', default='mistralai/Mistral-7B-Instruct-v0.2')
    TEMPERATURE = 0.7
    MAX_TOKENS = 256  # Reduced for faster responses and cost efficiency
    CONTEXT_WINDOW = 6
    ENABLE_STREAMING = False
    ENABLE_PERSISTENCE = True
    TIMEOUT_SECONDS = 30

    # HuggingFace API Configuration
    HF_API_KEY = config('HF_API_KEY', default=None)
    HF_API_URL = config('HF_API_URL', default='https://api-inference.huggingface.co')

    def __init__(self, user=None, conversation_id=None, session_key=None):
        self.user = user
        self.session_key = session_key
        self.model = self.MODEL
        self.conversation = None
        self.conversation_history = []

        # Initialize HuggingFace Inference Client
        if self.HF_API_KEY:
            self.hf_client = InferenceClient(
                api_key=self.HF_API_KEY,
                model=self.MODEL
            )
        else:
            self.hf_client = None

        # Initialize tools for advanced features
        self.tools = ChatbotTools(user)

        # Load or create conversation
        if conversation_id:
            self._load_conversation(conversation_id)
        elif self.ENABLE_PERSISTENCE:
            self._create_conversation()

    def _load_conversation(self, conversation_id):
        """Load existing conversation from database"""
        try:
            if self.user and self.user.is_authenticated:
                self.conversation = Conversation.objects.get(
                    conversation_id=conversation_id,
                    user=self.user
                )
            else:
                self.conversation = Conversation.objects.get(
                    conversation_id=conversation_id,
                    session_key=self.session_key
                )

            # Load message history
            messages = self.conversation.messages.all()
            for msg in messages:
                if msg.role != 'system':  # Skip system messages
                    self.conversation_history.append({
                        'role': msg.role,
                        'content': msg.content
                    })
        except Conversation.DoesNotExist:
            self._create_conversation()

    def _create_conversation(self):
        """Create a new conversation"""
        conversation_id = str(uuid.uuid4())
        self.conversation = Conversation.objects.create(
            user=self.user if self.user and self.user.is_authenticated else None,
            conversation_id=conversation_id,
            model_used=self.model,
            session_key=self.session_key if not (self.user and self.user.is_authenticated) else None
        )

    def _save_message(self, role, content, response_time_ms=None):
        """Save message to database if persistence is enabled"""
        if self.ENABLE_PERSISTENCE and self.conversation:
            ConversationMessage.objects.create(
                conversation=self.conversation,
                role=role,
                content=content,
                response_time_ms=response_time_ms
            )

            # Generate title from first user message
            if role == 'user' and not self.conversation.title:
                self.conversation.generate_title()

    @classmethod
    def get_hf_options(cls):
        """Get formatted options for HuggingFace Inference API"""
        return {
            'temperature': cls.TEMPERATURE,
            'max_new_tokens': cls.MAX_TOKENS,
        }

    @staticmethod
    def _get_static_base_context():
        """
        Get cached static base context that rarely changes.
        Cached for 1 hour to improve performance.
        """
        cache_key = 'chatbot_static_base_context'
        cached_context = cache.get(cache_key)

        if cached_context:
            return cached_context

        # Base gym information (static)
        context = """You are FitBot, an AI customer service assistant for Rhose Gym, a modern fitness center.
Your primary role is to provide excellent customer service and answer frequently asked questions about:

1. MEMBERSHIPS & PRICING
   - Explain membership plans, pricing, and benefits
   - Help members understand their subscription status and expiration dates
   - Guide users through the membership purchase process
   - Explain walk-in passes and day passes

2. PAYMENTS & TRANSACTIONS
   - Answer questions about payment methods (Cash, GCash)
   - Explain payment status and history
   - Help with pending payments and payment confirmation
   - Provide information about payment references and receipts

3. CUSTOMER SERVICE & SUPPORT
   - Answer common questions about gym policies
   - Assist with account-related inquiries
   - Help troubleshoot common issues
   - Guide users on how to use the kiosk system
   - Provide information about gym hours and facilities

4. GYM FACILITIES & USAGE
   - Explain available equipment and facilities
   - Provide basic workout guidance
   - Share gym etiquette and safety rules

Always be friendly, professional, helpful, and empathetic. Prioritize customer satisfaction.
Keep your responses concise, clear, and action-oriented. When discussing the gym system, use the data provided.
If you don't know something specific, politely direct the user to contact the gym staff directly.
"""

        # Add static gym information
        context += "\n\nGYM FACILITIES:\n"
        context += "- Cardio equipment (treadmills, bikes, ellipticals)\n"
        context += "- Strength training (free weights, machines)\n"
        context += "- Group fitness classes\n"
        context += "- Locker rooms and showers\n"

        context += "\n\nGYM POLICIES:\n"
        context += "- Members must check in/out using kiosk PIN\n"
        context += "- Proper gym attire required\n"
        context += "- Clean equipment after use\n"
        context += "- Memberships expire on end date\n"

        context += "\n\nCOMMON FAQS - QUICK ANSWERS:\n"
        context += "Q: How do I pay for membership?\n"
        context += "A: We accept Cash and GCash. You can subscribe to a plan from the Membership Plans page.\n\n"
        context += "Q: How do I check my payment history?\n"
        context += "A: Login to your dashboard to view your complete payment history and transaction details.\n\n"
        context += "Q: What if my payment is pending?\n"
        context += "A: Pending payments need to be confirmed by staff. Check your dashboard or contact us for status.\n\n"
        context += "Q: How do I use my kiosk PIN?\n"
        context += "A: Enter your 6-digit PIN at the kiosk to check in when you arrive and check out when you leave.\n\n"
        context += "Q: Can I renew my membership?\n"
        context += "A: Yes! You can purchase a new membership plan from the Membership Plans page before or after your current one expires.\n\n"
        context += "Q: What's the difference between membership and walk-in pass?\n"
        context += "A: Memberships provide longer-term access (30-365 days), while walk-in passes are for single-day or short-term visits.\n\n"
        context += "Q: How do I register for the gym?\n"
        context += "A: Click 'Join Now' or 'Register' on the homepage, fill out your details, choose a membership plan, and complete payment.\n\n"

        # Cache for 1 hour
        cache.set(cache_key, context, 3600)
        return context

    @staticmethod
    def _get_cached_membership_plans():
        """Get cached membership plans. Cached for 10 minutes."""
        cache_key = 'chatbot_membership_plans'
        cached_plans = cache.get(cache_key)

        if cached_plans:
            return cached_plans

        active_plans = MembershipPlan.objects.filter(is_active=True)
        plans_text = ""

        if active_plans.exists():
            plans_text = "\n\nAVAILABLE MEMBERSHIP PLANS:\n"
            for plan in active_plans:
                plans_text += f"- {plan.name}: ₱{plan.price} for {plan.duration_days} days\n"
                if plan.description:
                    plans_text += f"  Description: {plan.description}\n"

        # Cache for 10 minutes
        cache.set(cache_key, plans_text, 600)
        return plans_text

    @staticmethod
    def _get_cached_walkin_passes():
        """Get cached walk-in passes. Cached for 10 minutes."""
        cache_key = 'chatbot_walkin_passes'
        cached_passes = cache.get(cache_key)

        if cached_passes:
            return cached_passes

        walk_in_passes = FlexibleAccess.objects.filter(is_active=True)
        passes_text = ""

        if walk_in_passes.exists():
            passes_text = "\n\nWALK-IN PASSES:\n"
            for pass_obj in walk_in_passes:
                passes_text += f"- {pass_obj.name}: ₱{pass_obj.price} for {pass_obj.duration_days} day(s)\n"

        # Cache for 10 minutes
        cache.set(cache_key, passes_text, 600)
        return passes_text

    def get_system_context(self):
        """
        Generate system context based on user role and gym data.
        Optimized with caching for faster performance.
        """
        # Start with cached static base context
        context = self._get_static_base_context()

        # Add cached membership plans and walk-in passes
        context += self._get_cached_membership_plans()
        context += self._get_cached_walkin_passes()

        # Add user-specific context (not cached as it's frequently changing)
        if self.user and self.user.is_authenticated:
            context += f"\n\nCURRENT USER: {self.user.get_full_name()} ({self.user.role})\n"

            if self.user.role == 'member':
                # Get member's active membership with optimized query
                active_membership = UserMembership.objects.filter(
                    user=self.user,
                    status='active',
                    end_date__gte=date.today()
                ).select_related('plan').first()

                if active_membership:
                    context += f"Active Membership: {active_membership.plan.name}\n"
                    context += f"Days Remaining: {active_membership.days_remaining()}\n"
                    context += f"Expires: {active_membership.end_date}\n"

                    # Get kiosk PIN
                    if self.user.kiosk_pin:
                        context += f"Kiosk PIN: {self.user.kiosk_pin}\n"
                else:
                    context += "No active membership\n"

                # Get recent attendance count (optimized - only count, no full data)
                recent_count = Attendance.objects.filter(
                    user=self.user
                ).count()

                if recent_count > 0:
                    context += f"\nRECENT GYM VISITS: {recent_count} visits logged\n"

            elif self.user.role in ['admin', 'staff']:
                # Cache staff stats for 2 minutes (frequently accessed)
                cache_key = f'chatbot_staff_stats_{date.today()}'
                cached_stats = cache.get(cache_key)

                if cached_stats:
                    context += cached_stats
                else:
                    # Get today's stats for staff/admin
                    today = date.today()
                    today_checkins = Attendance.objects.filter(
                        check_in__date=today
                    ).count()
                    currently_in = Attendance.objects.filter(
                        check_out__isnull=True
                    ).count()

                    stats_text = f"\nTODAY'S STATS:\n"
                    stats_text += f"- Check-ins today: {today_checkins}\n"
                    stats_text += f"- Currently in gym: {currently_in}\n"

                    # Cache for 2 minutes
                    cache.set(cache_key, stats_text, 120)
                    context += stats_text

        return context

    @staticmethod
    def get_fitness_knowledge():
        """
        General fitness and gym culture knowledge.
        Cached for 1 hour as it's completely static.
        """
        cache_key = 'chatbot_fitness_knowledge'
        cached_knowledge = cache.get(cache_key)

        if cached_knowledge:
            return cached_knowledge

        knowledge = """
WORKOUT TIPS:
- Warm up 5-10 minutes before exercise
- Progressive overload: gradually increase weight/reps
- Rest 48 hours between training same muscle groups
- Mix cardio and strength training
- Stay hydrated (drink water before, during, after)

BEGINNER ROUTINE (3 days/week):
- Day 1: Upper body (push-ups, rows, shoulder press)
- Day 2: Lower body (squats, lunges, leg press)
- Day 3: Full body circuit with cardio

NUTRITION BASICS:
- Protein: 1.6-2.2g per kg body weight for muscle building
- Eat whole foods, avoid processed foods
- Pre-workout: carbs + protein 1-2 hours before
- Post-workout: protein within 30-60 minutes
- Stay hydrated: 2-3 liters water daily

GYM ETIQUETTE:
- Wipe down equipment after use
- Re-rack weights properly
- Share equipment, don't hog machines
- Use headphones for music
- Respect personal space

COMMON MISTAKES:
- Skipping warm-up and cool-down
- Poor form (risking injury)
- Not tracking progress
- Inconsistent training
- Overtraining without rest
"""
        # Cache for 1 hour
        cache.set(cache_key, knowledge, 3600)
        return knowledge

    def chat(self, user_message):
        """
        Process user message with intent detection and intelligent routing
        Enhanced with analytics, operations, and tool calling

        PERFORMANCE OPTIMIZATION: FAQ fast-path checked FIRST for all queries
        """
        start_time = time.time()

        # OPTIMIZATION #1: Check FAQ database FIRST - instant response (<10ms)
        # This should be done BEFORE any other processing
        from .chatbot_tools import FAQFastPath
        faq_answer, faq_score = FAQFastPath.find_faq_match(user_message)
        if faq_answer:
            # FAQ matched - return immediately, no AI needed
            response_time_ms = int((time.time() - start_time) * 1000)

            # Save to conversation history
            self._save_message("user", user_message)
            self._save_message("assistant", faq_answer, response_time_ms)

            # Log usage
            self._log_chatbot_usage(user_message, faq_answer, 'faq', time.time() - start_time)

            return {
                "success": True,
                "response": faq_answer,
                "conversation_id": self.conversation.conversation_id if self.conversation else None,
                "intent": "faq",
                "handled_by": "faq_fastpath",
                "response_time_ms": response_time_ms
            }

        # Step 1: Detect intent and route to appropriate tool
        intent, confidence = self.tools.detect_intent(user_message)

        # Step 2: Try to handle with tools first (for analytics/operations)
        tool_response = None
        if intent in ['analytical', 'operational', 'member_lookup']:
            tool_response = self.tools.route_query(user_message)

            # If tool handled the query, return immediately
            if tool_response:
                # Log chatbot usage
                self._log_chatbot_usage(user_message, tool_response, intent, time.time() - start_time)

                # Save to conversation history
                self._save_message("user", user_message)
                self._save_message("assistant", tool_response, int((time.time() - start_time) * 1000))

                return {
                    "success": True,
                    "response": tool_response,
                    "conversation_id": self.conversation.conversation_id if self.conversation else None,
                    "intent": intent,
                    "handled_by": "tools",
                    "response_time_ms": int((time.time() - start_time) * 1000)
                }

        # Step 3: If tools didn't handle it, use AI chatbot
        return self._chat_with_ai(user_message, start_time, intent)

    def _chat_with_ai(self, user_message, start_time, intent='informational'):
        """
        PERFORMANCE OPTIMIZATION #2: Reduce Ollama Context Size

        Optimizations:
        1. Intent-based context loading (minimal for FAQs, none for analytics)
        2. Reduce conversation history to 0-2 messages based on query type
        3. Strip unnecessary information from system prompts
        4. Use max_tokens=256 for short responses (50% reduction)

        Expected improvement:
        - Memory usage: -40%
        - Processing time: -30-40%
        - Token consumption: -60%
        """
        # BEFORE: Full context for all queries
        # AFTER: Intent-based context optimization

        system_context = ""

        # ========== INTENT-BASED CONTEXT LOADING ==========
        # Analytical queries: Minimal context (just role-based info)
        if intent == 'analytical':
            system_context = "You are FitBot, a gym customer service assistant. Answer briefly and concisely."

        # Operational queries: Minimal context
        elif intent == 'operational':
            system_context = "You are FitBot, a gym system assistant. Provide clear, direct answers."

        # Informational/FAQ fallback: Standard but reduced context
        elif intent == 'informational':
            system_context = self._get_static_base_context()
            # Only add fitness knowledge if explicitly requested
            if any(kw in user_message.lower() for kw in ['workout', 'exercise', 'fitness', 'training', 'gym tips']):
                system_context += self.get_fitness_knowledge()

        # Member lookup: User-specific context only
        elif intent == 'member_lookup':
            if self.user and self.user.is_authenticated:
                system_context = f"You are FitBot. The current user is {self.user.get_full_name()} ({self.user.role})."
            else:
                system_context = "You are FitBot, a gym customer service assistant."

        # Add brief capabilities hint only for staff/admin
        if self.user and self.user.is_staff_or_admin():
            system_context += "\nYou can help with analytics, operations, and member management."

        # Prepare messages for Ollama
        messages = [
            {
                "role": "system",
                "content": system_context
            }
        ]

        # ========== REDUCE CONVERSATION HISTORY (OPTIMIZATION) ==========
        # BEFORE: Context window of 6 messages (or 3 for analytical)
        # AFTER: Dynamic context window based on intent

        if len(self.conversation_history) > 0:
            # Analytical: No history (fresh analysis every time)
            if intent == 'analytical':
                context_window = 0
            # Operational: Last message only
            elif intent == 'operational':
                context_window = 1
            # Informational: Last 1-2 messages max
            elif intent == 'informational':
                context_window = 2
            # Member lookup: No history needed
            elif intent == 'member_lookup':
                context_window = 0
            # Default
            else:
                context_window = min(self.CONTEXT_WINDOW, 2)

            # Add only the necessary messages
            if context_window > 0:
                messages.extend(self.conversation_history[-context_window:])

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        try:
            # Check if HuggingFace API key is configured
            if not self.HF_API_KEY:
                return {
                    "success": False,
                    "error": "HuggingFace API key not configured",
                    "response": "The chatbot is not properly configured. Please contact the administrator."
                }

            # ========== OPTIMIZE HUGGINGFACE PARAMETERS ==========
            hf_options = self.get_hf_options()

            if self.ENABLE_STREAMING:
                # Streaming response
                return self._chat_stream(messages, user_message, start_time, intent)
            else:
                # Standard response with HuggingFace Inference API
                # Format messages for HuggingFace (convert system message to context)
                formatted_messages = []
                for msg in messages:
                    formatted_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

                # Call HuggingFace Inference API
                response = self.hf_client.text_generation(
                    prompt=self._format_prompt_for_hf(formatted_messages),
                    temperature=hf_options['temperature'],
                    max_new_tokens=hf_options['max_new_tokens'],
                    do_sample=True,
                    top_p=0.95
                )

                # Extract assistant message
                assistant_message = response if isinstance(response, str) else response.get('generated_text', '')

                # Calculate response time
                response_time_ms = int((time.time() - start_time) * 1000)

                # Update conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": user_message
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })

                # Save messages to database
                self._save_message("user", user_message)
                self._save_message("assistant", assistant_message, response_time_ms)

                # Log usage
                self._log_chatbot_usage(user_message, assistant_message, intent, time.time() - start_time)

                return {
                    "success": True,
                    "response": assistant_message,
                    "conversation_id": self.conversation.conversation_id if self.conversation else None,
                    "model": self.model,
                    "intent": intent,
                    "handled_by": "ai",
                    "response_time_ms": response_time_ms
                }

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "authentication" in error_msg.lower():
                friendly_error = "HuggingFace API key is invalid or expired. Please check your credentials."
            elif "rate" in error_msg.lower():
                friendly_error = "API rate limit exceeded. Please try again in a moment."
            elif "timeout" in error_msg.lower():
                friendly_error = "Request timed out. The AI service is taking too long to respond."
            else:
                friendly_error = f"Chatbot error: {error_msg}"

            # Log error
            if self.user:
                AuditLog.log(
                    action='chatbot_error',
                    user=self.user,
                    description=f'Chatbot error: {error_msg}',
                    severity='error',
                    error=error_msg
                )

            return {
                "success": False,
                "error": friendly_error,
                "response": "I'm having trouble processing your request right now. Please try again in a moment."
            }

    def _format_prompt_for_hf(self, messages):
        """Format messages for HuggingFace API format"""
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"

        prompt += "Assistant:"
        return prompt

    def _chat_stream(self, messages, user_message, start_time, intent='informational'):
        """Handle streaming responses with HuggingFace API"""
        try:
            if not self.HF_API_KEY:
                return {
                    "success": False,
                    "error": "HuggingFace API key not configured",
                    "response": "The chatbot is not properly configured."
                }

            # HuggingFace InferenceClient doesn't support true streaming in the same way
            # So we'll use the regular text generation and treat it as non-streamed
            hf_options = self.get_hf_options()
            prompt = self._format_prompt_for_hf(messages)

            response = self.hf_client.text_generation(
                prompt=prompt,
                temperature=hf_options['temperature'],
                max_new_tokens=hf_options['max_new_tokens'],
                do_sample=True,
                top_p=0.95
            )

            full_response = response if isinstance(response, str) else response.get('generated_text', '')
            response_time_ms = int((time.time() - start_time) * 1000)

            # Update history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": full_response})

            # Save to database
            self._save_message("user", user_message)
            self._save_message("assistant", full_response, response_time_ms)

            # Log usage
            self._log_chatbot_usage(user_message, full_response, intent, time.time() - start_time)

            return {
                "success": True,
                "response": full_response,
                "conversation_id": self.conversation.conversation_id if self.conversation else None,
                "model": self.model,
                "intent": intent,
                "handled_by": "ai_stream",
                "response_time_ms": response_time_ms,
                "streaming": True
            }
        except Exception as e:
            error_msg = str(e)
            return {
                "success": False,
                "error": error_msg,
                "response": "I encountered an error while processing your request. Please try again."
            }

    def _log_chatbot_usage(self, user_message, bot_response, intent, response_time):
        """
        Log chatbot usage for analytics and monitoring
        """
        if not self.user or not self.user.is_authenticated:
            return

        # Only log for staff/admin (to track their usage of advanced features)
        if self.user.is_staff_or_admin():
            AuditLog.log(
                action='report_generated',
                user=self.user,
                description=f'Chatbot query: {user_message[:100]}...',
                severity='info',
                intent=intent,
                response_time_seconds=response_time,
                query_length=len(user_message),
                response_length=len(bot_response)
            )

    def get_quick_suggestions(self):
        """Get context-aware quick reply suggestions with enhanced features"""
        suggestions = []

        if self.user and self.user.is_authenticated:
            if self.user.role == 'member':
                suggestions = [
                    "What's my membership status?",
                    "How do I check my payment history?",
                    "How do I use my kiosk PIN?",
                    "How can I renew my membership?",
                    "Show me workout tips for beginners",
                    "What are the gym hours?"
                ]
            elif self.user.role in ['admin', 'staff']:
                suggestions = [
                    "Show me today's revenue summary",
                    "Who checked in today?",
                    "Find members expiring in 7 days",
                    "Show pending payment approvals",
                    "This week's attendance report",
                    "Membership growth this month"
                ]
        else:
            suggestions = [
                "What membership plans do you offer?",
                "How much are walk-in passes?",
                "How do I register for the gym?",
                "What payment methods do you accept?",
                "How do I check in at the gym?",
                "Tell me about your facilities"
            ]

        return suggestions

    @staticmethod
    def check_hf_status():
        """Check if HuggingFace API key is configured"""
        hf_api_key = config('HF_API_KEY', default=None)
        if hf_api_key:
            return {
                "status": "configured",
                "message": "HuggingFace API is configured and ready"
            }
        else:
            return {
                "status": "not_configured",
                "message": "HuggingFace API key is not set. Please configure HF_API_KEY environment variable."
            }

    @staticmethod
    def get_supported_models():
        """Get list of supported HuggingFace models"""
        return [
            "mistralai/Mistral-7B-Instruct-v0.2",
            "meta-llama/Llama-2-7b-chat-hf",
            "tiiuae/falcon-7b-instruct",
            "gpt2",  # Smaller model for testing
        ]

    @staticmethod
    def clear_cache():
        """
        Clear all chatbot-related cache.
        Should be called when gym data (plans, passes) is updated.
        """
        cache_keys = [
            'chatbot_static_base_context',
            'chatbot_membership_plans',
            'chatbot_walkin_passes',
            'chatbot_fitness_knowledge',
        ]

        for key in cache_keys:
            cache.delete(key)

        # Clear staff stats cache (varies by date)
        # This is a wildcard delete - in production, use cache.delete_pattern if available
        today = date.today()
        cache.delete(f'chatbot_staff_stats_{today}')


# Legacy compatibility function
def get_database_context(query):
    """
    Query-specific database context retrieval
    (Maintained for backward compatibility)
    """
    query_lower = query.lower()
    context = {}

    # Membership-related queries
    if any(word in query_lower for word in ['membership', 'plan', 'price', 'cost', 'subscribe']):
        plans = MembershipPlan.objects.filter(is_active=True)
        context['plans'] = [
            {
                'name': p.name,
                'price': float(p.price),
                'days': p.duration_days,
                'description': p.description
            } for p in plans
        ]

    # Walk-in queries
    if any(word in query_lower for word in ['walk-in', 'day pass', 'visitor', 'guest']):
        passes = FlexibleAccess.objects.filter(is_active=True)
        context['passes'] = [
            {
                'name': p.name,
                'price': float(p.price),
                'days': p.duration_days
            } for p in passes
        ]

    # Statistics queries
    if any(word in query_lower for word in ['stats', 'statistics', 'how many', 'count']):
        context['stats'] = {
            'total_members': User.objects.filter(role='member').count(),
            'active_memberships': UserMembership.objects.filter(
                status='active',
                end_date__gte=date.today()
            ).count(),
            'checked_in_now': Attendance.objects.filter(
                check_out__isnull=True
            ).count()
        }

    return context
