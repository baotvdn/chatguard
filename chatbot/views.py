import json

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render

from chatbot.services.chatbot_service import get_chatbot


@login_required
def chatbot_page(request):
    """Render the chatbot interface with conversation history."""
    chatbot = get_chatbot()
    # Get conversation history from LangGraph state
    messages = chatbot.get_conversation_history(request.user)

    # Convert LangGraph messages to template format
    conversation = []
    for msg in messages:
        role = "user" if msg.type == "human" else "assistant"
        conversation.append({"role": role, "content": msg.content})

    return render(request, "chatbot/index.html", {"conversation": conversation})


@login_required
def clear_chat(request):
    """Clear the conversation history from LangGraph state."""
    chatbot = get_chatbot()
    chatbot.clear_conversation(request.user)
    return redirect("chatbot_page")


@login_required
def stream_chat(request):
    """Stream chatbot response."""
    user_message = request.POST.get("message", "").strip()

    def generate():
        chatbot = get_chatbot()

        # Stream the response (message saving is handled inside stream_response)
        for chunk in chatbot.stream_response(user_message, request.user):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        # Send completion signal
        yield f"data: {json.dumps({'complete': True})}\n\n"

    response = StreamingHttpResponse(generate(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    return response


def register(request):
    """User registration view."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("chatbot_page")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})


@user_passes_test(lambda u: u.is_superuser)
def debug_state(request):
    """Debug endpoint to inspect LangGraph conversation state (admin only)."""
    user_id = request.GET.get("user_id")

    if not user_id:
        return JsonResponse({"error": "user_id parameter required"}, status=400)

    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(id=user_id)

        chatbot = get_chatbot()
        state_snapshot = chatbot.get_conversation_state(user)

        # Convert state to JSON-serializable format
        debug_info = {
            "thread_id": f"user_{user.id}",
            "username": user.username,
            "state_values": {
                "messages": [
                    {"type": getattr(msg, "type", "unknown"), "content": getattr(msg, "content", str(msg))}
                    for msg in state_snapshot.values.get("messages", [])
                ],
                "message_count": len(state_snapshot.values.get("messages", [])),
            },
            "next_nodes": list(state_snapshot.next),
            "config": {
                "thread_id": state_snapshot.config.get("configurable", {}).get("thread_id"),
                "checkpoint_id": state_snapshot.config.get("configurable", {}).get("checkpoint_id"),
            },
            "parent_config": state_snapshot.parent_config,
        }

        return JsonResponse(debug_info, json_dumps_params={"indent": 2})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
