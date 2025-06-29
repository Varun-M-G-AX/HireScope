import re
import streamlit as st
from datetime import datetime
import time
from typing import Dict, List, Any

# Mock OpenAI and database collection imports
# Replace these with your actual imports
try:
    from openai import OpenAI
    from utils import collection  # Your database collection utility
except ImportError:
    # Mock implementations just to make the code runnable
    class MockOpenAI:
        class chat:
            class completions:
                def create(**kwargs):
                    return type('obj', (object,), {
                        'choices': [type('obj', (object,), {
                            'message': type('obj', (object,), {
                                'content': "Mock response - replace with your OpenAI implementation"
                            })
                        })]
                    })
    openai = MockOpenAI()
    collection = type('obj', (object,), {
        'count': lambda: 5,
        'query': lambda **kwargs: {'documents': [["Resume snippet 1", "Resume snippet 2"]]}
    })

# --- Page Configuration ---
st.set_page_config(
    page_title="HireScope Chat",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS.GG Icons Setup ---
GG_CSS = """
<link href='https://css.gg/css' rel='stylesheet'>
<style>
/* Dark/Light Mode Variables */
:root {
    --primary-bg: #ffffff;
    --secondary-bg: #f5f7fa;
    --text-color: #1a1a1a;
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --message-user-bg: #e1f5fe;
    --message-assistant-bg: #f1f8e9;
    --border-color: #e1e4e8;
    --shadow-color: rgba(0,0,0,0.1);
}

@media (prefers-color-scheme: dark) {
    :root {
        --primary-bg: #1e1e1e;
        --secondary-bg: #2d2d2d;
        --text-color: #f0f0f0;
        --primary-color: #7c93ff;
        --secondary-color: #9a6bff;
        --message-user-bg: #2a3a45;
        --message-assistant-bg: #2a3d35;
        --border-color: #3a3a3a;
        --shadow-color: rgba(0,0,0,0.3);
    }
}

/* Base Styles */
body {
    background-color: var(--primary-bg);
    color: var(--text-color);
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    margin: 0;
    padding: 0;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: var(--secondary-bg);
    border-right: 1px solid var(--border-color);
}

/* Header Styling */
.chat-header {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    padding: 1.25rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 15px var(--shadow-color);
    color: white;
}

.chat-header h2 {
    margin: 0;
    font-weight: 600;
    font-size: 1.35rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Message Styling */
.chat-message {
    padding: 0.75rem 1rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    max-width: 85%;
    position: relative;
    transition: all 0.2s ease;
}

.user-message {
    background-color: var(--message-user-bg);
    margin-left: auto;
    border-top-right-radius: 4px;
}

.assistant-message {
    background-color: var(--message-assistant-bg);
    margin-right: auto;
    border-top-left-radius: 4px;
}

.message-timestamp {
    font-size: 0.65rem;
    opacity: 0.7;
    margin-top: 0.25rem;
    text-align: right;
}

/* Typing Indicator */
.typing-indicator-container {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--secondary-bg);
    border-radius: 18px;
    width: fit-content;
    margin-left: 0.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px var(--shadow-color);
    font-size: 0.85rem;
}

.typing-animation {
    display: flex;
    gap: 0.35rem;
}

.typing-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--primary-color);
    animation: typingAnimation 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) { animation-delay: 0s; }
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingAnimation {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
    30% { transform: translateY(-4px); opacity: 1; }
}

/* Button Styling */
.stButton > button {
    width: 100%;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    background: var(--primary-color);
    color: white;
    border: none;
    transition: all 0.25s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px var(--shadow-color);
}

.secondary-btn > button {
    background: var(--secondary-bg);
    color: var(--text-color);
    border: 1px solid var(--border-color);
}

.secondary-btn > button:hover {
    background: var(--secondary-bg);
    border-color: var(--primary-color);
}

.delete-btn > button {
    background: #ff4b4b !important;
}

/* Chat List Styling */
.chat-item {
    padding: 0.5rem;
    border-radius: 8px;
    margin-bottom: 0.35rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.chat-item:hover {
    background: rgba(102, 126, 234, 0.1);
}

.chat-item.active {
    background: rgba(102, 126, 234, 0.2);
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 2rem;
    color: var(--text-color);
    opacity: 0.7;
    font-style: italic;
}

/* Footer */
.footer {
    text-align: center;
    color: var(--text-color);
    font-size: 0.85rem;
    padding: 1rem;
    opacity: 0.8;
}

/* General Utility Classes */
.flex {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.mb-1 { margin-bottom: 1rem; }
.mt-1 { margin-top: 1rem; }
.badge {
    font-size: 0.7rem;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    background: var(--secondary-bg);
    color: var(--text-color);
}
</style>
"""

# Inject CSS into app
st.markdown(GG_CSS, unsafe_allow_html=True)

# --- Chat Context Prompt ---
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a recruiting assistant. Answer ONLY from résumé snippets provided in context. "
        "If the query is unrelated to candidates or résumés, say: "
        "'Sorry, I can only answer questions about candidates based on the résumé snippets provided.'"
    )
}

