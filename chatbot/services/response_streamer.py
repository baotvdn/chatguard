class ResponseStreamer:
    """Handles streaming responses from the LangGraph."""

    def __init__(self, graph, state_manager):
        self.graph = graph
        self.state_manager = state_manager

    def stream_response(self, user_message: str, user):
        """Stream a response from the chatbot for a user message."""
        try:
            # Get thread configuration
            config = self.state_manager.get_thread_config(user)
            
            # Prepare messages for processing
            messages = self.state_manager.prepare_messages_for_graph(user, user_message)

            # Stream response from the graph
            for message_chunk, metadata in self.graph.stream(
                {"messages": messages, "user_id": user.id}, 
                config=config, 
                stream_mode="messages"
            ):
                if metadata.get("langgraph_node") == "chatbot" and message_chunk.content:
                    yield message_chunk.content

        except Exception as e:
            yield f"Error: {str(e)}"