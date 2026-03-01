import os

def get_config() -> dict:
    from dotenv import load_dotenv
    load_dotenv()

    config = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
        "PINECONE_INDEX_NAME": os.getenv("PINECONE_INDEX_NAME", "rag-assistant"),
    }

    missing = [k for k, v in config.items() if not v]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please fill in your .env file."
        )

    return config