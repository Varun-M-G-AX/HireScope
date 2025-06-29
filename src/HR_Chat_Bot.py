import re
import streamlit as st
from datetime import datetime
from streamlit.components.v1 import html
from utils import collection, openai

# --- Page Configuration ---
st.set_page_config(
    page_title="💬 HireScope Chat",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
/* General styling */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* Sidebar styling */
section[data-testid="stSidebar"] > div {
    overflow-y: auto;
    max-height: 85vh;
    padding-top: 1rem;
}

/* Chat header */
.chat-header {
    background: linear-gradient(135deg, #667eea, #764ba2);
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    color: white;
}
.chat-header h2 {
    margin: 0;
    font-weight: 600;
    font-size: 1.5rem;
}

/* Chat messages */
.chat-message {
    padding: 0.75rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    max-width: 80%;
}
.user-message {
    background-color: #e1f5fe;
    align-self: flex-end;
}
.assistant-message {
    background-color: #f1f8e9;
    align-self: flex-start;
}

/* Chat title editing */
.chat-title-edit {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.chat-title-edit input {
    flex-grow: 1;
    padding: 0.5rem;
    border-radius: 8px;
    border: 1px solid #ddd;
}

/* Buttons */
.stButton > button {
    width: 100%;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    background: #667eea;
    color: white;
    border: none;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(0,0,0,0.1);
}

/* Enhanced Typing Indicator */
.typing-indicator-container {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: #f3f4f6;
    border-radius: 18px;
    width: fit-content;
    margin-left: 8px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.typing-indicator-text {
    font-weight: 500;
    color: #4b5563;
    font-size: 14px;
}
.typing-animation {
    display: flex;
    gap: 4px;
}
.typing-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #667eea;
    animation: typingAnimation 1.4s infinite ease-in-out;
}
.typing-dot:nth-child(1) {
    animation-delay: 0s;
}
.typing-dot:nth-child(2) {
    animation-delay: 0.2s;
}
.typing-dot:nth-child(3) {
    animation-delay: 0.4s;
}
@keyframes typingAnimation {
    0%, 60%, 100% {
        transform: translateY(0);
        opacity: 0.6;
    }
    30% {
        transform: translateY(-5px);
        opacity: 1;
    }
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 2rem;
    color: #666;
    font-style: italic;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .chat-header {
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .chat-header h2 {
        font-size: 1.2rem;
    }
}
</style>
""", unsafe_allow_html=True)

# --- Chat Context Prompt ---
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a recruiting assistant. "
        "Answer ONLY from résumé snippets provided in context. "
        "If the query is unrelated to candidates or résumés, say: "
        "'Sorry, I can only answer questions about candidates based on the résumé snippets provided.'"
    )
}

# --- Session Initialization ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}
if "active_chat" not in st.session_state:
    new_title = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
    st.session_state.active_chat = new_title
    st.session_state.all_chats[new_title] = [SYSTEM_PROMPT]
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {k: k for k in st.session_state.all_chats}
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "editing_title" not in st.session_state:
    st.session_state.editing_title = None

# --- Helper Functions ---
def show_typing_indicator():
    """Display enhanced typing indicator with smooth animation"""
    return """
    <div class="typing-indicator-container">
        <div class="typing-indicator-text">HireScope is thinking</div>
        <div class="typing-animation">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    </div>
    """

def generate_chat_title(messages):
    """Generate a descriptive title for the chat using AI"""
    try:
        # Get the first few user messages
        user_messages = [m["content"] for m in messages if m["role"] == "user"][:3]
        if not user_messages:
            return f"Chat - {datetime.now():%Y-%m-%d}"
        
        # Create prompt for title generation
        prompt = (
            "Generate a concise, descriptive title (3-5 words) for this chat conversation "
            "based on the following initial messages. The title should capture the main topic "
            "of discussion. Respond ONLY with the title, no other text.\n\n"
            "Messages:\n" + "\n".join(f"- {msg}" for msg in user_messages)
        )
        
        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=20
        )
        
        title = response.choices[0].message.content.strip()
        # Clean up the title
        title = re.sub(r'^["\']|["\']$', "", title)  # Remove surrounding quotes if any
        return title[:40]  # Truncate to 40 chars
        
    except Exception as e:
        st.error(f"Error generating chat title: {e}")
        return f"Chat - {datetime.now():%Y-%m-%d}"

def should_rename(chat_key):
    """Determine if a chat should be auto-renamed"""
    if not chat_key.startswith("New Chat"):
        return False
    chat = st.session_state.all_chats[chat_key]
    user_msgs = [m for m in chat if m["role"] == "user"]
    return len(user_msgs) >= 2  # Rename after at least 2 user messages

def truncate_title(title, max_length=30):
    """Truncate chat title for display"""
    if len(title) <= max_length:
        return title
    return title[:max_length-3] + "..."

# --- Sidebar: Chat Management ---
with st.sidebar:
    st.markdown("## 💬 Chat History")
    
    # New Chat Button
    if st.button("➕ Start New Chat", key="new_chat"):
        new_name = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
        st.session_state.all_chats[new_name] = [SYSTEM_PROMPT]
        st.session_state.chat_titles[new_name] = new_name
        st.session_state.active_chat = new_name
        st.session_state.is_generating = False
        st.session_state.editing_title = None
        st.experimental_rerun()
    
    # Chat List
    if st.session_state.all_chats:
        st.markdown("---")
        sorted_chats = sorted(st.session_state.all_chats.keys(), reverse=True)
        
        for name in sorted_chats:
            title = st.session_state.chat_titles.get(name, name)
            display_title = truncate_title(title)
            
            if name == st.session_state.active_chat:
                st.markdown(f"**🔵 {display_title}**")
            else:
                if st.button(display_title, key=f"select_{name}"):
                    st.session_state.active_chat = name
                    st.session_state.is_generating = False
                    st.session_state.editing_title = None
                    st.experimental_rerun()
    
    # Delete Chat Button
    if len(st.session_state.all_chats) > 1:
        st.markdown("---")
        if st.button("🗑️ Delete Current Chat", key="delete_chat"):
            if st.session_state.active_chat in st.session_state.all_chats:
                del st.session_state.chat_titles[st.session_state.active_chart]
                del st.session_state.all_chats[st.session_state.active_chat]
                st.session_state.active_chat = list(st.session_state.all_chats.keys())[0]
                st.session_state.is_generating = False
                st.session_state.editing_title = None
                st.experimental_rerun()
    
    # Statistics
    st.markdown("---")
    st.markdown(f"**Total Chats:** {len(st.session_state.all_chats)}")
    current_chat = st.session_state.all_chats.get(st.session_state.active_chat, [])
    message_count = len([m for m in current_chat if m["role"] != "system"])
    st.markdown(f"**Messages in Chat:** {message_count}")

# --- Main Chat Interface ---
chat_key = st.session_state.active_chat
chat = st.session_state.all_chats.get(chat_key, [SYSTEM_PROMPT])
title = st.session_state.chat_titles.get(chat_key, chat_key)

# Chat Header with Title Editing
with st.container():
    st.markdown(f"""
    <div class="chat-header">
        <h2>💼 {title}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Title editing interface
    if st.session_state.editing_title == chat_key:
        new_title = st.text_input(
            "Edit chat title:", 
            value=title,
            key="title_edit_input",
            label_visibility="collapsed"
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Save"):
                st.session_state.chat_titles[chat_key] = new_title
                st.session_state.editing_title = None
                st.experimental_rerun()
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.editing_title = None
                st.experimental_rerun()
    else:
        if st.button("✏️ Rename Chat", key="rename_chat"):
            st.session_state.editing_title = chat_key
            st.experimental_rerun()

# Display Chat Messages
message_container = st.container()
with message_container:
    if len(chat) <= 1:
        st.markdown("""
        <div class="empty-state">
            <h3>👋 Welcome to HireScope Chat!</h3>
            <p>Ask me anything about the candidates in your database.</p>
            <p><em>Example: "Show me candidates with Python experience" or "Who has the most relevant experience for a senior developer role?"</em></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in chat[1:]:
            with st.container():
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-message user-message">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)

# Show typing indicator if generating
if st.session_state.is_generating:
    with st.chat_message("assistant"):
        st.markdown(show_typing_indicator(), unsafe_allow_html=True)

# Chat Input
query = st.chat_input("💬 Ask about candidates...", disabled=st.session_state.is_generating)

# --- Handle User Query ---
if query and not st.session_state.is_generating:
    st.session_state.is_generating = True
    
    # Add user message
    chat.append({"role": "user", "content": query})
    
    # Show user message immediately
    with st.container():
        st.markdown(f'<div class="chat-message user-message">{query}</div>', unsafe_allow_html=True)
    
    # Show typing indicator
    typing_placeholder = st.empty()
    with typing_placeholder:
        st.markdown(show_typing_indicator(), unsafe_allow_html=True)
    
    # Process query
    try:
        if is_greeting(query):
            reply = "Hello! I'm here to help you find information about candidates. How can I assist you today?"
        else:
            # Check if we have any documents
            try:
                total = collection.count()
            except Exception as e:
                st.error(f"Database connection error: {e}")
                total = 0
            
            if total == 0:
                reply = "I don't have any résumé data available right now. Please make sure the candidate database is properly loaded."
            else:
                # Check if query is recruitment-related
                relevant = is_recruitment_query(query)
                
                # Search for relevant documents
                try:
                    hits = collection.query(
                        query_texts=[query], 
                        n_results=max(1, min(5, total))
                    )
                    docs = hits.get("documents", [[]])[0]
                except Exception as e:
                    st.error(f"Search error: {e}")
                    docs = []
                
                # If we found documents, consider it relevant
                if docs and any(d.strip() for d in docs):
                    relevant = True
                
                if not relevant:
                    reply = "Sorry, I can only answer questions about candidates based on the résumé snippets provided. Please ask about candidate qualifications, experience, or skills."
                elif not docs or all(not d.strip() for d in docs):
                    reply = "I couldn't find any résumé information that matches your query. Try rephrasing your question or asking about different qualifications."
                else:
                    # Generate response using found documents
                    context = "\n\n---\n\n".join(docs)
                    chat[0]["content"] = f"Answer ONLY from these résumé snippets:\n\n{context}"
                    
                    try:
                        resp = openai.chat.completions.create(
                            model="gpt-4o",
                            messages=chat,
                            temperature=0.3,
                            max_tokens=1000
                        )
                        reply = resp.choices[0].message.content.strip()
                    except Exception as e:
                        reply = f"I'm having trouble generating a response right now. Please try again. Error: {str(e)}"
        
        # Add assistant response
        chat.append({"role": "assistant", "content": reply})
        
        # Auto-rename chat if needed
        if should_rename(chat_key):
            new_title = generate_chat_title(chat)
            st.session_state.chat_titles[chat_key] = new_title
        
        # Clear typing indicator and show response
        typing_placeholder.empty()
        with st.container():
            st.markdown(f'<div class="chat-message assistant-message">{reply}</div>', unsafe_allow_html=True)
        
    except Exception as e:
        typing_placeholder.empty()
        error_msg = f"An unexpected error occurred: {str(e)}"
        chat.append({"role": "assistant", "content": error_msg})
        st.error(error_msg)
    
    finally:
        st.session_state.is_generating = False
        st.experimental_rerun()

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em; padding: 1rem;">
    <p>🤖 <strong>HireScope Chat</strong> - AI-powered candidate search and analysis</p>
    <p><em>Ask questions about candidates, skills, experience, and qualifications</em></p>
</div>
""", unsafe_allow_html=True)