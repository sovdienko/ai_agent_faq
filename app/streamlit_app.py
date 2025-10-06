"""Simple chat app built with Streamlit and Pydantic AI.

Run with: streamlit run app/streamlit_app.py
"""

import asyncio
import os
from dotenv import load_dotenv
import streamlit as st

import ingest
import search_agent
import logs

# Load environment variables
load_dotenv()

# Configuration
REPO_OWNER = "DataTalksClub"
REPO_NAME = "faq"


@st.cache_resource
def initialize_index():
    """Initialize and cache the document index."""
    def filter(doc):
        return 'data-engineering' in doc['filename']

    with st.spinner("Indexing repository data..."):
        index = ingest.index_data(REPO_OWNER, REPO_NAME, filter=filter)
    return index


@st.cache_resource
def initialize_agent(_index):
    """Initialize and cache the search agent."""
    agent = search_agent.init_agent(_index, REPO_OWNER, REPO_NAME)
    return agent


def main():
    st.set_page_config(
        page_title="AI FAQ Assistant",
        page_icon="🤖",
        layout="centered"
    )

    st.title(f"🤖 AI FAQ Assistant")
    st.caption(f"Ask questions about {REPO_OWNER}/{REPO_NAME}")

    # Initialize index and agent
    index = initialize_index()
    agent = initialize_agent(index)

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Your question:"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Run agent asynchronously
                    response = asyncio.run(agent.run(user_prompt=prompt))

                    # Log the interaction
                    logs.log_interaction_to_file(agent, response.new_messages())

                    # Display response
                    assistant_response = response.output
                    st.markdown(assistant_response)

                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })

                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message
                    })

    # Sidebar with controls
    with st.sidebar:
        st.header("Options")

        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

        st.divider()

        st.subheader("About")
        st.write(f"""
        This chatbot answers questions about the
        **{REPO_OWNER}/{REPO_NAME}** repository
        using AI-powered search.
        """)

        st.divider()

        st.caption(f"Total messages: {len(st.session_state.messages)}")


if __name__ == "__main__":
    main()
