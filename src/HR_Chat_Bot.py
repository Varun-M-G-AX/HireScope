import re
import streamlit as st
from datetime import datetime
# Import collection and the openai module directly from utils.py
from utils import collection, openai # Now importing the 'openai' module

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="HireScope Chat",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SESSION STATE MANAGEMENT ---
# Initialize session state for multi-chat management.
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}

if "active_chat_id" not in st.session_state:
    # Create a default first chat
    chat_id = f"chat_{datetime.now().timestamp()}"
    st.session_state.active_chat_id = chat_id
    st.session_state.all_chats[chat_id] = {
        "name": f"New Chat - {datetime.now():%Y-%m-%d %H:%M}",
        "messages": [] # Start with no messages
    }

# The system prompt is now a constant, not stored in the chat history itself.
SYSTEM_PROMPT = (
    "You are an expert recruiting assistant for HireScope. Your name is 'ScopeAI'. "
    "You must answer questions based *only* on the provided résumé context for the candidates. "
    "Be concise and professional. When asked to compare candidates, create a markdown table. "
    "If the provided résumés do not contain the answer, say 'The provided résumés do not contain information on this topic.' "
    "If the user's query is unrelated to recruiting, candidates, or the provided context, politely state: "
    "'I can only answer questions about candidates based on their résumés.'"
)

# --- 3. CORE LOGIC (RAG ENGINE) ---
def get_rag_response(query: str, chat_history: list):
    """
    Retrieves context from ChromaDB and generates a response using the LLM.
    """
    # 1. Retrieve relevant résumé snippets from the vector database
    try:
        total_docs = collection.count()
        if total_docs == 0:
            return "My knowledge base is empty. Please upload some résumés first using the 'Upload Résumés' page.", []
            
        results = collection.query(
            query_texts=[query],
            n_results=min(5, total_docs) # Retrieve up to 5 relevant documents
        )
        context_docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
            
        if not context_docs:
            return "I couldn't find any résumés in my database that match your query. Please try rephrasing it.", []

    except Exception as e:
        st.error(f"Database query failed: {e}")
        return "I am having trouble accessing the candidate database right now. Please try again later.", []

    # 2. Construct the prompt for the LLM
    context = "\n\n---\n\n".join(context_docs)
    prompt_with_context = (
        f"**Résumé Context:**\n{context}\n\n"
        f"**User Query:**\n{query}"
    )
        
    # 3. Create the message list for the API call
    # Filter out 'sources' from chat_history as it's not a standard OpenAI role/content field
    filtered_chat_history = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]

    messages_for_api = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *filtered_chat_history, # Include past messages for conversational context
        {"role": "user", "content": prompt_with_context}
    ]

    # 4. Call the LLM using the imported openai module
    try:
        response = openai.chat.completions.create( # Now using 'openai' directly
            model="gpt-4o",
            messages=messages_for_api,
            temperature=0.0 # Low temperature for factual, grounded answers
        )
        reply = response.choices[0].message.content
        return reply, metadatas # Return the answer and the sources used
    except Exception as e:
        st.error(f"Error communicating with the AI model: {e}")
        return "I'm sorry, I encountered an error while generating a response. Please check your API key or try again later.", []


