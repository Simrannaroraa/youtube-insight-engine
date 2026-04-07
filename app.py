import streamlit as st
import utils
import time

# --- Page Config ---
st.set_page_config(
    page_title="YT Insight Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Cyberpunk/Dark Theme ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #050510;
        color: #E0E0E0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0B0C15;
        border-right: 1px solid #1F2937;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background-color: #111827;
        color: #00FFC2; /* Neon Cyan */
        border: 1px solid #374151;
        border-radius: 8px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: #000;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 201, 255, 0.5);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #00F0FF; /* Cyberpunk Cyan */
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Cards/Expanders */
    .streamlit-expanderHeader {
        background-color: #1F2937;
        color: #F3F4F6;
        border-radius: 8px;
    }
    .stAlert {
        background-color: #1F2937;
        color: #F3F4F6;
        border: 1px solid #374151;
    }
    
    /* Chat Message */
    .stChatMessage {
        background-color: #111827;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "summary" not in st.session_state:
    st.session_state["summary"] = None
if "takeaways" not in st.session_state:
    st.session_state["takeaways"] = None
if "topics" not in st.session_state:
    st.session_state["topics"] = None
if "vector_store" not in st.session_state:
    st.session_state["vector_store"] = None
if "transcript_text" not in st.session_state:
    st.session_state["transcript_text"] = None
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- Sidebar ---
with st.sidebar:
    st.title("⚡ Insight History")
    st.markdown("---")
    # Mock history for now
    st.caption("No recent history.")
    st.markdown("---")
    st.info("💡 Tip: Use a video with clear spoken audio for best results.")

# --- Main Layout ---
st.title("📺 YT Insight Engine")
st.markdown("Attributes **Executive Summary**, **Gold Nuggets**, and **Interactive Q&A** from any YouTube video.")

video_url = st.text_input("Enter YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Analyze Video ⚡"):
    if not video_url:
        st.warning("Please enter a valid URL.")
    else:
        # Clear previous session data when a new video is analyzed
        st.session_state["summary"] = None
        st.session_state["takeaways"] = None
        st.session_state["topics"] = None
        st.session_state["vector_store"] = None
        st.session_state["transcript_text"] = None
        st.session_state["messages"] = []
        try:
            with st.spinner("Initialising Quantum Link... (Extracting Transcript)"):
                transcript_text, transcript_list = utils.get_transcript(video_url)
                st.session_state["transcript_text"] = transcript_text
            
            # Show video thumbnail/embed
            st.video(video_url)
            
            progress_bar = st.progress(0, text="Analyzing Content...")
            
            with st.status("Processing intelligence...", expanded=True):
                # 1. Summary
                st.write("Generating Executive Summary...")
                summary = utils.generate_summary(transcript_text)
                st.session_state["summary"] = summary
                progress_bar.progress(33, text="Summary Generated...")
                
                # 2. Takeaways
                st.write("Extracting Gold Nuggets...")
                takeaways = utils.generate_key_takeaways(transcript_text)
                st.session_state["takeaways"] = takeaways
                progress_bar.progress(66, text="Takeaways Extracted...")
                
                # 3. Topics
                st.write("Segmenting Topics...")
                topics = utils.generate_topics(transcript_list)
                st.session_state["topics"] = topics
                
                # 4. Vector DB (for RAG)
                st.write("Building Knowledge Base...")
                # Note: This might be slow for long videos.
                vector_store = utils.create_vector_db(transcript_text)
                st.session_state["vector_store"] = vector_store
                
                progress_bar.progress(100, text="Analysis Complete!")
                time.sleep(1)
                progress_bar.empty()
                
        except ValueError as e:
            if "API Key" in str(e):
                 st.error(f"⚠️ {e}")
                 st.markdown("""
                 **Action Required:**
                 1. Create a file named `.env` in the `YT-Insight-Engine` folder.
                 2. Add your Google API Key: `GOOGLE_API_KEY=your_key_here`.
                 """)
            else:
                 st.error(f"Error accessing video data: {e}. Please ensure the video has captions enabled.")
        except Exception as e:
            if "404" in str(e) and "models/" in str(e):
                st.error(f"⚠️ Model Error: {e}")
                st.warning("The specified model is not available for your API Key/Region.")
                
                with st.spinner("Fetching available models..."):
                    available = utils.list_available_models()
                    st.code("\n".join(available), language="text")
                    st.info("Please update the model name in utils.py to one of the above.")
            else:
                st.error(f"An unexpected error occurred: {e}")

# --- Display Results ---
if st.session_state["summary"]:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Executive Summary")
        st.info(st.session_state["summary"])
        
        st.subheader("💎 Key Takeaways")
        st.markdown(st.session_state["takeaways"])
        
    with col2:
        st.subheader("📍 Topic Timeline")
        st.markdown(st.session_state["topics"])

    st.markdown("---")
    
    # --- RAG Q&A Interface ---
    st.subheader("🤖 Ask the Video")
    
    # Display chat messages
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about the video content..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if st.session_state["vector_store"]:
            with st.spinner("Thinking..."):
                qa_chain = utils.get_qa_chain(st.session_state["vector_store"])
                response = qa_chain.run(prompt)
                
            st.session_state["messages"].append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
        else:
            st.error("Vector Store not initialized. Please analyze a video first.")
