"""
Quick test script to verify member lookup patterns are working
Run this to test the chatbot's member lookup detection
"""

def test_member_lookup_patterns():
    """Test that various query patterns are correctly detected"""

    # Import the tools
    import sys
    import os
    import django

    # Setup Django
    sys.path.insert(0, '/home/user/Web-Based-Gym-System-Chatbot-Integration')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_project.settings')
    django.setup()

    from gym_app.chatbot_tools import ChatbotTools
    from gym_app.models import User

    # Test queries that should trigger member lookup
    test_queries = [
        "Can you give me Carlos Bautista's details?",
        "give me Carlo Bautista detail",
        "Carlos Bautista information",
        "What's Lucia Aquino's info",
        "lucia.aquino@gmail.com",
        "show me John Doe's profile",
        "pull up Maria Santos",
        "get me info on Pedro Cruz",
        "look up member Ana Garcia",
        "Roberto Santos detail",
        "information about Juan dela Cruz"
    ]

    print("=" * 70)
    print("MEMBER LOOKUP PATTERN DETECTION TEST")
    print("=" * 70)
    print()

    # Get a staff user for testing (they have permission)
    staff_user = User.objects.filter(role__in=['admin', 'staff']).first()

    if not staff_user:
        print("❌ No staff/admin user found. Create one first.")
        return

    print(f"Testing as: {staff_user.get_full_name()} ({staff_user.role})")
    print()

    # Initialize tools
    tools = ChatbotTools(staff_user)

    # Test each query
    results = []
    for query in test_queries:
        print(f"Query: \"{query}\"")

        # Detect intent
        intent, confidence = tools.detect_intent(query)
        print(f"  Intent: {intent} (confidence: {confidence})")

        # Try to route
        response = tools.route_query(query)

        if response:
            # Check if it's an error or success
            if "❌" in response or "not found" in response.lower():
                status = "⚠️  ROUTED (but member not found - this is expected)"
            elif "requires" in response and "access" in response:
                status = "❌ PERMISSION DENIED"
            else:
                status = "✅ SUCCESS (member found)"

            print(f"  Result: {status}")
            # Show first 150 chars of response
            preview = response[:150].replace('\n', ' ')
            print(f"  Preview: {preview}...")
        else:
            status = "❌ NOT ROUTED (will use AI)"
            print(f"  Result: {status}")

        results.append({
            'query': query,
            'intent': intent,
            'routed': bool(response),
            'status': status
        })
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    routed_count = sum(1 for r in results if r['routed'])
    member_lookup_count = sum(1 for r in results if r['intent'] == 'member_lookup')

    print(f"Total queries tested: {len(test_queries)}")
    print(f"Detected as member_lookup: {member_lookup_count}/{len(test_queries)}")
    print(f"Successfully routed to tools: {routed_count}/{len(test_queries)}")
    print()

    if routed_count == len(test_queries):
        print("🎉 ALL PATTERNS WORKING! All queries were routed to member lookup.")
    elif routed_count > 0:
        print(f"⚠️  PARTIAL SUCCESS: {routed_count} queries routed, {len(test_queries) - routed_count} fell back to AI")
        print("\nQueries that failed:")
        for r in results:
            if not r['routed']:
                print(f"  - \"{r['query']}\"")
    else:
        print("❌ PATTERNS NOT WORKING: No queries were routed to tools")

    print()
    print("Note: 'member not found' errors are expected if test members don't exist.")
    print("The important thing is that queries are being ROUTED to the lookup tool.")


if __name__ == '__main__':
    test_member_lookup_patterns()
