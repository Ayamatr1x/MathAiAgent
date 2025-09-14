import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from qdrant_utils import search_qdrant, openai_client
from search_utils import search_and_generate_answer
import time
import sqlite3

# Import DSPy integration
try:
    from dspyfeedback import create_enhanced_solver, solve_with_enhanced_system
    DSPY_INTEGRATION_AVAILABLE = True
    print("✅ DSPy integration imported successfully")
    # Initialize the enhanced solver system
    enhanced_solver = create_enhanced_solver()
    print("✅ Enhanced solver system initialized")
except ImportError as e:
    print(f"⚠️ DSPy integration not available: {e}")
    DSPY_INTEGRATION_AVAILABLE = False
    enhanced_solver = None

app = FastAPI(title="Math Agent API (Agentic-RAG)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Pydantic models
# ----------------------------
class Query(BaseModel):
    question: str

class FeedbackIn(BaseModel):
    question: str
    answer: str
    rating: Optional[int] = None
    comment: Optional[str] = None

class AnswerOut(BaseModel):
    question: str
    source: str
    steps: List[str]
    final_answer: Optional[str]
    enhanced: Optional[bool] = False
    method: Optional[str] = "standard"
    confidence: Optional[float] = 0.5

class EnhancedFeedbackOut(BaseModel):
    status: str
    enhanced: bool
    improvement_applied: bool
    method_used: str
    improved_steps: Optional[List[str]] = None

# ----------------------------
# Guardrails
# ----------------------------
MATH_KEYWORDS = [
    "solve", "integrate", "differentiate", "derivative", "limit", "roots",
    "equation", "matrix", "theorem", "prove", "evaluate", "simplify",
    "laplace", "fourier", "sum", "product", "geometry", "trigonometry",
    "probability", "stats", "statistical", "integral", "sum", "factorize"
]

def input_guardrail(query: str) -> bool:
    q = query.lower()
    if any(ch.isdigit() for ch in q):
        return True
    if any(kw in q for kw in MATH_KEYWORDS):
        return True
    return False

def output_guardrail_text(text: str) -> str:
    if not text or len(text.strip()) == 0:
        return "⏳ This question could not be answered from the knowledge base or web search."
    banned = ["joke", "love letter", "sex", "romance", "politics"]
    low = text.lower()
    if any(b in low for b in banned):
        return "⚠️ This system only returns mathematics-related educational answers."
    return text

# ----------------------------
# Generation helpers
# ----------------------------
def generate_step_by_step_standard(question: str, context: str = "") -> Dict[str, Any]:
    prompt = f"""
You are a patient mathematics professor. Provide a step-by-step solution to the question below.
Return a JSON with two keys: "steps" (a list of numbered steps, concise) and "final_answer" (short).
Do NOT add any extra commentary outside the JSON.

Question: {question}

Context (if any): {context}
"""
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful math professor who explains steps clearly."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        text = resp.choices[0].message.content.strip()
    except Exception as e:
        return {
            "steps": ["Error connecting to AI model. Please check your API configuration."],
            "final_answer": f"Service temporarily unavailable: {str(e)}",
            "enhanced": False,
            "method": "error",
            "confidence": 0.0
        }

    try:
        payload = json.loads(text)
        steps = payload.get("steps", [])
        final = payload.get("final_answer", "")
        steps = [str(s).strip() for s in steps] if isinstance(steps, list) else [str(steps)]
        return {
            "steps": steps,
            "final_answer": str(final).strip(),
            "enhanced": False,
            "method": "standard",
            "confidence": 0.6
        }
    except Exception:
        safe_text = output_guardrail_text(text)
        return {
            "steps": [safe_text],
            "final_answer": safe_text,
            "enhanced": False,
            "method": "standard_fallback",
            "confidence": 0.4
        }

def generate_step_by_step_enhanced(question: str, context: str = "") -> Dict[str, Any]:
    """Generate solution using DSPy enhanced system"""
    if not DSPY_INTEGRATION_AVAILABLE or not enhanced_solver:
        print("⚠️ DSPy not available, falling back to standard")
        return generate_step_by_step_standard(question, context)
    
    try:
        result = solve_with_enhanced_system(question, context, enhanced_solver)
        print(f"✅ DSPy enhanced solution generated with method: {result.get('method')}")
        return result
    except Exception as e:
        print(f"⚠️ DSPy enhanced generation failed: {e}, falling back to standard")
        return generate_step_by_step_standard(question, context)

# ----------------------------
# Enhanced /ask endpoint
# ----------------------------
KB_MATCH_THRESHOLD = 0.4

@app.post("/ask", response_model=AnswerOut)
def ask_question(q: Query):
    question = q.question.strip()
    print(f"🔍 Received question: {question}")

    if not input_guardrail(question):
        raise HTTPException(status_code=400, detail="Only mathematics-related queries are allowed. Try phrasing the math problem more explicitly.")

    try:
        kb_results = search_qdrant(question, top_k=1)
        print(f"📚 KB search completed, found {len(kb_results) if kb_results else 0} results")
    except Exception as e:
        kb_results = []
        print("⚠️ Qdrant search failed:", e)

    # Determine source and context
    if kb_results and len(kb_results) > 0:
        top_score = getattr(kb_results[0], "score", 0)
        print(f"📊 Top KB score: {top_score:.3f} (threshold: {KB_MATCH_THRESHOLD})")
        if top_score >= KB_MATCH_THRESHOLD:
            payload = getattr(kb_results[0], "payload", {}) or {}
            src = payload.get("source", "Knowledge Base")
            context = payload.get("problem", "") or payload.get("solution", "")
            print(f"📚 Using KB context for answer generation with source: {src}")
        else:
            print(f"⚠️ KB score too low ({top_score:.3f} < {KB_MATCH_THRESHOLD}), falling back to web")
            src = "web"
            context = ""
    else:
        src = "web"
        context = ""
        print(f"🌐 Using web search for answer generation (no KB results)")

    # Get web context if needed
    if src == "web":
        try:
            context = search_and_generate_answer(question)
            print("🌐 Web context retrieved")
        except Exception as e:
            print("⚠️ Web search failed:", e)
            context = ""

    # Generate answer - try DSPy enhanced first, fallback to standard
    try:
        if DSPY_INTEGRATION_AVAILABLE and enhanced_solver:
            print("🧠 Attempting DSPy enhanced generation")
            gen = generate_step_by_step_enhanced(question, context)
        else:
            print("📝 Using standard generation")
            gen = generate_step_by_step_standard(question, context)
        
        steps = gen["steps"]
        final = gen["final_answer"]
        enhanced = gen.get("enhanced", False)
        method = gen.get("method", "standard")
        confidence = gen.get("confidence", 0.5)
        
    except Exception as e:
        print("⚠️ All generation methods failed:", e)
        gen = generate_step_by_step_standard(question, context="")
        return AnswerOut(
            question=question,
            source="fallback",
            steps=gen["steps"],
            final_answer=gen["final_answer"] or "Unable to generate a complete solution. Please try rephrasing your question.",
            enhanced=False,
            method="fallback",
            confidence=0.3
        )

    final = output_guardrail_text(final)
    steps = [output_guardrail_text(s) for s in steps]

    print(f"✅ Generated answer with method: {method}, enhanced: {enhanced}")
    return AnswerOut(
        question=question,
        source=src,
        steps=steps,
        final_answer=final,
        enhanced=enhanced,
        method=method,
        confidence=confidence
    )

# ----------------------------
# Database initialization
# ----------------------------
DB_PATH = "feedback.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT,
        rating INTEGER,
        comment TEXT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()
    print("📊 Database initialized")

init_db()

# ----------------------------
# Enhanced /feedback endpoint with DSPy integration
# ----------------------------
@app.post("/feedback", response_model=EnhancedFeedbackOut)
def receive_enhanced_feedback(f: FeedbackIn):
    print(f"💭 Received feedback for question: {f.question[:50]}...")
    
    try:
        # Store basic feedback first
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO feedback (question, answer, rating, comment) VALUES (?, ?, ?, ?)",
                    (f.question, f.answer, f.rating, f.comment))
        conn.commit()
        conn.close()
        
        # Try DSPy enhancement if available and feedback has content
        if DSPY_INTEGRATION_AVAILABLE and enhanced_solver and (f.rating or f.comment):
            try:
                feedback_text = f.comment or f"Rating: {f.rating}/5"
                
                # Process feedback through DSPy system
                improvement_result = enhanced_solver.process_feedback(
                    question=f.question,
                    original_solution=f.answer,
                    feedback_text=feedback_text,
                    rating=f.rating or 3
                )
                
                improved_steps = improvement_result.get("steps", [])
                method_used = improvement_result.get("method", "dspy_improved")
                improvement_applied = improvement_result.get("improvement_applied", False)
                
                print(f"🔄 DSPy improvement: {improvement_applied}, method: {method_used}")
                
                return EnhancedFeedbackOut(
                    status="ok",
                    enhanced=True,
                    improvement_applied=improvement_applied,
                    method_used=method_used,
                    improved_steps=improved_steps
                )
                
            except Exception as e:
                print(f"⚠️ DSPy feedback processing failed: {e}")
                # Fall back to standard response
                pass
        
        # Standard feedback response
        return EnhancedFeedbackOut(
            status="ok",
            enhanced=DSPY_INTEGRATION_AVAILABLE,
            improvement_applied=False,
            method_used="standard",
            improved_steps=None
        )
        
    except Exception as e:
        print(f"❌ Feedback processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process feedback: {e}")

