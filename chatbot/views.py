from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import StreamingHttpResponse
import json
from .chatbot_service import get_chatbot


def chatbot_page(request):
    """Render the chatbot interface with conversation history."""
    conversation = request.session.get('conversation', [])
    
    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        
        if user_message:
            # Add user message to conversation
            conversation.append({
                'role': 'user', 
                'content': user_message
            })
            
            try:
                # Get chatbot response
                chatbot = get_chatbot()
                bot_response = chatbot.get_response(user_message)
                
                # Add bot response to conversation
                conversation.append({
                    'role': 'assistant', 
                    'content': bot_response
                })
                
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                # Still save the user message even if bot response fails
            
            # Save conversation to session
            request.session['conversation'] = conversation
            
            # Redirect to prevent form resubmission on refresh
            return redirect('chatbot_page')
    
    return render(request, 'chatbot/index.html', {
        'conversation': conversation
    })


def clear_chat(request):
    """Clear the conversation history."""
    request.session['conversation'] = []
    return redirect('chatbot_page')


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
    
    # Add user message to conversation
    conversation = request.session.get('conversation', [])
    conversation.append({
        'role': 'user', 
        'content': user_message
    })
    
    def generate():
        chatbot = get_chatbot()
        full_response = ""
        
        # Stream the response
        for chunk in chatbot.stream_response(user_message):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Add complete response to conversation and save to session
        conversation.append({
            'role': 'assistant', 
            'content': full_response
        })
        request.session['conversation'] = conversation
        request.session.save()
        
        # Send completion signal
        yield f"data: {json.dumps({'complete': True, 'full_response': full_response})}\n\n"
    
    response = StreamingHttpResponse(generate(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response
