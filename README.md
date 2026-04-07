🎥 YouTube Insight Engine

An AI-powered application that summarizes YouTube videos and answers user questions using Retrieval-Augmented Generation (RAG).

⸻

🚀 Features
	•	📜 Extracts YouTube video transcripts
	•	🔍 Semantic search using FAISS
	•	🤖 AI-powered summaries using Google Gemini
	•	❓ Ask questions about video content
	•	⚡ Fast and efficient retrieval system

⸻

🧠 Tech Stack
	•	Python
	•	LangChain – workflow orchestration
	•	FAISS – vector similarity search
	•	Google Gemini API – text generation
	•	dotenv – environment variable management
  
📂 Project Structure
youtube-insight-engine/
│── app.py                 # Main application
│── utils.py               # Helper functions
│── debug_transcript.py    # Debug transcript extraction
│── debug_langchain.py     # Debug LangChain flow
│── debug_utils.py         # Debug utilities
│── list_models.py         # List available Gemini models
│── requirements.txt       # Dependencies
│── .env.example           # Sample environment file


⚙️ Setup Instructions

1️⃣ Clone the repository
git clone https://github.com/Simrannaroraa/youtube-insight-engine.git
cd youtube-insight-engine

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Setup environment variables

Create a .env file:
GOOGLE_API_KEY=your_api_key_here

4️⃣ Run the application
Streamlit run app.py

🔄 How It Works
	1.	🎥 Extract YouTube transcript
	2.	✂️ Split into chunks
	3.	🔢 Convert text into embeddings
	4.	📦 Store in FAISS vector database
	5.	🔍 Retrieve relevant chunks
	6.	🤖 Generate answer using Gemini

⸻

💡 Example Use Case
	•	Input: “Summarize this YouTube video”
	•	Output: Concise AI-generated summary
	•	Input: “What are the key points about AI?”
	•	Output: Context-aware answer from video


  🚧 Future Improvements
	•	🌐 Web UI (React / Next.js)
	•	📱 Mobile app integration
	•	🎙️ Multi-video analysis
	•	☁️ Cloud deployment (AWS / Vercel)