# ----------------------------
# DSPy status and metrics endpoints
# ----------------------------
@app.get("/dspy-status")
def get_dspy_status():
    print("🔍 Status requested")
    
    status = {
        "dspy_available": DSPY_INTEGRATION_AVAILABLE,
        "enhanced_solver_ready": enhanced_solver is not None
    }
    
    if DSPY_INTEGRATION_AVAILABLE and enhanced_solver:
        status["message"] = "DSPy system active and ready for enhanced learning"
        status["solver_type"] = enhanced_solver.solver.dspy_available
    else:
        status["message"] = "DSPy system not available - using standard mode"
    
    return status

@app.get("/learning-metrics")
def get_learning_metrics():
    print("📊 Metrics requested")
    
    if DSPY_INTEGRATION_AVAILABLE and enhanced_solver:
        try:
            stats = enhanced_solver.get_stats()
            return {
                "total_improvements": stats.get("total_improvements", 0),
                "average_rating": stats.get("average_rating", 0.0),
                "learning_active": stats.get("learning_active", False),
                "methods_used": stats.get("methods_used", {}),
                "dspy_available": stats.get("dspy_available", False)
            }
        except Exception as e:
            print(f"⚠️ Error getting learning metrics: {e}")
    
    # Fallback metrics
    return {
        "total_improvements": 0,
        "average_rating": 0.0,
        "learning_active": False,
        "methods_used": {},
        "dspy_available": False
    }

