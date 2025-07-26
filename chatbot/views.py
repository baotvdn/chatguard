from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import StreamingHttpResponse
import json
from .chatbot_service import get_chatbot
from .models import Conversation, Message


@login_required
def chatbot_page(request):
    """Render the chatbot interface with conversation history."""
    # Get or create conversation for this user
    conversation_obj, _ = Conversation.objects.get_or_create(
        user=request.user,
        defaults={'user': request.user}
    )
    
    # Get all messages for this conversation
    messages_list = conversation_obj.messages.all()
    conversation = [
        {'role': msg.role, 'content': msg.content}
        for msg in messages_list
    ]
    
    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        
        if user_message:
            # Save user message to database
            Message.objects.create(
                conversation=conversation_obj,
                role=Message.RoleChoices.USER,
                content=user_message
            )
            
            try:
                # Get chatbot response
                chatbot = get_chatbot()
                bot_response = chatbot.get_response(user_message, request.user)
                
                # Save bot response to database
                Message.objects.create(
                    conversation=conversation_obj,
                    role=Message.RoleChoices.ASSISTANT,
                    content=bot_response
                )
                
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
            
            # Redirect to prevent form resubmission on refresh
            return redirect('chatbot_page')
    
    return render(request, 'chatbot/index.html', {
        'conversation': conversation
    })


@login_required
def clear_chat(request):
    """Clear the conversation history."""
    # Delete all messages for this user's conversation
    conversation_obj = Conversation.objects.filter(user=request.user).first()
    if conversation_obj:
        conversation_obj.messages.all().delete()
    return redirect('chatbot_page')


@login_required
def stream_chat(request):
    """Stream chatbot response."""
    if request.method != 'POST':
        return StreamingHttpResponse(
            json.dumps({"error": "Only POST method allowed"}),
            content_type='application/json'
        )
    
    user_message = request.POST.get('message', '').strip()
    if not user_message:
        return StreamingHttpResponse(
            json.dumps({"error": "Message is required"}),
            content_type='application/json'
        )
    
    # Get or create conversation for this user
    conversation_obj, _ = Conversation.objects.get_or_create(
        user=request.user,
        defaults={'user': request.user}
    )
    
    # Save user message to database
    Message.objects.create(
        conversation=conversation_obj,
        role=Message.RoleChoices.USER,
        content=user_message
    )
    
    def generate():
        chatbot = get_chatbot()
        full_response = ""
        
        # Stream the response
        for chunk in chatbot.stream_response(user_message):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Save complete response to database
        Message.objects.create(
            conversation=conversation_obj,
            role=Message.RoleChoices.ASSISTANT,
            content=full_response
        )
        
        # Send completion signal
        yield f"data: {json.dumps({'complete': True, 'full_response': full_response})}\n\n"
    
    response = StreamingHttpResponse(generate(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response


def register(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('chatbot_page')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
