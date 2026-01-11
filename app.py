import streamlit as st
import requests
import json
import re
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide"  # Changed to wide for better sidebar
)

# Custom CSS for better styling
st.markdown("""
    <style>
    /* Main background */
    .main {
        background-color: #f0f2f6;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1e1e1e;
        width: 280px !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* All chat messages - force white background and black text */
    div[data-testid="stChatMessage"] {
        background-color: white !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin: 10px 0 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }
    
    /* Force black text everywhere in chat */
    div[data-testid="stChatMessage"],
    div[data-testid="stChatMessage"] *,
    div[data-testid="stChatMessage"] p,
    div[data-testid="stChatMessage"] div,
    div[data-testid="stChatMessage"] span {
        color: #000000 !important;
    }
    
    /* User message - gray background */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background-color: #e8e8e8 !important;
        border-left: 4px solid #9e9e9e !important;
    }
    
    /* Assistant message - lighter gray background */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background-color: #f5f5f5 !important;
        border-left: 4px solid #bdbdbd !important;
    }
    
    /* Chat history item styling */
    .chat-history-item {
        padding: 10px;
        margin: 5px 0;
        border-radius: 8px;
        cursor: pointer;
        background-color: #2a2a2a;
        transition: background-color 0.2s;
    }
    
    .chat-history-item:hover {
        background-color: #3a3a3a;
    }
    
    .chat-history-item.active {
        background-color: #4a4a4a;
        border-left: 3px solid #2196F3;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {
        "chat_1": {
            "title": "New Chat",
            "messages": [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    }

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "chat_1"

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Sidebar for chat history
with st.sidebar:
    st.markdown("### 💬 Chat History")
    st.markdown("---")
    
    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True):
        new_chat_id = f"chat_{len(st.session_state.chat_sessions) + 1}"
        st.session_state.chat_sessions[new_chat_id] = {
            "title": "New Chat",
            "messages": [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        st.session_state.current_chat_id = new_chat_id
        st.rerun()
    
    st.markdown("---")
    
    # Display chat history
    for chat_id, chat_data in st.session_state.chat_sessions.items():
        # Get first message as title or use default
        if chat_data["messages"]:
            title = chat_data["messages"][0]["content"][:30] + "..." if len(chat_data["messages"][0]["content"]) > 30 else chat_data["messages"][0]["content"]
        else:
            title = chat_data["title"]
        
        # Chat history button
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(
                f"💭 {title}",
                key=f"chat_{chat_id}",
                use_container_width=True,
                type="primary" if chat_id == st.session_state.current_chat_id else "secondary"
            ):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        
        with col2:
            if st.button("🗑️", key=f"delete_{chat_id}", help="Delete chat"):
                if len(st.session_state.chat_sessions) > 1:
                    del st.session_state.chat_sessions[chat_id]
                    # Set current chat to first available
                    st.session_state.current_chat_id = list(st.session_state.chat_sessions.keys())[0]
                    st.rerun()
    
    st.markdown("---")
    
    # API Key input
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input(
        "OpenRouter API Key",
        value=st.session_state.api_key,
        type="password",
        help="Enter your OpenRouter API key"
    )
    if api_key:
        st.session_state.api_key = api_key
    
    st.markdown("---")
    st.markdown("### 📝 How to Use")
    st.markdown("""
    1. Enter API Key above
    2. Type your message
    3. Press Enter to send
    4. Create new chats anytime!
    """)
    
    st.markdown("---")
    st.markdown("[Get API Key](https://openrouter.ai/)")

# Get current chat messages
current_chat = st.session_state.chat_sessions[st.session_state.current_chat_id]
messages = current_chat["messages"]

# Main chat area
st.title("🤖 AI Chatbot Assistant")
st.markdown("*Chat with AI using OpenRouter API*")
st.markdown("---")

# Display chat history
for message in messages:
    avatar = "👨‍💼" if message["role"] == "user" else "🔮"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Function to call OpenRouter API
def get_ai_response(user_message, api_key, messages):
    """
    Mengirim pesan ke OpenRouter API dan mendapatkan respons
    """
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare conversation history for context
        conversation_history = [
            {"role": "system", "content": "Kamu adalah asisten AI yang ramah dan membantu. Jawab dalam bahasa Indonesia dengan sopan dan informatif."}
        ]
        
        # Add previous messages for context (limit to last 10 messages)
        for msg in messages[-10:]:
            conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        data = {
            "model": "mistralai/mistral-7b-instruct",
            "messages": conversation_history,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            # Clean unwanted markdown/HTML tags and instruction tokens
            ai_response = re.sub(r'\[/?s\]', '', ai_response)  # Remove [s] and [/s]
            ai_response = re.sub(r'\[/?strike\]', '', ai_response)  # Remove [strike] tags
            ai_response = re.sub(r'<<>>|<</>>|<<s>>|<</s>>', '', ai_response)  # Remove << >> variants
            ai_response = re.sub(r'<<?s?>?>|<<?/s?>?>', '', ai_response)  # Remove other variants
            ai_response = re.sub(r'\[/?INST\]', '', ai_response)  # Remove [INST] and [/INST]
            ai_response = re.sub(r'\[/?SYS\]', '', ai_response)  # Remove [SYS] tags
            ai_response = ai_response.strip()  # Remove extra whitespace
            return ai_response
        elif response.status_code == 402:
            return "⚠️ **Error 402: Insufficient Credits**\n\nAPI key Anda kehabisan credit. Silakan:\n1. Top up credit di [OpenRouter](https://openrouter.ai/settings/credits)\n2. Atau gunakan API key yang baru"
        elif response.status_code == 401:
            return "⚠️ **Error 401: Invalid API Key**\n\nAPI key tidak valid. Silakan periksa kembali API key Anda."
        else:
            return f"⚠️ **Error {response.status_code}**\n\n{response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return "⚠️ Request timeout. API membutuhkan waktu terlalu lama untuk merespons."
    except requests.exceptions.ConnectionError:
        return "⚠️ Tidak dapat terhubung ke API. Periksa koneksi internet Anda."
    except Exception as e:
        return f"⚠️ Terjadi kesalahan: {str(e)}"

# Chat input
if prompt := st.chat_input("Ketik pesan Anda di sini..."):
    # Check if API key is provided
    if not st.session_state.api_key:
        st.error("⚠️ Silakan masukkan API Key terlebih dahulu di sidebar!")
    else:
        # Add user message to current chat
        messages.append({"role": "user", "content": prompt})
        st.session_state.chat_sessions[st.session_state.current_chat_id]["messages"] = messages
        
        # Display user message
        with st.chat_message("user", avatar="👨‍💼"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant", avatar="🔮"):
            message_placeholder = st.empty()
            with st.spinner("AI sedang berpikir..."):
                response = get_ai_response(prompt, st.session_state.api_key, messages)
                
                # Check if response is empty or error
                if not response or response.strip() == "":
                    response = "⚠️ Maaf, saya tidak dapat memberikan respons. Silakan coba lagi."
                
                message_placeholder.markdown(response)
        
        # Add assistant response to current chat
        messages.append({"role": "assistant", "content": response})
        st.session_state.chat_sessions[st.session_state.current_chat_id]["messages"] = messages

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Made by Gjustine</div>",
    unsafe_allow_html=True
)