@app.post("/improve-solution")
def improve_solution(improvement_request: Dict[str, str]):
    if not DSPY_INTEGRATION_AVAILABLE or not enhanced_solver:
        raise HTTPException(status_code=400, detail="Improvement not available without DSPy")
    
    question = improvement_request.get("question", "")
    original_solution = improvement_request.get("original_solution", "")
    feedback = improvement_request.get("feedback", "")
    
    if not question or not original_solution or not feedback:
        raise HTTPException(status_code=400, detail="Missing required fields: question, original_solution, feedback")
    
    try:
        result = enhanced_solver.process_feedback(
            question=question,
            original_solution=original_solution,
            feedback_text=feedback,
            rating=3  # Default rating for manual improvements
        )
        
        return {
            "improved_steps": result.get("steps", []),
            "final_answer": result.get("final_answer", ""),
            "method": result.get("method", "unknown"),
            "improvement_applied": result.get("improvement_applied", False)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Improvement failed: {str(e)}")

# ----------------------------
# Health check endpoint
# ----------------------------
@app.get("/health")
def health_check():
    print("🏥 Health check requested")
    return {
        "status": "healthy",
        "components": {
            "qdrant": "available",
            "openai": "available", 
            "web_search": "available",
            "dspy_learning": "enabled" if DSPY_INTEGRATION_AVAILABLE else "disabled",
            "enhanced_solver": "ready" if enhanced_solver else "not_initialized"
        }
    }

@app.get("/")
def root():
    return {
        "message": "Math Agent API", 
        "status": "running",
        "dspy_enabled": DSPY_INTEGRATION_AVAILABLE
    }

# ----------------------------
# Run guidance
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Math Agent API")
    print("🌐 CORS enabled for localhost:3000 and localhost:5173")
    if DSPY_INTEGRATION_AVAILABLE:
        print("🧠 DSPy enhanced learning system active")
    else:
        print("📚 Running in standard mode - DSPy not available")
    uvicorn.run(app, host="0.0.0.0", port=8000)