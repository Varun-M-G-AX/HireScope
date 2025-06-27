import re
import streamlit as st
from datetime import datetime

# Import collection and the openai module directly from utils.py
# Ensure utils.py is in the same directory or accessible via PYTHONPATH
from utils import collection, openai

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="HireScope Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SESSION STATE MANAGEMENT ---
# Initialize session state for multi-chat management.
# "all_chats" stores a dictionary of chat sessions, keyed by their unique IDs.
# Each chat session contains a "name" and a list of "messages".
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}

# "active_chat_id" tracks the currently selected chat session.
if "active_chat_id" not in st.session_state:
    # Create a default first chat if none exists
    chat_id = f"chat_{datetime.now().timestamp()}" # Unique ID for the chat
    st.session_state.active_chat_id = chat_id
    st.session_state.all_chats[chat_id] = {
        "name": f"New Chat - {datetime.now():%Y-%m-%d %H:%M}", # Default name
        "messages": [] # Start with an empty list of messages
    }

# The system prompt is a constant and defines the AI's persona and rules.
# It's not stored in the chat history itself but prepended to each API call.
SYSTEM_PROMPT = (
    "You are an expert recruiting assistant for HireScope. Your name is 'ScopeAI'. "
    "You must answer questions based *only* on the provided résumé context for the candidates. "
    "Be concise and professional. When asked to compare candidates, create a markdown table. "
    "If the provided résumés do not contain the answer, say 'The provided résumés do not contain information on this topic.' "
    "If the user's query is unrelated to recruiting, candidates, or the provided context, politely state: "
    "'I can only answer questions about candidates based on their résumés.'"
)

# --- 3. CORE LOGIC (RAG ENGINE) ---
def get_rag_response(query: str, chat_history_for_llm: list):
    """
    Retrieves relevant context from ChromaDB based on the user's query
    and generates an AI response using the OpenAI LLM.

    Args:
        query (str): The user's current query.
        chat_history_for_llm (list): A list of previous messages (role, content)
                                     to provide conversational context to the LLM.

    Returns:
        tuple: A tuple containing the AI's response (str) and a list of
               source metadatas (list of dicts).
    """
    # 1. Retrieve relevant résumé snippets from the vector database (ChromaDB)
    try:
        total_docs = collection.count()
        if total_docs == 0:
            return (
                "My knowledge base is empty. Please upload some résumés first "
                "using the 'Upload Résumés' page to enable candidate queries."
            ), []
            
        # Query ChromaDB for documents most similar to the user's query
        # Retrieve up to 5 relevant documents, or fewer if total_docs is less than 5
        results = collection.query(
            query_texts=[query],
            n_results=min(5, total_docs)
        )
        context_docs = results.get("documents", [[]])[0] # Extracted text content
        metadatas = results.get("metadatas", [[]])[0]   # Associated metadata (e.g., candidate name, ID)
            
        if not context_docs or all(not d.strip() for d in context_docs):
            return (
                "I couldn't find any résumés in my database that directly match your query. "
                "Please try rephrasing it or ensure relevant résumés have been uploaded."
            ), []

    except Exception as e:
        st.error(f"Database query failed: {e}")
        return "I am having trouble accessing the candidate database right now. Please try again later.", []

    # 2. Construct the full prompt for the LLM, including the retrieved context
    context = "\n\n---\n\n".join(context_docs)
    prompt_with_context = (
        f"**Résumé Context:**\n{context}\n\n"
        f"**User Query:**\n{query}"
    )
        
    # 3. Create the message list for the OpenAI API call
    # This list includes the system prompt, historical chat messages, and the current user query with context.
    messages_for_api = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *chat_history_for_llm, # Unpack past messages for conversational context
        {"role": "user", "content": prompt_with_context}
    ]

    # 4. Call the OpenAI LLM (GPT-4o) to generate a response
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_api,
            temperature=0.0 # Low temperature for factual, grounded answers based on context
        )
        reply = response.choices[0].message.content
        return reply, metadatas # Return the AI's answer and the sources (metadata) used
    except Exception as e:
        st.error(f"Error communicating with the AI model: {e}")
        return "I'm sorry, I encountered an error while generating a response. Please check your OpenAI API key or try again later.", []

