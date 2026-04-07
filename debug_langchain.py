from langchain_community.document_loaders import YoutubeLoader

video_url = "https://www.youtube.com/watch?v=6H5gQXzN6vQ"

try:
    print("Attempting LangChain YoutubeLoader...")
    loader = YoutubeLoader.from_youtube_url(
        video_url, 
        add_video_info=True,
        language=["en", "en-US"]
    )
    docs = loader.load()
    print("Success!")
    print(f"Content preview: {docs[0].page_content[:100]}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()