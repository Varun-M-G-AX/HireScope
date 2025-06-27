import re
import streamlit as st
from datetime import datetime
# Assuming 'collection' is your ChromaDB collection and 'openai' is the configured client
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
            return "My knowledge base is empty. Please upload some résumés first.", []
            
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
        return "I am having trouble accessing the candidate database right now.", []

    # 2. Construct the prompt for the LLM
    context = "\n\n---\n\n".join(context_docs)
    prompt_with_context = (
        f"**Résumé Context:**\n{context}\n\n"
        f"**User Query:**\n{query}"
    )
    
    # 3. Create the message list for the API call
    messages_for_api = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *chat_history, # Include past messages for conversational context
        {"role": "user", "content": prompt_with_context}
    ]

    # 4. Call the LLM
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_api,
            temperature=0.0 # Low temperature for factual, grounded answers
        )
        reply = response.choices[0].message.content
        return reply, metadatas # Return the answer and the sources used
    except Exception as e:
        st.error(f"Error communicating with the AI model: {e}")
        return "I'm sorry, I encountered an error while generating a response.", []


# --- 4. SIDEBAR UI (CHAT MANAGEMENT) ---
with st.sidebar:
    st.title("HireScope")
    st.write("---")
    
    # --- New Chat Button ---
    if st.button("➕ New Chat", use_container_width=True):
        chat_id = f"chat_{datetime.now().timestamp()}"
        st.session_state.active_chat_id = chat_id
        st.session_state.all_chats[chat_id] = {
            "name": f"New Chat - {datetime.now():%Y-%m-%d %H:%M}",
            "messages": []
        }
        st.rerun()

    st.write("---")
    st.subheader("📂 Chat Sessions")

    # --- Chat Selection ---
    chat_names = {cid: data["name"] for cid, data in st.session_state.all_chats.items()}
    active_chat_id = st.session_state.active_chat_id
    
    selected_chat_id = st.radio(
        "Select a chat:",
        options=list(chat_names.keys()),
        format_func=lambda cid: chat_names[cid],
        index=list(chat_names.keys()).index(active_chat_id)
    )

    if selected_chat_id != active_chat_id:
        st.session_state.active_chat_id = selected_chat_id
        st.rerun()

    # --- Active Chat Management (Rename & Delete) ---
    st.write("---")
    st.subheader("Manage Active Chat")
    active_chat_data = st.session_state.all_chats[active_chat_id]

    new_name = st.text_input("📝 Rename:", value=active_chat_data["name"])
    if new_name != active_chat_data["name"]:
        active_chat_data["name"] = new_name
        st.toast("Chat renamed!")

    if st.button("🗑️ Delete Chat", use_container_width=True):
        # Prevent deleting the last chat
        if len(st.session_state.all_chats) > 1:
            # Confirmation before deleting
            if "confirm_delete" not in st.session_state:
                st.session_state.confirm_delete = True
                st.warning("Are you sure? Click again to delete.")
            else:
                del st.session_state.all_chats[active_chat_id]
                del st.session_state.confirm_delete
                st.session_state.active_chat_id = list(st.session_state.all_chats.keys())[0]
                st.toast("Chat deleted.")
                st.rerun()
        else:
            st.error("Cannot delete the last remaining chat.")
    else:
        # Reset confirmation state if user clicks elsewhere
        if "confirm_delete" in st.session_state:
            del st.session_state.confirm_delete


# --- 5. MAIN CHAT INTERFACE ---
st.title(f"💬 {st.session_state.all_chats[active_chat_id]['name']}")
st.markdown(f"**Assistant:** ScopeAI | **Knowledge Base:** {collection.count()} Résumés")

# Display chat history
chat_messages = st.session_state.all_chats[active_chat_id]["messages"]
for msg in chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Show sources if they exist in the message metadata
        if "sources" in msg and msg["sources"]:
            with st.expander("📚 Sources"):
                for source in msg["sources"]:
                    st.info(f"**Candidate:** {source.get('name', 'N/A')} (ID: {source.get('candidate_id', 'N/A')})")

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

# Handle user input
user_query = st.chat_input("Ask about candidates, skills, experience...")
if user_query:
    # Add user message to history and display it
    chat_messages.append({"role": "user", "content": user_query})
    st.chat_message("user").markdown(user_query)
    
    # Get and display assistant's response
    with st.chat_message("assistant"):
        with st.spinner("Searching résumés and thinking..."):
            response, sources = get_rag_response(user_query, chat_messages)
            st.markdown(response)
            
            # Display sources if any were used
            if sources:
                with st.expander("📚 Sources"):
                    for source in sources:
                        st.info(f"**Candidate:** {source.get('name', 'N/A')} (ID: {source.get('candidate_id', 'N/A')})")

    # Add assistant message to history
    chat_messages.append({"role": "assistant", "content": response, "sources": sources})