# --- Helper Functions for Chat Logic ---
def is_greeting(text: str) -> bool:
    """Checks if the input text is a simple greeting."""
    return bool(re.fullmatch(r"(hi|hello|hey|thanks|thank you|good (morning|afternoon|evening))[!. ]*", text.strip(), re.I))

def is_recruitment_query(query: str) -> bool:
    """
    Uses a small LLM call to determine if a query is related to recruiting/candidates.
    This acts as a guardrail for off-topic questions.
    """
    prompt = (
        "Respond ONLY with 'Yes' or 'No'. Does this query relate to candidates, "
        "resumes, recruiting, jobs, or HR?\n"
        f"Query: \"{query}\""
    )
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o", # Using gpt-4o for this classification
            messages=[{"role": "user", "content": prompt}],
            temperature=0 # Keep temperature low for clear Yes/No
        )
        return resp.choices[0].message.content.strip().lower().startswith("yes")
    except Exception as e:
        st.warning(f"Could not classify query relevance due to API error: {e}. Proceeding with RAG.")
        return True # Default to True if classification fails, to allow RAG to try


# --- 4. SIDEBAR UI (CHAT MANAGEMENT) ---
with st.sidebar:
    st.title("HireScope")
    st.markdown("---")
        
    # --- New Chat Button ---
    if st.button("➕ Start New Chat", use_container_width=True, help="Create a fresh chat session."):
        chat_id = f"chat_{datetime.now().timestamp()}"
        st.session_state.active_chat_id = chat_id
        st.session_state.all_chats[chat_id] = {
            "name": f"New Chat - {datetime.now():%Y-%m-%d %H:%M}",
            "messages": []
        }
        st.toast("New chat created!", icon="✨")
        st.rerun() # Rerun to switch to the new chat immediately

    st.markdown("---")
    st.subheader("📂 Your Chat Sessions")
    st.markdown("Switch between your ongoing conversations.")

    # Get current chat names for display in the radio button
    chat_names = {cid: data["name"] for cid, data in st.session_state.all_chats.items()}
    active_chat_id = st.session_state.active_chat_id
        
    # Streamlit radio button for chat selection
    selected_chat_id = st.radio(
        "Select a chat:",
        options=list(chat_names.keys()), # Use chat IDs as options
        format_func=lambda cid: chat_names[cid], # Display chat names
        index=list(chat_names.keys()).index(active_chat_id), # Set default selection
        key="chat_selector" # Unique key for the widget
    )

    # If a different chat is selected, update active_chat_id and rerun
    if selected_chat_id != active_chat_id:
        st.session_state.active_chat_id = selected_chat_id
        st.rerun()

    # --- Active Chat Management (Rename & Delete) ---
    st.markdown("---")
    st.subheader("⚙️ Manage Current Chat")
    # Get the data for the currently active chat
    active_chat_data = st.session_state.all_chats[active_chat_id]

    # Text input for renaming the active chat
    new_name = st.text_input("📝 Rename Chat:", value=active_chat_data["name"], key="rename_chat_input")
    if new_name != active_chat_data["name"] and new_name.strip(): # Check for actual change and non-empty name
        # Ensure the new name isn't already taken by another chat
        if new_name in chat_names.values() and new_name != active_chat_data["name"]:
            st.warning("A chat with this name already exists. Please choose a different name.")
        else:
            active_chat_data["name"] = new_name
            st.toast("Chat renamed successfully!", icon="✅")
            # No rerun needed for just renaming, state updates automatically

    # Delete confirmation logic for the active chat
    delete_button_clicked = st.button("🗑️ Delete This Chat", use_container_width=True, help="Permanently delete the current chat session.")

    if delete_button_clicked:
        # Prevent deleting the last remaining chat session
        if len(st.session_state.all_chats) > 1:
            # Implement a double-click confirmation for deletion
            if "confirm_delete" not in st.session_state or not st.session_state.confirm_delete:
                st.session_state.confirm_delete = True
                st.warning("Are you sure you want to delete this chat? Click 'Delete This Chat' again to confirm.")
            else:
                del st.session_state.all_chats[active_chat_id] # Delete the chat
                del st.session_state.confirm_delete # Reset confirmation state
                # Switch to the first available chat after deletion
                st.session_state.active_chat_id = list(st.session_state.all_chats.keys())[0]
                st.toast("Chat deleted successfully.", icon="🗑️")
                st.rerun() # Rerun to update the UI with the new active chat
        else:
            st.error("Cannot delete the last remaining chat. Create a new one first if you wish to start over.")
            # Reset confirmation if deletion was blocked
            if "confirm_delete" in st.session_state:
                del st.session_state.confirm_delete
    else:
        # If the delete button was not clicked, and a confirmation was pending, reset it
        if "confirm_delete" in st.session_state and st.session_state.confirm_delete:
            del st.session_state.confirm_delete

    # Display the ChromaDB résumé count from utils.py for quick reference
    # This assumes utils.py already has the st.sidebar.write for the count
    # If not, you could add:
    # try:
    #     st.sidebar.markdown(f"📊 **Résumés in DB:** {collection.count()}")
    # except Exception as e:
    #     st.sidebar.error(f"Error getting DB count: {e}")


