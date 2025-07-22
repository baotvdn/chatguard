from django.shortcuts import render, redirect
from django.contrib import messages
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
