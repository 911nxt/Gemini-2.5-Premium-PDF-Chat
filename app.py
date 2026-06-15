import streamlit as st
import os
import time
from google import genai
from google.genai import types

# ==========================================
# 1. PAGE CONFIGURATION & METADATA
# ==========================================
st.set_page_config(
    page_title="Abdulrahman Alnammoura | Premium Gemini RAG PDF Chat",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CUSTOM CSS STYLING (Premium Dark Theme Override)
# ==========================================
st.markdown("""
<style>
    /* Import Premium Plus Jakarta Sans Font */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Header Gradient Text Styling */
    .title-text {
        background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
    }
    
    .subtitle-text {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Strict CSS Styling for Dark Mode Metric Cards */
    .metric-card {
        background: #1e293b;
        color: #ffffff;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #475569;
    }
    
    /* Force high-contrast legibility for inputs and sidebar components */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }
    
    .stTextInput>div>div>input {
        color: #ffffff !important;
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }
    
    .stSelectbox>div>div>div {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "last_uploaded_name" not in st.session_state:
    st.session_state["last_uploaded_name"] = None

# ==========================================
# 4. SIDEBAR CONFIGURATION
# ==========================================
model_name = "gemini-2.5-flash"

with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # Retrieve default API Key from environment variables
    default_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
    
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=default_key,
        placeholder="AIzaSy...",
        help="Your Google AI Studio Gemini API Key."
    )
    
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        help="Lower values produce more factual and precise answers."
    )
    
    st.markdown("---")
    st.markdown("### 📁 Document Ingestion")
    
    uploaded_file = st.file_uploader(
        "Upload PDF Document",
        type=["pdf"],
        help="Upload a PDF document to chat with natively."
    )
    
    if uploaded_file and st.session_state["last_uploaded_name"] != uploaded_file.name:
        st.session_state["chat_history"] = []
        st.session_state["last_uploaded_name"] = uploaded_file.name
        st.success("New document loaded! Chat history cleared.")
        
    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state["chat_history"] = []
        st.success("Chat history cleared!")
        st.rerun()

# ==========================================
# 5. MAIN PANEL INTERFACE
# ==========================================
st.markdown('<div class="title-text">Abdulrahman Alnammoura | Premium Gemini RAG PDF Chat</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">A professional-grade, high-performance RAG workspace using native Gemini API.</div>', unsafe_allow_html=True)

# 5.1 Check API Key
if not api_key:
    st.warning("⚠️ Please configure your Gemini API Key in the sidebar to start.")
    st.stop()

# 5.2 Prompt for Document Ingestion
if not uploaded_file:
    st.info("💡 **Welcome!** Please upload a PDF file in the sidebar to begin interacting with its contents.")
    st.stop()

# 5.3 Display Ingestion Metadata Card
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <strong>📂 Active PDF:</strong> {uploaded_file.name}<br/>
        <strong>⚖️ File Size:</strong> {len(uploaded_file.getvalue()) / 1024:.1f} KB
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <strong>🤖 Model:</strong> {model_name}<br/>
        <strong>🌡️ Temperature:</strong> {temperature}
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 6. CONVERSATIONAL RAG LOGIC & CHAT UI
# ==========================================
# Render Conversation History
for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept User Chat Query
user_query = st.chat_input("Ask a question about the document...")

if user_query:
    # Render User Query Immediately
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state["chat_history"].append({"role": "user", "content": user_query})
    
    # Generate Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("🧠 *Processing document and formulating answer...*")
        
        try:
            # Step A: Initialize native Google GenAI Client
            client = genai.Client(api_key=api_key)
            
            # Step B: Construct PDF part directly from uploaded bytes
            pdf_part = types.Part.from_bytes(
                data=uploaded_file.getvalue(),
                mime_type="application/pdf"
            )
            
            # Step C: Formulate Grounded Prompt with Chat History & Context
            prompt_contents = [
                pdf_part,
                "You are a Senior HR Expert and an advanced Applicant Tracking System (ATS) simulator. Analyze the uploaded PDF resume thoroughly. When the user asks for an ATS score or evaluation, grade the resume out of 100% based on professional standards (Layout, Skills, AI degree alignment, Keywords, Experience impact). Provide a detailed, constructive breakdown of strengths, weaknesses, and clear actionable bullet points for improvement. Maintain a supportive, highly professional tone. Your final response must still be beautifully formatted for Abdulrahman Alnammoura's premium workspace."
            ]
            
            # Append Chat History Messages
            for msg in st.session_state["chat_history"][:-1]:  # exclude latest user query
                role_label = "User" if msg["role"] == "user" else "Assistant"
                prompt_contents.append(f"{role_label}: {msg['content']}")
                
            # Append Latest Query
            prompt_contents.append(f"User: {user_query}\nAssistant:")
            
            # Step D: Call Gemini Model with 503 Retry & Pro Fallback
            config = types.GenerateContentConfig(temperature=temperature)
            
            response = None
            last_err = None
            primary_model = model_name.replace("models/", "")
            
            # Try 1: Primary Model (gemini-2.5-flash)
            try:
                response = client.models.generate_content(
                    model=primary_model,
                    contents=prompt_contents,
                    config=config
                )
            except Exception as e:
                last_err = e
                response_placeholder.markdown("⚠️ *Gemini is busy, retrying in 2 seconds...*")
                time.sleep(2.0)
                
                try:
                    # Try 2: Retry Primary Model
                    response = client.models.generate_content(
                        model=primary_model,
                        contents=prompt_contents,
                        config=config
                    )
                except Exception as e_retry:
                    last_err = e_retry
                    fallback_model = "gemini-2.5-pro"
                    response_placeholder.markdown("⚠️ *Flash unavailable, falling back to Gemini 2.5 Pro...*")
                    time.sleep(1.0)
                    
                    try:
                        response = client.models.generate_content(
                            model=fallback_model,
                            contents=prompt_contents,
                            config=config
                        )
                    except Exception as e_fallback:
                        last_err = e_fallback
            
            if response is None:
                raise last_err
            
            answer = response.text or "No response text generated by the model."
            
            # Display Final Response
            response_placeholder.markdown(answer)
            st.session_state["chat_history"].append({"role": "assistant", "content": answer})
            
        except Exception as e:
            response_placeholder.error(f"❌ **Error:** {str(e)}")
            st.error("Please verify that your Gemini API key is correct and valid.")
