from chatbot.services.state import State


def domain_agent(state: State, llm) -> State:
    return {"messages": [llm.invoke(state["messages"])]}
