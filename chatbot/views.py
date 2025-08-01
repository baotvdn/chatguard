import json

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, render

from chatbot.models import Conversation, Message
from chatbot.services.chatbot_service import get_chatbot


@login_required
def chatbot_page(request):
    """Render the chatbot interface with conversation history."""
    conversation_obj, _ = Conversation.objects.get_or_create(user=request.user, defaults={"user": request.user})
    conversation = conversation_obj.get_conversation_history()

    return render(request, "chatbot/index.html", {"conversation": conversation})


@login_required
def clear_chat(request):
    """Clear the conversation history."""
    conversation_obj = Conversation.objects.filter(user=request.user).first()
    if conversation_obj:
        conversation_obj.messages.all().delete()
    return redirect("chatbot_page")


@login_required
def stream_chat(request):
    """Stream chatbot response."""
    user_message = request.POST.get("message", "").strip()

    # Get or create conversation for this user
    conversation_obj, _ = Conversation.objects.get_or_create(user=request.user, defaults={"user": request.user})

    # Save user message to database
    Message.objects.create(conversation=conversation_obj, role=Message.RoleChoices.USER, content=user_message)

    def generate():
        chatbot = get_chatbot()
        full_response = ""

        # Stream the response
        for chunk in chatbot.stream_response(user_message, request.user):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        # Save complete response to database
        Message.objects.create(conversation=conversation_obj, role=Message.RoleChoices.ASSISTANT, content=full_response)

        # Send completion signal
        yield f"data: {json.dumps({'complete': True, 'full_response': full_response})}\n\n"

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
