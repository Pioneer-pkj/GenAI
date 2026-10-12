from google.adk.agents.context import Context
from google.genai import types

def check_access(context: Context):
    """
    Check if the user has access to the data
    """
    session =  context._invocation_context.session
    print(f"************callback result *********",session)
    user = session.user_id

    hr_team = ['pankaj', 'sanket', 'rihansh']

    if user in hr_team:
       print("✅ [callback] User {user} is authorized to access this application")
       return None
    else:
        print (f"❌ [callback] User {user} is not authorized to access this application")
        return types.Content(
            parts=[types.Part(text=f"You do not have access to HR Agent, user {user} is not in HR team")],
            role="model"  
        )

def log_completion(callback_context: Context):
    print("======== *** Completion *** ========")
    session = callback_context._invocation_context.session
    current_invocation_id = getattr(callback_context, "invocation_id", None)

    # 1. Filter events for current invocation (or use all session.events for total session history)
    invocation_events = [
        e for e in session.events
        if getattr(e, "invocation_id", None) == current_invocation_id
    ] if current_invocation_id else session.events

    # 2. Extract Token Usage
    prompt_tokens = 0
    candidate_tokens = 0
    thoughts_tokens = 0
    total_tokens = 0

    for event in invocation_events:
        usage = getattr(event, "usage_metadata", None)
        if usage:
            total_tokens += getattr(usage, "total_token_count", 0) or 0
            prompt_tokens += getattr(usage, "prompt_token_count", 0) or 0
            candidate_tokens += getattr(usage, "candidates_token_count", 0) or 0
            thoughts_tokens += getattr(usage, "thoughts_token_count", 0) or 0

    # 3. Extract Time Consumed (Duration in seconds)
    time_consumed = 0.0
    if invocation_events:
        start_time = invocation_events[0].timestamp
        end_time = invocation_events[-1].timestamp
        time_consumed = round(end_time - start_time, 3)

    print(f"⏱️ Time Consumed: {time_consumed}s")
    print(f"🔢 Total Tokens Consumed: {total_tokens}")
    print(f"   ├── Prompt Tokens: {prompt_tokens}")
    print(f"   ├── Candidate Tokens: {candidate_tokens}")
    print(f"   └── Thoughts Tokens: {thoughts_tokens}")

    
