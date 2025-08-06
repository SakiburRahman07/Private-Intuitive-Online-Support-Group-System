from typing import Dict, List, TypedDict
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from sqlalchemy import create_engine, text
from datetime import datetime
import uuid
from utils.logger import logger
from config.settings import settings

# Initialize Groq chat model
groq_api_key = settings.GROQ_API_KEY
if not groq_api_key:
    logger.error("GROQ_API_KEY not found in environment variables")
    raise ValueError("GROQ_API_KEY not found in environment variables")

# Initialize database engine
try:
    engine = create_engine(settings.DATABASE_URL)
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Successfully connected to PostgreSQL database")
except Exception as e:
    logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
    raise

# Initialize embeddings
try:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    logger.info("Successfully initialized HuggingFace embeddings")
except Exception as e:
    logger.error(f"Failed to initialize embeddings: {str(e)}")
    raise

# Initialize vector store
try:
    pg_vector_store = PGVector(
        embeddings=embeddings,
        connection=settings.DATABASE_URL,
        collection_name="diary_entries",
        use_jsonb=True,
    )
    logger.info("Successfully initialized PostgreSQL vector store")
except Exception as e:
    logger.error(f"Failed to initialize vector store: {str(e)}")
    raise

model = ChatGroq(
    groq_api_key=groq_api_key, model_name="llama3-70b-8192", temperature=0.7
)


# Define state types
class AgentState(TypedDict):
    messages: List[Dict]
    mood: str
    analysis: str
    confidence: float


# Define Pydantic models
class DiaryEntry(BaseModel):
    content: str
    date: str
    user_id: str


class StoredDiaryEntry(DiaryEntry):
    id: str
    mood: str
    analysis: str
    confidence: float
    created_at: datetime


class MoodAnalysis(BaseModel):
    mood: str
    analysis: str
    confidence: float


# Define the nodes for our graph
def analyze_mood(state: AgentState) -> AgentState:
    """Analyze the mood from the diary entry."""
    messages = state["messages"]
    last_message = messages[-1]["content"]

    # Create prompt for mood analysis
    prompt = f"""Analyze the following diary entry and determine the user's mood:
    {last_message}
    
    Please provide:
    1. The primary mood (e.g., happy, sad, anxious, calm)
    2. A brief analysis of why you think this is the mood
    3. Your confidence level (0-1)
    
    Format your response as:
    MOOD: [mood]
    ANALYSIS: [analysis]
    CONFIDENCE: [confidence]
    """

    try:
        response = model.invoke(prompt)
        response_text = response.content

        # Parse the response
        mood = ""
        analysis = ""
        confidence = 0.5  # Default confidence if parsing fails

        for line in response_text.split("\n"):
            if line.startswith("MOOD:"):
                mood = line.split(":")[1].strip()
            elif line.startswith("ANALYSIS:"):
                analysis = line.split(":")[1].strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    confidence = 0.5

        # Ensure we have valid values
        if not mood:
            mood = "neutral"
        if not analysis:
            analysis = "Unable to determine specific mood patterns"

        return {
            "messages": messages,
            "mood": mood,
            "analysis": analysis,
            "confidence": confidence,
        }
    except Exception as e:
        # Return default values in case of error
        return {
            "messages": messages,
            "mood": "neutral",
            "analysis": "Error in mood analysis",
            "confidence": 0.5,
        }


# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("analyze_mood", analyze_mood)

# Add edges
workflow.add_edge("analyze_mood", END)
workflow.set_entry_point("analyze_mood")

# Compile the graph
graph = workflow.compile()


# Core functions for diary operations
def analyze_diary_entry(entry: DiaryEntry) -> MoodAnalysis:
    """Analyze a diary entry and return mood analysis."""
    logger.info(f"Analyzing diary entry for user_id: {entry.user_id}")
    try:
        # Initialize state with all required fields
        initial_state = {
            "messages": [{"role": "user", "content": entry.content}],
            "mood": "",
            "analysis": "",
            "confidence": 0.0,
        }

        # Run the graph
        logger.info("Invoking mood analysis graph")
        result = graph.invoke(initial_state)

        # Create response
        response = MoodAnalysis(
            mood=result.get("mood", "neutral"),
            analysis=result.get("analysis", "Unable to analyze mood"),
            confidence=result.get("confidence", 0.5),
        )
        logger.info(
            f"Analysis complete. Mood: {response.mood}, Confidence: {response.confidence}"
        )
        return response
    except Exception as e:
        logger.error(f"Error in mood analysis: {str(e)}")
        raise


def store_diary_entry(entry: DiaryEntry) -> StoredDiaryEntry:
    """Store a diary entry in AstraDB with mood analysis."""
    logger.info(f"Storing diary entry for user_id: {entry.user_id}")
    try:
        # Analyze mood
        logger.info("Analyzing mood for entry")
        mood_analysis = analyze_diary_entry(entry)

        # Create document for vector store
        doc_id = str(uuid.uuid4())
        document = {
            "id": doc_id,
            "content": entry.content,
            "date": entry.date,
            "user_id": entry.user_id,
            "mood": mood_analysis.mood,
            "analysis": mood_analysis.analysis,
            "confidence": mood_analysis.confidence,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Store in PostgreSQL
        logger.info(f"Storing entry in PostgreSQL with ID: {doc_id}")
        pg_vector_store.add_texts(
            texts=[entry.content], metadatas=[document], ids=[doc_id]
        )

        # Return stored entry
        stored_entry = StoredDiaryEntry(
            content=entry.content,
            date=entry.date,
            user_id=entry.user_id,
            id=doc_id,
            mood=mood_analysis.mood,
            analysis=mood_analysis.analysis,
            confidence=mood_analysis.confidence,
            created_at=datetime.utcnow(),
        )
        logger.info(f"Entry stored successfully with ID: {doc_id}")
        return stored_entry
    except Exception as e:
        logger.error(f"Error storing diary entry: {str(e)}")
        raise


def search_diary_entries(
    query: str, user_id: str, limit: int = 5
) -> List[StoredDiaryEntry]:
    """Search diary entries using semantic search."""
    logger.info(
        f"Searching entries for user_id: {user_id}, query: {query}, limit: {limit}"
    )
    try:
        # Search in vector store
        logger.info("Performing similarity search in vector store")
        results = pg_vector_store.similarity_search_with_score(
            query=query, k=limit, filter={"user_id": user_id}
        )

        # Format results
        entries = []
        for doc, score in results:
            metadata = doc.metadata
            entries.append(
                StoredDiaryEntry(
                    id=metadata["id"],
                    content=doc.page_content,
                    date=metadata["date"],
                    user_id=metadata["user_id"],
                    mood=metadata["mood"],
                    analysis=metadata["analysis"],
                    confidence=metadata["confidence"],
                    created_at=datetime.fromisoformat(metadata["created_at"]),
                )
            )

        logger.info(f"Search complete. Found {len(entries)} entries.")
        return entries
    except Exception as e:
        logger.error(f"Error searching diary entries: {str(e)}")
        raise
