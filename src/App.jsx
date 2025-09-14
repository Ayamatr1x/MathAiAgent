import React, { useState, useEffect } from "react";

function App() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);
  const [rating, setRating] = useState("");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [dsypStatus, setDsypStatus] = useState(null);
  const [learningMetrics, setLearningMetrics] = useState(null);
  const [history, setHistory] = useState([]);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  // Fetch DSPy status on component mount
  useEffect(() => {
    fetchDSPyStatus();
    fetchLearningMetrics();
  }, []);

  // Function to fetch DSPy status
  const fetchDSPyStatus = async () => {
    try {
      const res = await fetch("http://localhost:8000/dspy-status");
      const data = await res.json();
      setDsypStatus(data);
    } catch (err) {
      console.error("Failed to fetch DSPy status:", err);
    }
  };

  // Function to fetch learning metrics
  const fetchLearningMetrics = async () => {
    try {
      const res = await fetch("http://localhost:8000/learning-metrics");
      const data = await res.json();
      setLearningMetrics(data);
    } catch (err) {
      console.error("Failed to fetch learning metrics:", err);
    }
  };

  // Enhanced ask question function
  const askQuestion = async () => {
    if (!question.trim()) {
      alert("Please enter a math question!");
      return;
    }

    setLoading(true);
    setFeedbackSubmitted(false);
    
    try {
      const res = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Request failed");
      }
      
      const data = await res.json();
      setResponse(data);
      
      // Add to history
      setHistory(prev => [{
        question: data.question,
        answer: data.final_answer,
        timestamp: new Date().toLocaleTimeString(),
        enhanced: data.enhanced,
        method: data.method,
        confidence: data.confidence
      }, ...prev.slice(0, 9)]); // Keep last 10
      
    } catch (err) {
      console.error("Error asking question:", err);
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Enhanced feedback submission
  const sendFeedback = async () => {
    if (!response) {
      alert("Ask a question first!");
      return;
    }

    if (!rating && !comment) {
      alert("Please provide a rating or comment!");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: response.question,
          answer: response.final_answer,
          rating: rating ? parseInt(rating) : null,
          comment: comment.trim() || null,
        }),
      });

      const feedbackResult = await res.json();
      
      if (feedbackResult.enhanced && feedbackResult.improvement_applied) {
        alert("✅ Thank you! Your feedback helped improve the AI's learning system!");
      } else {
        alert("✅ Thank you for your feedback!");
      }
      
      setRating("");
      setComment("");
      setFeedbackSubmitted(true);
      
      // Refresh learning metrics
      await fetchLearningMetrics();
      
    } catch (err) {
      console.error("Error sending feedback:", err);
      alert("Failed to send feedback. Please try again.");
    }
  };

  // Star rating component
  const StarRating = () => (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map(star => (
        <button
          key={star}
          onClick={() => setRating(star.toString())}
          className={`text-2xl transition-colors duration-200 hover:scale-110 transform ${
            star <= parseInt(rating || 0) ? 'text-amber-400' : 'text-gray-300 hover:text-amber-300'
          }`}
        >
          ★
        </button>
      ))}
    </div>
  );

  // Method badge component
  const MethodBadge = ({ method, enhanced, confidence }) => {
    const getBadgeStyle = (method, enhanced) => {
      if (enhanced && method.includes('dspy')) 
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      if (method.includes('kb')) 
        return 'bg-blue-100 text-blue-800 border-blue-200';
      if (method.includes('web')) 
        return 'bg-orange-100 text-orange-800 border-orange-200';
      return 'bg-gray-100 text-gray-800 border-gray-200';
    };

    return (
      <div className="flex items-center gap-2">
        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getBadgeStyle(method, enhanced)}`}>
          {enhanced ? '🧠 AI Enhanced' : method.toUpperCase()}
        </span>
        {confidence && (
          <span className="text-xs text-gray-500">
            {Math.round(confidence * 100)}% confidence
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-orange-400 to-amber-500 rounded-2xl mb-6 shadow-lg">
            <span className="text-2xl text-white">∫</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Math Tutor Assistant</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Get step-by-step solutions with AI-powered learning that improves from your feedback
          </p>
          
          {dsypStatus && (
            <div className={`inline-flex items-center gap-2 mt-6 px-4 py-2 rounded-full text-sm font-medium ${
              dsypStatus.dspy_available 
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' 
                : 'bg-amber-100 text-amber-800 border border-amber-200'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                dsypStatus.dspy_available ? 'bg-emerald-500' : 'bg-amber-500'
              }`}></div>
              {dsypStatus.dspy_available ? 'AI Learning System Active' : 'Standard Mode Active'}
            </div>
          )}
        </div>

        {/* Main Interface */}
        <div className="grid lg:grid-cols-3 gap-8">
          
          {/* Main Column - Question & Answer */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Question Input */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <div className="flex gap-4">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Ask me anything about math... (e.g., 'Find the derivative of sin(x²)')"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !loading && askQuestion()}
                    disabled={loading}
                    className="w-full px-4 py-3 text-gray-900 placeholder-gray-500 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200"
                  />
                </div>
                <button 
                  onClick={askQuestion}
                  disabled={loading || !question.trim()}
                  className="px-8 py-3 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-xl font-medium hover:from-orange-600 hover:to-amber-600 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Solving...
                    </>
                  ) : (
                    'Ask Question'
                  )}
                </button>
              </div>
            </div>

            {/* Answer Display */}
            {response && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">Solution</h3>
                    <MethodBadge 
                      method={response.method} 
                      enhanced={response.enhanced} 
                      confidence={response.confidence}
                    />
                  </div>
                </div>
                
                <div className="p-6 space-y-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-2">Question</h4>
                    <p className="text-gray-900 bg-gray-50 rounded-lg p-3">{response.question}</p>
                  </div>
                  
                  {response.steps && response.steps.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">Step-by-step Solution</h4>
                      <div className="space-y-3">
                        {response.steps.map((step, i) => (
                          <div key={i} className="flex gap-3">
                            <div className="flex-shrink-0 w-6 h-6 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm font-medium">
                              {i + 1}
                            </div>
                            <p className="text-gray-700 leading-relaxed">{step}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-xl p-4 border border-orange-200">
                    <h4 className="text-sm font-medium text-orange-800 mb-2">Final Answer</h4>
                    <p className="text-lg font-medium text-gray-900">{response.final_answer}</p>
                  </div>
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500 pt-2 border-t border-gray-100">
                    <span>Source: {response.source.toUpperCase()}</span>
                    <span>•</span>
                    <span>Method: {response.method}</span>
                    {response.enhanced && (
                      <>
                        <span>•</span>
                        <span className="text-emerald-600 font-medium">AI Enhanced</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Feedback Section */}
            {response && !feedbackSubmitted && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 px-6 py-4 border-b border-amber-200">
                  <h3 className="text-lg font-semibold text-gray-900">Help Improve This Solution</h3>
                  <p className="text-sm text-gray-600 mt-1">Your feedback helps the AI learn and provide better answers</p>
                </div>
                
                <div className="p-6 space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">Rate this solution</label>
                    <StarRating />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Comments (optional)</label>
                    <textarea
                      placeholder="Suggest improvements, report errors, or ask for clarification..."
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
                      rows={3}
                    />
                  </div>
                  
                  <button 
                    onClick={sendFeedback}
                    className="w-full px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-white rounded-xl font-medium hover:from-emerald-600 hover:to-green-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-all duration-200"
                  >
                    Submit Feedback
                  </button>
                </div>
              </div>
            )}

            {feedbackSubmitted && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6 text-center">
                <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-emerald-600 text-xl">✓</span>
                </div>
                <p className="text-emerald-800 font-medium">Thank you for your feedback!</p>
                <p className="text-emerald-600 text-sm mt-1">Your input helps improve the AI's learning system</p>
              </div>
            )}
          </div>

          {/* Right Column - Stats & History */}
          <div className="space-y-6">
            
            {/* Learning Metrics */}
            {learningMetrics && dsypStatus?.dspy_available && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-blue-200">
                  <h4 className="text-lg font-semibold text-gray-900">AI Learning Progress</h4>
                </div>
                <div className="p-6 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{learningMetrics.total_improvements}</div>
                      <div className="text-xs text-gray-500 uppercase tracking-wide">Improvements</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{learningMetrics.average_rating}/5.0</div>
                      <div className="text-xs text-gray-500 uppercase tracking-wide">Avg Rating</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-center gap-2 pt-4 border-t border-gray-100">
                    <div className={`w-2 h-2 rounded-full ${
                      learningMetrics.learning_active ? 'bg-green-500' : 'bg-yellow-500'
                    }`}></div>
                    <span className="text-sm text-gray-700">
                      {learningMetrics.learning_active ? 'Learning Active' : 'Collecting Data'}
                    </span>
                  </div>
                  
                  {learningMetrics.methods_used && (
                    <div className="pt-4 border-t border-gray-100">
                      <h5 className="text-sm font-medium text-gray-700 mb-2">Methods Used</h5>
                      <div className="space-y-1">
                        {Object.entries(learningMetrics.methods_used).map(([method, count]) => (
                          <div key={method} className="flex justify-between text-xs">
                            <span className="text-gray-600 capitalize">{method}</span>
                            <span className="text-gray-900 font-medium">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Question History */}
            {history.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
                  <h4 className="text-lg font-semibold text-gray-900">Recent Questions</h4>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {history.map((item, index) => (
                    <div key={index} className="p-4 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors">
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-gray-900 line-clamp-2">{item.question}</p>
                        <p className="text-xs text-gray-600 line-clamp-1">{item.answer}</p>
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>{item.timestamp}</span>
                          <div className="flex items-center gap-1">
                            <span>{item.enhanced ? '🧠' : '📚'}</span>
                            <span className="capitalize">{item.method}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;