# Initialize session state
def initialize_session_state():
    if "all_chats" not in st.session_state:
        st.session_state.all_chats = {}
    if "active_chat" not in st.session_state:
        new_title = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        st.session_state.active_chat = new_title
        st.session_state.all_chats[new_title] = [SYSTEM_PROMPT]
    if "chat_titles" not in st.session_state:
        st.session_state.chat_titles = {k: k for k in st.session_state.all_chats}
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False
    if "editing_title" not in st.session_state:
        st.session_state.editing_title = None
    if "show_delete_confirm" not in st.session_state:
        st.session_state.show_delete_confirm = False

initialize_session_state()

# --- Helper Functions ---
def show_typing_indicator():
    """Display enhanced typing indicator with smooth animation"""
    return """
    <div class="typing-indicator-container">
        <span>HireScope AI is thinking</span>
        <div class="typing-animation">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    </div>
    """

def format_message_timestamp():
    """Return formatted timestamp for messages"""
    return f'<div class="message-timestamp">{datetime.now().strftime("%H:%M")}</div>'

def generate_chat_title(messages: List[Dict[str, str]]) -> str:
    """Generate a descriptive title for the chat using AI"""
    try:
        user_messages = [m["content"] for m in messages if m["role"] == "user"][:3]
        if not user_messages:
            return f"Chat - {datetime.now().strftime('%Y-%m-%d')}"
        
        prompt = (
            "Generate a concise title (3-5 words) for this conversation.\n"
            "Focus on the main topic being discussed.\n"
            "Messages:\n" + "\n".join(f"- {msg[:100]}" for msg in user_messages)
        )
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=20
        )
        
        title = response.choices[0].message.content.strip()
        title = re.sub(r'^["\']|["\']$', "", title)
        return title[:40]
    except Exception as e:
        st.error(f"Error generating chat title: {str(e)}")
        return f"Chat - {datetime.now().strftime('%Y-%m-%d')}"

def should_rename(chat_key: str) -> bool:
    """Determine if a chat should be auto-renamed"""
    if not chat_key.startswith("New Chat"):
        return False
    chat = st.session_state.all_chats[chat_key]
    user_msgs = [m for m in chat if m["role"] == "user"]
    return len(user_msgs) >= 2

def truncate_title(title: str, max_length: int = 28) -> str:
    """Truncate chat title for display"""
    return title if len(title) <= max_length else f"{title[:max_length-3]}..."

def is_greeting(text: str) -> bool:
    """Check if message is a simple greeting"""
    return bool(re.fullmatch(
        r"(hi|hello|hey|thanks|thank you|good (morning|afternoon|evening))[!. ]*", 
        text.strip(), 
        re.I
    ))

