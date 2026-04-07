import os
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

genai_api_key = os.getenv("GOOGLE_API_KEY")

def validate_api_key():
    if not genai_api_key:
        raise ValueError("Google API Key not found. Please create a .env file with GOOGLE_API_KEY.")

# We don't raise immediately on import to allow app to start, 
# but we will check before LLM usage.

import re
from urllib.parse import urlparse, parse_qs

def get_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    Supports standard youtube.com and youtu.be links.
    """
    if not url:
        return None

    # Clean whitespace
    url = url.strip()

    # Handle raw IDs
    if len(url) == 11 and re.match(r"^[0-9A-Za-z_-]{11}$", url):
        return url

    try:
        parsed = urlparse(url)
    except Exception:
        parsed = None

    # Direct query param v
    if parsed and parsed.query:
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            candidate = qs["v"][0]
            if len(candidate) == 11:
                return candidate

    # Short URL youtu.be/ID or path containing ID
    if parsed and parsed.netloc in ("youtu.be", "www.youtu.be"):
        path_id = parsed.path.lstrip("/")
        if len(path_id) == 11:
            return path_id

    # Look for ID pattern in URL
    regex = r"(?:v=|/)([0-9A-Za-z_-]{11})(?:[&?#]|$)"
    match = re.search(regex, url)
    if match:
        return match.group(1)

    return None

import json
import subprocess

def get_transcript_ytdlp(video_url):
    """
    Fallback method using yt-dlp to fetch subtitles.
    Requires yt-dlp to be installed.
    """
    try:
        # Command to dump subtitles in JSON format without downloading video
        command = [
            "yt-dlp",
            "--js-runtimes", "deno",
            "--write-auto-sub",
            "--write-sub",
            "--skip-download",
            "--no-warnings",
            "--geo-bypass",
            "--sleep-requests", "1",
            "--throttled-rate", "50K",
            "--print-json"
        ]

        cookies_path = os.getenv("YT_DLP_COOKIES_PATH")
        if cookies_path:
            command += ["--cookies", cookies_path]

        proxy = os.getenv("YT_DLP_PROXY")
        if proxy:
            command += ["--proxy", proxy]

        # Add language fallback list to improve subtitle discovery.
        command += ["--sub-lang", "en,hi,hi-IN,en-US,en-GB"]
        command.append(video_url)
        
        # Run yt-dlp
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        
        # yt-dlp prints JSON info. But subtitles are usually written to file or we need --dump-json.
        # Actually, extracting specific subtitle text via yt-dlp purely in stdout is tricky because it downloads files.
        # Better approach: Use yt-dlp to get the 'automatic_captions' or 'subtitles' URL, then fetch that.
        
        if result.returncode != 0:
            extra = ""
            if "Sign in to confirm you’re not a bot" in result.stderr:
                extra = " Please set YT_DLP_COOKIES_PATH in .env and pass browser cookies."
            raise Exception(f"yt-dlp failed: {result.stderr}{extra}")

        video_info = json.loads(result.stdout)
        
        # Try to find english captions
        captions = None
        if 'subtitles' in video_info and 'en' in video_info['subtitles']:
            captions = video_info['subtitles']['en']
        elif 'automatic_captions' in video_info and 'en' in video_info['automatic_captions']:
            captions = video_info['automatic_captions']['en']
            
        if not captions:
            # Try en-orig or similar
            for lang in ['en-orig', 'en-US', 'en-GB']:
                 if 'automatic_captions' in video_info and lang in video_info['automatic_captions']:
                    captions = video_info['automatic_captions'][lang]
                    break
        
        if not captions:
            raise ValueError("No English captions found via yt-dlp.")
            
        # The captions are a list of formats. usually json3 or vtt.
        # We need to fetch the content. yt-dlp gave us URLs.
        # Let's use requests to fetch the 'json3' format if available, simpler to parse.
        
        caption_url = None
        for fmt in captions:
            if fmt['ext'] == 'json3':
                caption_url = fmt['url']
                break
        
        if not caption_url:
             # Fallback to whatever is first
             caption_url = captions[0]['url']
        
        import requests
        resp = requests.get(caption_url)
        if resp.status_code != 200:
             raise Exception("Failed to download caption data from URL provided by yt-dlp")
             
        # Parse JSON3 or VTT. JSON3 is expected if we selected it.
        # If it's VTT/SRT we need a parser. Let's hope for JSON3 for auto-subs usually.
        
        try:
             # JSON3 format: { "events": [ { "tStartMs": 1000, "dDurationMs": 200, "segs": [ { "utf8": "text" } ] } ] }
             data = resp.json()
             transcript_text = ""
             transcript_data = [] # For list format
             
             if 'events' in data:
                 for event in data['events']:
                     text_seg = ""
                     if 'segs' in event:
                         for seg in event['segs']:
                             if 'utf8' in seg and seg['utf8'] != '\n':
                                 text_seg += seg['utf8']
                     
                     if text_seg.strip():
                         transcript_text += " " + text_seg
                         transcript_data.append({
                             'text': text_seg,
                             'start': event.get('tStartMs', 0) / 1000.0,
                             'duration': event.get('dDurationMs', 0) / 1000.0
                         })
                         
             return transcript_text, transcript_data
             
        except:
            # If json parse fails, might be XML or VTT.
             return str(resp.text), []

    except Exception as e:
        raise e

def get_transcript(video_url):
    """
    Extracts transcript from a YouTube video URL.
    Returns the transcript text or raises an exception.
    """
    from langchain_community.document_loaders import YoutubeLoader

    try:
        loader = YoutubeLoader.from_youtube_url(
            video_url,
            add_video_info=False,
            language=["en", "en-US", "hi", "hi-IN"]
        )
        docs = loader.load()
        if not docs:
            raise ValueError("No transcript documents were loaded.")

        transcript_text = " ".join([doc.page_content for doc in docs])
        transcript_list = [{"text": doc.page_content, "start": 0} for doc in docs]
        return transcript_text, transcript_list
    except Exception as e:
        # If YoutubeLoader fails or returns no docs, try the yt-dlp fallback.
        print(f"YoutubeLoader fallback triggered: {e}")
        return get_transcript_ytdlp(video_url)

import google.generativeai as genai

def list_available_models():
    """Lists available models for the configured API key."""
    validate_api_key()
    genai.configure(api_key=genai_api_key)
    models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name)
    except Exception as e:
        models.append(f"Error listing models: {e}")
    return models

def get_llm():
    """Returns a configured Gemini 2.5 Flash model."""
    validate_api_key()
    return ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.3, google_api_key=genai_api_key)

def generate_summary(text):
    """Generates a concise executive summary."""
    llm = get_llm()
    prompt_template = """
    You are an expert content summarizer. Provide a concise, widely accessible executive summary of the following video transcript.
    Constraint: The summary must be a single paragraph.
    
    Transcript:
    {text}
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
    chain = prompt | llm
    response = chain.invoke({"text": text})
    return response.content

