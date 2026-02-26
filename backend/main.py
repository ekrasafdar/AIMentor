from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from structures.trie import Trie
from structures.linked_list import DoublyLinkedList
from structures.graph import Graph
from structures.heap import MaxHeap
from llm_service import get_llm_response
import uvicorn
import os
import uuid
from pathlib import Path

app = FastAPI(title="Mental Health Chatbot Backend")

# Define paths
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Mount static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
async def read_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

# --- Data Structure Initialization ---

# 1. Trie for Crisis Detection
crisis_trie = Trie()
crisis_keywords = {
    "suicide": "crisis",
    "kill myself": "crisis",
    "hurt myself": "crisis",
    "die": "crisis",
    "overdose": "crisis",
    "anxiety": "anxiety",
    "panic": "anxiety",
    "depressed": "depression",
    "sad": "depression",
    "lonely": "loneliness"
}
for word, category in crisis_keywords.items():
    crisis_trie.insert(word, category)

# 2. Graph for Resources (with ratings for Heap)
resource_graph = Graph()
# Add nodes with ratings (1-10)
resource_graph.add_node("root", {"title": "Mental Health", "desc": "General well-being", "rating": 5})
resource_graph.add_node("anxiety", {"title": "Anxiety Support", "desc": "Tips for managing anxiety", "link": "https://www.anxiety.org", "rating": 8})
resource_graph.add_node("depression", {"title": "Depression Help", "desc": "Understanding depression", "link": "https://www.nami.org", "rating": 9})
resource_graph.add_node("meditation", {"title": "Meditation", "desc": "Guided breathing", "link": "https://www.headspace.com", "rating": 7})
resource_graph.add_node("crisis", {"title": "Crisis Hotline", "desc": "Immediate help: 988", "link": "tel:988", "rating": 10})
# Pakistan Specific Resources
resource_graph.add_node("umang", {"title": "Umang Pakistan", "desc": "24/7 Mental Health Helpline", "link": "tel:03117786264", "rating": 10})
resource_graph.add_node("rozan", {"title": "Rozan Helpline", "desc": "Emotional Health Support", "link": "tel:080022444", "rating": 9})

# Add edges
resource_graph.add_edge("root", "anxiety")
resource_graph.add_edge("root", "depression")
resource_graph.add_edge("anxiety", "meditation")
resource_graph.add_edge("depression", "crisis")
resource_graph.add_edge("crisis", "umang")
resource_graph.add_edge("crisis", "rozan")

# 3. Session Management (Hash Map)
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, DoublyLinkedList] = {}

    def get_history(self, session_id: str) -> DoublyLinkedList:
        if session_id not in self.sessions:
            self.sessions[session_id] = DoublyLinkedList(max_size=10)
        return self.sessions[session_id]

session_manager = SessionManager()

# --- API Models ---

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    detected_category: Optional[str] = None
    resources: List[dict] = []
    session_id: str

# --- Endpoints ---

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    user_msg = request.message
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Step 1: Check Trie for keywords
    category = crisis_trie.search(user_msg)
    
    raw_resources = []
    system_instruction = "You are a compassionate mental health assistant. Be empathetic and brief."

    # Step 2: Handle Crisis/Category
    if category == "crisis":
        system_instruction += " The user is in crisis. Urgently suggest they call a hotline. Do not give medical advice."
        raw_resources = resource_graph.get_related("crisis")
    elif category:
        raw_resources = resource_graph.get_related(category)
        if category == "anxiety":
             raw_resources.extend(resource_graph.get_related("meditation"))

    # Step 3: Prioritize Resources using MaxHeap
    # We want to show highest rated resources first
    resource_heap = MaxHeap()
    for res in raw_resources:
        # Ensure rating exists, default to 5
        if 'rating' not in res:
            res['rating'] = 5
        resource_heap.insert(res)
    
    sorted_resources = resource_heap.get_sorted_list()

    # Step 4: Update Session History
    history = session_manager.get_history(session_id)
    history.append("user", user_msg)
    
    # Step 5: Generate Response
    history_text = ""
    current = history.head
    while current:
        history_text += f"{current.role}: {current.content}\n"
        current = current.next
        
    ai_response = await get_llm_response(history_text, user_msg, system_instruction)
    
    # Update history with AI response
    history.append("assistant", ai_response)
    
    return ChatResponse(
        response=ai_response,
        detected_category=category,
        resources=sorted_resources,
        session_id=session_id
    )

from report_generator import create_pdf_report

@app.get("/report/{session_id}")
async def generate_report(session_id: str):
    history = session_manager.get_history(session_id)
    if not history.head:
        raise HTTPException(status_code=404, detail="Session not found or empty")
    
    pdf_path = await create_pdf_report(session_id, history)
    return {"report_url": pdf_path}

@app.get("/history/{session_id}")
def get_history(session_id: str):
    history = session_manager.get_history(session_id)
    return history.to_list()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
