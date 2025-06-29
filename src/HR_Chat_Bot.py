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
    /* Global Styles */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Sidebar Styling */
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        overflow-y: auto;
        max-height: 85vh;
        padding: 1rem 0;
    }
    
    /* Chat Header */
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .chat-header h2 {
        color: white;
        margin: 0;
        font-weight: 600;
        font-size: 1.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Chat Messages */
    .stChatMessage {
        margin-bottom: 1rem;
    }
    
    /* Button Styling */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* New Chat Button */
    .new-chat-btn button {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
        font-weight: 600;
    }
    
    /* Delete Button */
    .delete-btn button {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        margin-top: 1rem;
    }
    
    /* Chat Selection Buttons */
    .chat-btn button {
        background: white;
        color: #333;
        border: 2px solid #e0e0e0;
        margin-bottom: 0.5rem;
        text-align: left;
        font-size: 0.9rem;
    }
    
    .chat-btn button:hover {
        border-color: #667eea;
        background: #f8f9ff;
    }
    
    /* Typing Animation */
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .typing-dots {
        display: flex;
        gap: 4px;
        margin-left: 0.5rem;
    }
    
    .typing-dots span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
    .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
    .typing-dots span:nth-child(3) { animation-delay: 0s; }
    
    @keyframes typing {
        0%, 80%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        40% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    /* Error Message */
    .error-message {
        background: #fee;
        border: 1px solid #fcc;
        border-radius: 8px;
        padding: 1rem;
        color: #c33;
        margin: 1rem 0;
    }
    
    /* Success Message */
    .success-message {
        background: #efe;
        border: 1px solid #cfc;
        border-radius: 8px;
        padding: 1rem;
        color: #3c3;
        margin: 1rem 0;
    }
    
    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 2rem;
        color: #666;
        font-style: italic;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem;
        }
        
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

# --- Helper Functions ---
def should_rename(chat_key):
    """Determine if a chat should be auto-renamed based on content"""
    if not chat_key.startswith("New Chat"):
        return False
    if len(st.session_state.all_chats) < 3:
        return False
    chat = st.session_state.all_chats[chat_key]
    user_msgs = [m for m in chat if m["role"] == "user"]
    if len(user_msgs) < 2:
        return False
    first = user_msgs[0]["content"].strip()
    return len(first) > 12 and not re.match(r"^(hi|hello|hey|thanks)", first, re.I)

def rename_chat(chat_key):
    """Auto-rename chat based on first meaningful message"""
    user_msgs = [m for m in st.session_state.all_chats[chat_key] if m["role"] == "user"]
    if user_msgs:
        first = user_msgs[0]["content"].strip().split("\n")[0]
        new_title = re.sub(r"[^\w\s]", "", first)[:40].strip().title()
        if new_title and len(new_title) > 3:
            st.session_state.chat_titles[chat_key] = new_title

def is_greeting(text):
    """Check if message is a simple greeting"""
    return bool(re.fullmatch(r"(hi|hello|hey|thanks|thank you|good (morning|afternoon|evening))[!. ]*", text.strip(), re.I))

def is_recruitment_query(query):
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
        st.error(f"Error checking query relevance: {e}")
        return False

def show_typing_indicator():
    """Display animated typing indicator"""
    return st.markdown("""
    <div class="typing-indicator">
        <span style="color: #667eea; font-weight: 600;">🤖 AI is thinking</span>
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def truncate_title(title, max_length=30):
    """Truncate chat title for display"""
    if len(title) <= max_length:
        return title
    return title[:max_length-3] + "..."

# --- Sidebar: Chat Management ---
with st.sidebar:
    st.markdown("## 💬 Chat History")
    
    # New Chat Button
    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("➕ Start New Chat", key="new_chat"):
        new_name = f"New Chat - {datetime.now():%Y-%m-%d %H:%M}"
        st.session_state.all_chats[new_name] = [SYSTEM_PROMPT]
        st.session_state.chat_titles[new_name] = new_name
        st.session_state.active_chat = new_name
        st.session_state.is_generating = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat List
    if st.session_state.all_chats:
        st.markdown("---")
        sorted_chats = sorted(st.session_state.all_chats.keys(), reverse=True)
        
        for name in sorted_chats:
            title = st.session_state.chat_titles.get(name, name)
            display_title = truncate_title(title)
            
            # Highlight active chat
            if name == st.session_state.active_chat:
                st.markdown(f"**🔵 {display_title}**")
            else:
                st.markdown('<div class="chat-btn">', unsafe_allow_html=True)
                if st.button(display_title, key=f"select_{name}"):
                    st.session_state.active_chat = name
                    st.session_state.is_generating = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Delete Chat Button
    if len(st.session_state.all_chats) > 1:
        st.markdown("---")
        st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Delete Current Chat", key="delete_chat"):
            if st.session_state.active_chat in st.session_state.all_chats:
                del st.session_state.chat_titles[st.session_state.active_chat]
                del st.session_state.all_chats[st.session_state.active_chat]
                st.session_state.active_chat = list(st.session_state.all_chats.keys())[0]
                st.session_state.is_generating = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Statistics
    st.markdown("---")
    st.markdown("### 📊 Statistics")
    st.markdown(f"**Total Chats:** {len(st.session_state.all_chats)}")
    
    current_chat = st.session_state.all_chats.get(st.session_state.active_chat, [])
    message_count = len([m for m in current_chat if m["role"] != "system"])
    st.markdown(f"**Messages in Chat:** {message_count}")

# --- Main Chat Interface ---
chat_key = st.session_state.active_chat
chat = st.session_state.all_chats.get(chat_key, [SYSTEM_PROMPT])
title = st.session_state.chat_titles.get(chat_key, chat_key)

# Chat Header
st.markdown(f"""
<div class="chat-header">
    <h2>💼 {title}</h2>
</div>
""", unsafe_allow_html=True)

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
        for msg in chat[1:]:  # Skip system message
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

# Show typing indicator if generating
if st.session_state.is_generating:
    with st.chat_message("assistant"):
        show_typing_indicator()

# Chat Input
query = st.chat_input("💬 Ask about candidates...", disabled=st.session_state.is_generating)

# --- Handle User Query ---
if query and not st.session_state.is_generating:
    st.session_state.is_generating = True
    
    # Add user message
    chat.append({"role": "user", "content": query})
    
    # Auto-rename chat if needed
    if should_rename(chat_key):
        rename_chat(chat_key)
    
    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(query)
    
    # Show typing indicator
    with st.chat_message("assistant"):
        typing_placeholder = st.empty()
        with typing_placeholder:
            show_typing_indicator()
    
    # Process query
    try:
        if is_greeting(query):
            reply = "Hello! 👋 I'm here to help you find information about candidates. How can I assist you today?"
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
                        reply = f"⚠️ I'm having trouble generating a response right now. Please try again. Error: {str(e)}"
        
        # Add assistant response
        chat.append({"role": "assistant", "content": reply})
        
        # Clear typing indicator and show response
        typing_placeholder.empty()
        st.markdown(reply)
        
    except Exception as e:
        typing_placeholder.empty()
        error_msg = f"⚠️ An unexpected error occurred: {str(e)}"
        chat.append({"role": "assistant", "content": error_msg})
        st.error(error_msg)
    
    finally:
        st.session_state.is_generating = False
        st.rerun()

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em; padding: 1rem;">
    <p>🤖 <strong>HireScope Chat</strong> - AI-powered candidate search and analysis</p>
    <p><em>Ask questions about candidates, skills, experience, and qualifications</em></p>
</div>
""", unsafe_allow_html=True)