def is_recruitment_query(query: str) -> bool:
    """Use AI to determine if query is recruitment-related"""
    prompt = (
        "Respond ONLY with 'Yes' or 'No'. Does this query relate to candidates, "
        "resumes, recruiting, jobs, hiring, or HR?\n"
        f"Query: \"{query}\""
    )
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        return resp.choices[0].message.content.strip().lower().startswith("yes")
    except Exception as e:
        st.error(f"Error checking query relevance: {str(e)}")
        return False

# --- Sidebar: Chat Management ---
with st.sidebar:
    st.markdown("""
    <div class="flex">
        <i class="gg-bot"></i>
        <h3>HireScope Chat</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # New Chat Button
    if st.button("➕ New Chat", key="new_chat", use_container_width=True):
        new_title = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        st.session_state.all_chats[new_title] = [SYSTEM_PROMPT]
        st.session_state.chat_titles[new_title] = new_title
        st.session_state.active_chat = new_title
        st.session_state.is_generating = False
        st.session_state.editing_title = None
        st.session_state.show_delete_confirm = False
        st.rerun()
    
    st.markdown("---")
    
    # Chat List
    if st.session_state.all_chats:
        sorted_chats = sorted(st.session_state.all_chats.keys(), reverse=True)
        
        for name in sorted_chats:
            title = st.session_state.chat_titles.get(name, name)
            display_title = truncate_title(title)
            active = name == st.session_state.active_chat
            
            if active:
                st.markdown(f"**{display_title}**")
            else:
                if st.button(
                    display_title, 
                    key=f"select_{name}",
                    use_container_width=True
                ):
                    st.session_state.active_chat = name
                    st.session_state.is_generating = False
                    st.session_state.editing_title = None
                    st.rerun()
    
    st.markdown("---")
    
    # Delete Current Chat Button
    if len(st.session_state.all_chats) > 1:
        if st.button("🗑️ Delete Current Chat", key="delete_chat", use_container_width=True):
            st.session_state.show_delete_confirm = True
        
        if st.session_state.show_delete_confirm:
            st.warning("Are you sure you want to delete this chat?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes", use_container_width=True):
                    name = st.session_state.active_chat
                    if name in st.session_state.all_chats:
                        del st.session_state.chat_titles[name]
                        del st.session_state.all_chats[name]
                        st.session_state.active_chat = next(iter(st.session_state.all_chats.keys()))
                        st.session_state.is_generating = False
                        st.session_state.editing_title = None
                        st.session_state.show_delete_confirm = False
                        st.rerun()
            with col2:
                if st.button("❌ No", use_container_width=True):
                    st.session_state.show_delete_confirm = False
                    st.rerun()
    
    st.markdown("---")
    
    # Statistics
    st.markdown(f"""
    <div class="flex">
        <i class="gg-list"></i>
        <span>Total Chats: <span class="badge">{len(st.session_state.all_chats)}</span></span>
    </div>
    """, unsafe_allow_html=True)
    
    current_chat = st.session_state.all_chats.get(st.session_state.active_chat, [])
    message_count = len([m for m in current_chat if m["role"] != "system"])
    st.markdown(f"""
    <div class="flex">
        <i class="gg-comment"></i>
        <span>Messages: <span class="badge">{message_count}</span></span>
    </div>
    """, unsafe_allow_html=True)

# --- Main Chat Interface ---
chat_key = st.session_state.active_chat
chat = st.session_state.all_chats.get(chat_key, [SYSTEM_PROMPT])
title = st.session_state.chat_titles.get(chat_key, chat_key)

# Chat Header with Title Editing
col1, col2 = st.columns([0.9, 0.1])
with col1:
    st.markdown(f"""
    <div class="chat-header">
        <h2>
            <i class="gg-briefcase"></i>
            {title}
        </h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if st.button("✏️", help="Rename chat"):
        st.session_state.editing_title = chat_key
        st.rerun()

# Title editing interface
if st.session_state.editing_title == chat_key:
    new_title = st.text_input(
        "Edit chat title:", 
        value=title,
        key="title_edit_input",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Save", use_container_width=True):
            st.session_state.chat_titles[chat_key] = new_title
            st.session_state.editing_title = None
            st.rerun()
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.editing_title = None
            st.rerun()

# Display Chat Messages
message_container = st.container()
with message_container:
    if len(chat) <= 1:
        st.markdown("""
        <div class="empty-state">
            <h3><i class="gg-smile"></i> Welcome to HireScope Chat!</h3>
            <p>Ask me anything about the candidates in your database.</p>
            <p><em>Example: "Show me candidates with Python experience" or "Find senior developers with React skills"</em></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in chat[1:]:
            role_class = "user-message" if msg["role"] == "user" else "assistant-message"
            icon = "<i class='gg-user'></i>" if msg["role"] == "user" else "<i class='gg-bot'></i>"
            sender = "You" if msg["role"] == "user" else "HireScope AI"
            
            st.markdown(
                f"""
                <div class="chat-message {role_class}">
                    <div class="flex">
                        {icon}
                        <span style="font-weight:500;">{sender}</span>
                    </div>
                    <div>{msg["content"]}</div>
                    {format_message_timestamp()}
                </div>
                """,
                unsafe_allow_html=True
            )

# Show typing indicator if generating
if st.session_state.is_generating:
    with st.chat_message("assistant"):
        st.markdown(show_typing_indicator(), unsafe_allow_html=True)

# Chat Input
query = st.chat_input("Ask about candidates...", disabled=st.session_state.is_generating)

# --- Handle User Query ---
if query and not st.session_state.is_generating:
    st.session_state.is_generating = True
    
    # Add user message
    chat.append({"role": "user", "content": query})
    
    # Show typing indicator
    typing_placeholder = st.empty()
    with typing_placeholder:
        st.markdown(show_typing_indicator(), unsafe_allow_html=True)
    
    # Process query
    try:
        if is_greeting(query):
            reply = "Hello! I'm here to help you find information about candidates. How can I assist you today?"
        else:
            if not is_recruitment_query(query):
                reply = "Sorry, I can only answer questions about candidates based on the résumé snippets provided."
            else:
                try:
                    # Check if we have any documents
                    total_docs = collection.count()
                    if total_docs == 0:
                        reply = "I don't have any résumé data available right now."
                    else:
                        # Search for relevant documents
                        hits = collection.query(
                            query_texts=[query],
                            n_results=min(5, total_docs)
                        )
                        docs = hits.get("documents", [[]])[0]
                        
                        if not docs or all(not d.strip() for d in docs):
                            reply = "No matching résumé information found. Try rephrasing your question."
                        else:
                            # Generate response using found documents
                            context = "\n\n---\n\n".join(docs)
                            chat[0]["content"] = f"Answer ONLY from:\n\n{context}"
                            
                            response = openai.chat.completions.create(
                                model="gpt-4",
                                messages=chat,
                                temperature=0.3,
                                max_tokens=1000
                            )
                            reply = response.choices[0].message.content.strip()
                except Exception as e:
                    reply = f"⚠️ Error processing your request: {str(e)}"
        
        # Add assistant response
        chat.append({"role": "assistant", "content": reply})
        
        # Auto-rename chat if needed
        if should_rename(chat_key):
            new_title = generate_chat_title(chat)
            st.session_state.chat_titles[chat_key] = new_title
        
        # Rerun to update the display
        st.rerun()
        
    except Exception as e:
        chat.append({"role": "assistant", "content": f"An error occurred: {str(e)}"})
        st.error(f"An error occurred: {str(e)}")
    finally:
        st.session_state.is_generating = False
        st.rerun()

# --- Footer ---
st.markdown("---")
st.markdown("""
<div class="footer">
    <div class="flex" style="justify-content: center; gap: 0.75rem;">
        <i class="gg-terminal"></i>
        <span>HireScope AI - Candidate Search Assistant</span>
    </div>
</div>
""", unsafe_allow_html=True)