def generate_key_takeaways(text):
    """Generates 5-7 key takeaways (Gold Nuggets)."""
    llm = get_llm()
    prompt_template = """
    You are an expert analyst. Identify the top 5-7 distinct "Gold Nuggets" or key insights from the following video transcript.
    Output format: a Markdown bulleted list.
    
    Transcript:
    {text}
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
    chain = prompt | llm
    response = chain.invoke({"text": text})
    return response.content

def generate_topics(transcript_list):
    """
    Generates topic segmentation from the raw transcript list (with timestamps).
    Uses a heuristic or LLM to group segments. 
    For efficiency, we'll suggest a simplified LLM approach or direct timestamp mapping.
    Here we use LLM to analyze the flow.
    """   
    formatted_transcript = ""
    # Sample every 30 seconds or so to keep context window small if needed, 
    # but for now let's try a bulk approach with a reasonable limit.
    for item in transcript_list[:300]: # Limit to first 300 chunks to avoid context overflow in MVP
        time = int(item['start'])
        minutes = time // 60
        seconds = time % 60
        timestamp = f"{minutes:02d}:{seconds:02d}"
        formatted_transcript += f"[{timestamp}] {item['text']}\n"
        
    llm = get_llm()
    prompt_template = """
    Analyze the following transcript with timestamps. 
    Identify 5-8 major topic shifts. 
    Output strictly in this format: "MM:SS - Topic Title"
    
    Transcript:
    {text}
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
    chain = prompt | llm
    response = chain.invoke({"text": formatted_transcript})
    return response.content

def create_vector_db(text):
    """Creates a FAISS vector index for the transcript."""
    validate_api_key()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_text(text)
    
    # Use gemini-embedding-001 which is available on most Gemini API keys
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=genai_api_key)
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    return vector_store

def get_qa_chain(vector_store):
    """Returns a QA chain for the vector store."""
    llm = get_llm()
    
    prompt_template = """
    Answer the question as detailed as possible from the provided context. Answer in English only.
    If the answer is not in the provided context, just say "answer is not available in the context", don't provide the wrong answer.
    
    Context:
    {context}
    
    Question:
    {question}
    
    Answer:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    retriever = vector_store.as_retriever()
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Wrap to have a run method for compatibility
    class QAChain:
        def __init__(self, chain):
            self.chain = chain
        
        def run(self, question):
            return self.chain.invoke(question)
    
    return QAChain(rag_chain)