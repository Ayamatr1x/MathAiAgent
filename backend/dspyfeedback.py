# simple_dspy_feedback.py
# Simplified DSPy integration that works with current versions
# Provides enhanced math solving and feedback learning capabilities

import os
import sqlite3
import json
from typing import List, Dict, Optional
from openai import OpenAI

# Set OpenAI API key as environment variable (safer approach)
OPENAI_API = "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"
os.environ["OPENAI_API_KEY"] = OPENAI_API

# Try importing DSPy with error handling and configure it
try:
    import dspy
    # Configure DSPy with OpenAI using the provided API key
    dspy.settings.configure(lm=dspy.OpenAI(model="gpt-4o-mini", api_key=OPENAI_API))
    DSPY_AVAILABLE = True
    print("✅ DSPy configured successfully with OpenAI")
except Exception as e:
    print(f"⚠️ DSPy configuration failed: {e}")
    print("📝 Check OpenAI API key, internet connection, or install dspy-ai with: pip install dspy-ai")
    DSPY_AVAILABLE = False

# Fallback OpenAI client
openai_client = OpenAI(api_key=OPENAI_API)

# ----------------------------
# DSPy Signatures (only if DSPy available)
# ----------------------------
if DSPY_AVAILABLE:
    class MathSolutionSignature(dspy.Signature):
        """Generate step-by-step mathematical solution"""
        question: str = dspy.InputField(desc="Mathematical question to solve")
        context: str = dspy.InputField(desc="Relevant context from knowledge base or web search")
        solution: str = dspy.OutputField(desc="Step-by-step solution with clear explanations")

    class FeedbackImprovementSignature(dspy.Signature):
        """Improve mathematical solution based on human feedback"""
        question: str = dspy.InputField(desc="Original mathematical question")
        original_solution: str = dspy.InputField(desc="Original solution that received feedback")
        human_feedback: str = dspy.InputField(desc="Human feedback about what was wrong or could be improved")
        improved_solution: str = dspy.OutputField(desc="Improved step-by-step solution incorporating feedback")

# ----------------------------
# Enhanced Math Solver Class
# ----------------------------
class EnhancedMathSolver:
    """Math solver with DSPy integration and fallback"""
    
    def __init__(self):
        self.dspy_available = DSPY_AVAILABLE
        
        if self.dspy_available:
            try:
                self.dspy_solver = dspy.ChainOfThought(MathSolutionSignature)
                self.dspy_improver = dspy.ChainOfThought(FeedbackImprovementSignature)
                print("✅ DSPy modules initialized successfully")
            except Exception as e:
                print(f"⚠️ DSPy modules failed to initialize: {e}")
                self.dspy_available = False
        
        # Always have OpenAI fallback
        self.openai_client = openai_client
        
        # Store training examples
        self.feedback_examples = []
    
    def solve_with_dspy(self, question: str, context: str = "") -> Dict:
        """Solve using DSPy if available, otherwise use OpenAI directly"""
        
        if self.dspy_available:
            try:
                # Use DSPy
                result = self.dspy_solver(question=question, context=context)
                solution_text = result.solution
                
                return {
                    "steps": self._parse_solution_steps(solution_text),
                    "final_answer": self._extract_final_answer(solution_text),
                    "raw_solution": solution_text,
                    "method": "dspy",
                    "confidence": 0.8
                }
            except Exception as e:
                print(f"⚠️ DSPy solving failed: {e}, falling back to OpenAI")
        
        # Fallback to direct OpenAI call
        return self._solve_with_openai(question, context)
    
    def improve_with_feedback(self, question: str, original_solution: str, feedback: str) -> Dict:
        """Improve solution based on feedback"""
        
        if self.dspy_available:
            try:
                # Use DSPy for improvement
                result = self.dspy_improver(
                    question=question,
                    original_solution=original_solution,
                    human_feedback=feedback
                )
                
                improved_text = result.improved_solution
                
                # Store feedback example
                self.feedback_examples.append({
                    "question": question,
                    "original": original_solution,
                    "feedback": feedback,
                    "improved": improved_text
                })
                
                return {
                    "steps": self._parse_solution_steps(improved_text),
                    "final_answer": self._extract_final_answer(improved_text),
                    "raw_solution": improved_text,
                    "method": "dspy_improved",
                    "improvement_applied": True
                }
                
            except Exception as e:
                print(f"⚠️ DSPy improvement failed: {e}, using OpenAI fallback")
        
        # Fallback improvement using OpenAI
        return self._improve_with_openai(question, original_solution, feedback)
    
    def _solve_with_openai(self, question: str, context: str = "") -> Dict:
        """Fallback solver using OpenAI directly"""
        prompt = f"""
You are a patient mathematics professor. Provide a step-by-step solution to the question below.

Question: {question}
Context: {context}

Provide a clear, step-by-step solution:
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful math professor who explains steps clearly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            
            solution_text = response.choices[0].message.content.strip()
            
            return {
                "steps": self._parse_solution_steps(solution_text),
                "final_answer": self._extract_final_answer(solution_text),
                "raw_solution": solution_text,
                "method": "openai_fallback",
                "confidence": 0.7
            }
            
        except Exception as e:
            return {
                "steps": [f"Error: {str(e)}"],
                "final_answer": "Could not generate solution",
                "raw_solution": "",
                "method": "error",
                "confidence": 0.0
            }
    
    def _improve_with_openai(self, question: str, original_solution: str, feedback: str) -> Dict:
        """Improve solution using OpenAI"""
        prompt = f"""
