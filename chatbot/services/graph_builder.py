import psycopg
from django.conf import settings
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langgraph.graph import END, START, StateGraph

from chatbot.services.agents.domain_agent import domain_agent
from chatbot.services.agents.safety_agent import safety_agent
from chatbot.services.state import State


class GraphBuilder:
    """Responsible for building and configuring the LangGraph conversation graph."""

    def __init__(self):
        self.llm = init_chat_model("anthropic:claude-3-5-sonnet-latest")
        self._graph = None
        self._store = None
        self._checkpointer = None

    def _get_store_and_checkpointer(self):
        """Get or create PostgreSQL store and checkpointer."""
        if self._store is None or self._checkpointer is None:
            conn = psycopg.connect(settings.DATABASE_URL, autocommit=True)
            
            self._store = PostgresStore(conn)
            self._store.setup()  # Run migrations
            
            self._checkpointer = PostgresSaver(conn)
            self._checkpointer.setup()  # Create tables
            
        return self._store, self._checkpointer

    def build_graph(self):
        """Build the complete conversation graph with safety and domain agents."""
        if self._graph is not None:
            return self._graph
            
        graph_builder = StateGraph(State)
        
        # Add nodes
        graph_builder.add_node("safety", lambda state: safety_agent(state, self.llm))
        graph_builder.add_node("chatbot", lambda state: domain_agent(state, self.llm))

        # Define conditional flow
        def should_continue(state):
            """Check if safety agent blocked the message."""
            messages = state.get("messages", [])
            if messages and messages[-1].type == "ai":
                return "end"
            return "continue"

        # Define graph flow: START -> safety -> (conditional) -> chatbot/END
        graph_builder.add_edge(START, "safety")
        graph_builder.add_conditional_edges("safety", should_continue, {"continue": "chatbot", "end": END})
        graph_builder.add_edge("chatbot", END)

        # Get store and checkpointer
        store, checkpointer = self._get_store_and_checkpointer()
        
        # Compile with both checkpointer and store
        self._graph = graph_builder.compile(
            checkpointer=checkpointer,
            store=store
        )
            
        return self._graph