# --- 5. MAIN CHAT INTERFACE ---
# Display the name of the currently active chat
st.header(f"💬 {st.session_state.all_chats[active_chat_id]['name']}")
st.markdown(f"**Assistant:** ScopeAI | **Knowledge Base:** {collection.count()} Résumés in ChromaDB")

# Get the messages for the active chat session
chat_messages = st.session_state.all_chats[active_chat_id]["messages"]

# Use a fixed-height container for chat messages with a scrollbar,
# mimicking a typical chat interface.
chat_container = st.container(height=500, border=True)

with chat_container:
    # Display a welcome message if the current chat is empty
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
        # Iterate through messages and display them using st.chat_message
        # Start from index 0 now, as the system prompt is handled separately in get_rag_response
        for msg in chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                # If the message has associated sources (from AI response), display them in an expander
                if "sources" in msg and msg["sources"]:
                    with st.expander("📚 Sources"):
                        for source in msg["sources"]:
                            st.markdown(f"**Candidate:** {source.get('name', 'N/A')} (ID: `{source.get('candidate_id', 'N/A')}`)")
                            # You could add more details from the source metadata here if needed
                            # st.json(source) # For debugging/detailed view of source metadata

# Handle user input at the bottom of the page
user_query = st.chat_input("Ask about candidates, skills, experience...", key="chat_input")

if user_query:
    # Add the user's query to the current chat's messages
    chat_messages.append({"role": "user", "content": user_query})
    # Rerun to immediately display the user's message in the chat container
    st.rerun() 

# This block executes after a rerun, specifically when the last message is from the user
if chat_messages and chat_messages[-1]["role"] == "user":
    # Prepare chat history for the LLM call: filter out 'sources' and system prompt
    # The system prompt is prepended in get_rag_response
    # We pass all messages *except* the very last user query, as it's handled separately
    # in the prompt_with_context
    chat_history_for_llm = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in chat_messages[:-1] # Exclude the current user query
        if msg["role"] != "system" # Exclude any old system messages if they somehow got in
    ]

    # Get and display the assistant's response
    with st.chat_message("assistant"):
        with st.spinner("Searching résumés and thinking..."):
            # Call the RAG engine to get the AI's reply and its sources
            response, sources = get_rag_response(user_query, chat_history_for_llm)
            st.markdown(response)
                
            # Display sources if any were used
            if sources:
                with st.expander("📚 Sources"):
                    for source in sources:
                        st.markdown(f"**Candidate:** {source.get('name', 'N/A')} (ID: `{source.get('candidate_id', 'N/A')}`)")
                        # st.json(source) # For debugging/detailed view

    # Add the assistant's response to the current chat's messages, including sources
    chat_messages.append({"role": "assistant", "content": response, "sources": sources})
    st.rerun() # Rerun to update the chat history with the assistant's response

st.markdown("---")
st.info("Remember to upload résumés on the 'Upload Résumés' page to populate the knowledge base!")