You are a mathematics professor. A student has provided feedback on your solution. Please improve it.

Original Question: {question}
Original Solution: {original_solution}
Student Feedback: {feedback}

Please provide an improved step-by-step solution that addresses the feedback:
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful math professor who improves explanations based on feedback."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            
            improved_text = response.choices[0].message.content.strip()
            
            return {
                "steps": self._parse_solution_steps(improved_text),
                "final_answer": self._extract_final_answer(improved_text),
                "raw_solution": improved_text,
                "method": "openai_improved",
                "improvement_applied": True
            }
            
        except Exception as e:
            return {
                "steps": [f"Error in improvement: {str(e)}"],
                "final_answer": "Could not improve solution",
                "method": "error",
                "improvement_applied": False
            }
    
    def _parse_solution_steps(self, solution_text: str) -> List[str]:
        """Parse solution text into discrete steps"""
        lines = solution_text.split('\n')
        steps = []
        current_step = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for step indicators
            if any(indicator in line.lower() for indicator in ['step', 'first', 'next', 'then', 'finally']):
                if current_step:
                    steps.append(current_step.strip())
                current_step = line
            else:
                current_step += " " + line
        
        if current_step:
            steps.append(current_step.strip())
            
        return steps if steps else [solution_text]
    
    def _extract_final_answer(self, solution_text: str) -> str:
        """Extract final answer from solution"""
        lines = solution_text.split('\n')
        for line in lines:
            if any(pattern in line.lower() for pattern in ['final answer', 'answer:', 'result:', 'therefore']):
                return line.strip()
        
        # If no explicit final answer, return last meaningful line
        meaningful_lines = [line.strip() for line in lines if line.strip()]
        return meaningful_lines[-1] if meaningful_lines else "Answer not clearly stated"

# ----------------------------
# Feedback Learning Database
# ----------------------------
class SimpleFeedbackSystem:
    """Simplified feedback system with learning"""
    
    def __init__(self, db_path: str = "feedback.db"):
        self.db_path = db_path
        self.solver = EnhancedMathSolver()
        self._init_enhanced_db()
    
    def _init_enhanced_db(self):
        """Initialize enhanced feedback database"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Enhanced feedback table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS dspy_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            original_solution TEXT,
            feedback_text TEXT,
            rating INTEGER,
            improved_solution TEXT,
            method_used TEXT,
            improvement_applied BOOLEAN DEFAULT FALSE,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Enhanced feedback database initialized")
    
    def process_feedback(self, question: str, original_solution: str, 
                        feedback_text: str, rating: int) -> Dict:
        """Process feedback and improve solution"""
        
        # Use enhanced solver to improve
        improved = self.solver.improve_with_feedback(
            question=question,
            original_solution=original_solution,
            feedback=feedback_text
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO dspy_feedback 
        (question, original_solution, feedback_text, rating, improved_solution, method_used, improvement_applied)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (question, original_solution, feedback_text, rating, 
              improved.get('raw_solution', ''), improved.get('method', 'unknown'),
              improved.get('improvement_applied', False)))
        
        conn.commit()
        conn.close()
        
        return improved
    
    def get_stats(self) -> Dict:
        """Get learning statistics"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*), AVG(rating) FROM dspy_feedback WHERE improvement_applied = TRUE")
        stats = cur.fetchone()
        
        cur.execute("SELECT method_used, COUNT(*) FROM dspy_feedback GROUP BY method_used")
        methods = dict(cur.fetchall())
        
        conn.close()
        
        return {
            "total_improvements": stats[0] or 0,
            "average_rating": round(stats[1] or 0, 2),
            "methods_used": methods,
            "dspy_available": self.solver.dspy_available,
            "learning_active": (stats[0] or 0) > 0
        }

# ----------------------------
# Integration Functions
# ----------------------------
def create_enhanced_solver():
    """Factory function to create feedback system instance"""
    return SimpleFeedbackSystem()

def solve_with_enhanced_system(question: str, context: str, feedback_system: SimpleFeedbackSystem) -> Dict:
    """Main integration point for enhanced solving"""
    result = feedback_system.solver.solve_with_dspy(question=question, context=context)
    
    # Format for existing API
    return {
        "steps": result["steps"],
        "final_answer": result["final_answer"],
        "confidence": result.get("confidence", 0.5),
        "enhanced": True,
        "method": result.get("method", "unknown")
    }

# Test function (optional, for local testing)
if __name__ == "__main__":
    print("🧪 Testing Enhanced Math Solver...")
    
    system = SimpleFeedbackSystem()
    
    # Test solve
    result = solve_with_enhanced_system(
        "What is the derivative of x^2?", 
        "", 
        system
    )
    
    print("📝 Test Result:")
    print(f"Method: {result['method']}")
    print(f"Steps: {result['steps']}")
    print(f"Final: {result['final_answer']}")
    
    # Test feedback
    feedback_result = system.process_feedback(
        question="What is the derivative of x^2?",
        original_solution="The derivative is 2x",
        feedback_text="Please show more steps",
        rating=3
    )
    
    print("\n🔄 Feedback Result:")
    print(f"Improved: {feedback_result['improvement_applied']}")
    print(f"Method: {feedback_result['method']}")
    print(f"Steps: {feedback_result['steps']}")
    
    # Show stats
    stats = system.get_stats()
    print(f"\n📊 Stats: {stats}")