# --- 4. SIDEBAR UI (CHAT MANAGEMENT) ---
with st.sidebar:
    st.title("HireScope Chat")
    st.markdown("---")
        
    # --- New Chat Button ---
    if st.button("➕ Start New Chat", use_container_width=True, help="Create a fresh chat session."):
        chat_id = f"chat_{datetime.now().timestamp()}"
        st.session_state.active_chat_id = chat_id
        st.session_state.all_chats[chat_id] = {
            "name": f"New Chat - {datetime.now():%Y-%m-%d %H:%M}",
            "messages": []
        }
        st.rerun()

    st.markdown("---")
    st.subheader("📂 Your Chat Sessions")
    st.markdown("Switch between your ongoing conversations.")

    # --- Chat Selection ---
    chat_names = {cid: data["name"] for cid, data in st.session_state.all_chats.items()}
    active_chat_id = st.session_state.active_chat_id
        
    selected_chat_id = st.radio(
        "Select a chat:",
        options=list(chat_names.keys()),
        format_func=lambda cid: chat_names[cid],
        index=list(chat_names.keys()).index(active_chat_id),
        key="chat_selector" # Added a key for stability
    )

    if selected_chat_id != active_chat_id:
        st.session_state.active_chat_id = selected_chat_id
        st.rerun()

    # --- Active Chat Management (Rename & Delete) ---
    st.markdown("---")
    st.subheader("⚙️ Manage Current Chat")
    active_chat_data = st.session_state.all_chats[active_chat_id]

    new_name = st.text_input("📝 Rename Chat:", value=active_chat_data["name"], key="rename_chat_input")
    if new_name != active_chat_data["name"]:
        active_chat_data["name"] = new_name
        st.toast("Chat renamed successfully!")
        # No rerun needed for just renaming, state updates automatically

    # Delete confirmation logic
    delete_button_clicked = st.button("🗑️ Delete This Chat", use_container_width=True, help="Permanently delete the current chat session.")

    if delete_button_clicked:
        if len(st.session_state.all_chats) > 1:
            if "confirm_delete" not in st.session_state or not st.session_state.confirm_delete:
                st.session_state.confirm_delete = True
                st.warning("Are you sure you want to delete this chat? Click 'Delete This Chat' again to confirm.")
            else:
                del st.session_state.all_chats[active_chat_id]
                del st.session_state.confirm_delete # Reset confirmation
                st.session_state.active_chat_id = list(st.session_state.all_chats.keys())[0] # Switch to first available chat
                st.toast("Chat deleted successfully.")
                st.rerun()
        else:
            st.error("Cannot delete the last remaining chat. Create a new one first if you wish to start over.")
            # Reset confirmation if it was set, as deletion was blocked
            if "confirm_delete" in st.session_state:
                del st.session_state.confirm_delete
    else:
        # If delete button was not clicked, and confirmation was pending, reset it
        if "confirm_delete" in st.session_state and st.session_state.confirm_delete:
            del st.session_state.confirm_delete


# --- 5. MAIN CHAT INTERFACE ---
st.header(f"💬 {st.session_state.all_chats[active_chat_id]['name']}")
st.markdown(f"**Assistant:** ScopeAI | **Knowledge Base:** {collection.count()} Résumés in ChromaDB")

# Display chat history
chat_messages = st.session_state.all_chats[active_chat_id]["messages"]

# Use a container for chat messages to ensure scrollability if needed
chat_container = st.container(height=500, border=True) # Fixed height with scrollbar

with chat_container:
    # Welcome message for new, empty chats
    if not chat_messages:
        st.info(
            "Welcome to the HireScope chat space! "
            "Ask me anything about the candidates in your database.\n\n"
            "**For example:**\n"
            "- 'Who has more than 5 years of experience with Python?'\n"
            "- 'Compare the skills of John Doe and Jane Smith.'\n"
            "- 'Find candidates who are project managers.'"
        )
    else:
        for msg in chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                # Show sources if they exist in the message metadata
                if "sources" in msg and msg["sources"]:
                    with st.expander("📚 Sources"):
                        for source in msg["sources"]:
                            st.markdown(f"**Candidate:** {source.get('name', 'N/A')} (ID: `{source.get('candidate_id', 'N/A')}`)")
                            # Optionally display more details from source metadata if available
                            # st.json(source) # For debugging/detailed view

# Handle user input at the bottom
user_query = st.chat_input("Ask about candidates, skills, experience...", key="chat_input")
if user_query:
    # Add user message to history and display it
    chat_messages.append({"role": "user", "content": user_query})
    # Rerun to display user message immediately in the chat_container
    st.rerun() 

# This block executes after rerun, displaying the assistant's response
if chat_messages and chat_messages[-1]["role"] == "user":
    # Ensure the last message is from the user before generating a response
    with st.chat_message("assistant"):
        with st.spinner("Searching résumés and thinking..."):
            response, sources = get_rag_response(user_query, chat_messages[:-1]) # Pass all but the current user message as chat history
            st.markdown(response)
                
            # Display sources if any were used
            if sources:
                with st.expander("📚 Sources"):
                    for source in sources:
                        st.markdown(f"**Candidate:** {source.get('name', 'N/A')} (ID: `{source.get('candidate_id', 'N/A')}`)")
                        # st.json(source) # For debugging/detailed view
    # Add assistant message to history
    chat_messages.append({"role": "assistant", "content": response, "sources": sources})
    st.rerun() # Rerun to update the chat history with the assistant's response

st.markdown("---")
st.info("Remember to upload résumés on the 'Upload Résumés' page to populate the knowledge base!")