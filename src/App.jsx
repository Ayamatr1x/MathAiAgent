import React, { useState, useEffect } from "react";
import { Send, Brain, History, TrendingUp, MessageSquare, Star, CheckCircle, AlertCircle, Clock, Zap } from "lucide-react";

function App() {
  const BASE_URL = "https://mathaiagent.onrender.com";

  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);
  const [rating, setRating] = useState("");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [dsypStatus, setDsypStatus] = useState(null);
  const [learningMetrics, setLearningMetrics] = useState(null);
  const [history, setHistory] = useState([]);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // Fetch DSPy status & learning metrics on mount
  useEffect(() => {
    fetchDSPyStatus();
    fetchLearningMetrics();
  }, []);

  // Fetch DSPy status
  const fetchDSPyStatus = async () => {
    try {
      const res = await fetch(`${BASE_URL}/dspy-status`);
      const data = await res.json();
      setDsypStatus(data);
    } catch (err) {
      console.error("Failed to fetch DSPy status:", err);
    }
  };

  // Fetch learning metrics
  const fetchLearningMetrics = async () => {
    try {
      const res = await fetch(`${BASE_URL}/learning-metrics`);
      const data = await res.json();
      setLearningMetrics(data);
    } catch (err) {
      console.error("Failed to fetch learning metrics:", err);
    }
  };

  // Ask question
  const askQuestion = async () => {
    if (!question.trim()) {
      alert("Please enter a math question!");
      return;
    }

    setLoading(true);
    setFeedbackSubmitted(false);

    try {
      const res = await fetch(`${BASE_URL}/ask`, {
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

      // Add to history (keep last 10)
      setHistory((prev) => [
        {
          question: data.question,
          answer: data.final_answer,
          timestamp: new Date().toLocaleTimeString(),
          enhanced: data.enhanced,
          method: data.method,
          confidence: data.confidence,
        },
        ...prev.slice(0, 9),
      ]);
    } catch (err) {
      console.error("Error asking question:", err);
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Send feedback
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
      const res = await fetch(`${BASE_URL}/feedback`, {
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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !loading) {
      e.preventDefault();
      askQuestion();
    }
  };

  // Star Rating Component
  const StarRating = () => (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => setRating(star.toString())}
          className={`text-xl transition-all duration-200 hover:scale-110 transform ${
            star <= parseInt(rating || 0)
              ? "text-orange-400"
              : "text-gray-300 hover:text-orange-300"
          }`}
        >
          <Star className={`w-5 h-5 ${star <= parseInt(rating || 0) ? 'fill-current' : ''}`} />
        </button>
      ))}
    </div>
  );

  // Method Badge Component
  const MethodBadge = ({ method, enhanced, confidence }) => {
    const getBadgeStyle = (method, enhanced) => {
      if (enhanced && method.includes("dspy"))
        return "bg-orange-50 text-orange-700 border-orange-200";
      if (method.includes("kb"))
        return "bg-blue-50 text-blue-700 border-blue-200";
      if (method.includes("web"))
        return "bg-purple-50 text-purple-700 border-purple-200";
      return "bg-gray-50 text-gray-700 border-gray-200";
    };

    return (
      <div className="flex items-center gap-3 flex-wrap">
        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${getBadgeStyle(
            method,
            enhanced
          )}`}
        >
          {enhanced ? (
            <>
              <Brain className="w-3 h-3" />
              AI Enhanced
            </>
          ) : (
            <>
              <Zap className="w-3 h-3" />
              {method.toUpperCase()}
            </>
          )}
        </span>
        {confidence && (
          <span className="inline-flex items-center gap-1 text-xs text-gray-500">
            <TrendingUp className="w-3 h-3" />
            {Math.round(confidence * 100)}% confidence
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Math AI Assistant</h1>
                <p className="text-sm text-gray-600">Powered by advanced reasoning</p>
              </div>
            </div>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <History className="w-4 h-4" />
              History
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Chat Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Input Section */}
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
              <div className="p-6">
                <label className="block text-sm font-medium text-gray-900 mb-3">
                  Ask a math question
                </label>
                <div className="relative">
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="e.g., Solve the quadratic equation x² - 5x + 6 = 0"
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                    rows="3"
                    disabled={loading}
                  />
                  <button
                    onClick={askQuestion}
                    disabled={loading || !question.trim()}
                    className="absolute right-3 bottom-3 inline-flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    {loading ? (
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                    {loading ? "Solving..." : "Ask"}
                  </button>
                </div>
              </div>
            </div>

            {/* Response Section */}
            {response && (
              <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
                <div className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <h3 className="font-semibold text-gray-900">Solution</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="font-medium text-gray-900 mb-2">Question:</p>
                      <p className="text-gray-700">{response.question}</p>
                    </div>
                    
                    <div className="bg-orange-50 rounded-lg p-4">
                      <p className="font-medium text-gray-900 mb-2">Answer:</p>
                      <p className="text-gray-800 whitespace-pre-wrap">{response.final_answer}</p>
                    </div>
                    
                    <MethodBadge 
                      method={response.method} 
                      enhanced={response.enhanced} 
                      confidence={response.confidence}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Feedback Section */}
            {response && !feedbackSubmitted && (
              <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
                <div className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <MessageSquare className="w-5 h-5 text-blue-500" />
                    <h3 className="font-semibold text-gray-900">How was this answer?</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Rate the answer (1-5 stars)
                      </label>
                      <StarRating />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Comments (optional)
                      </label>
                      <textarea
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        placeholder="Any feedback to help improve the AI's responses..."
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                        rows="3"
                      />
                    </div>
                    
                    <button
                      onClick={sendFeedback}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <Send className="w-4 h-4" />
                      Submit Feedback
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Status Cards */}
            <div className="grid gap-4">
              {dsypStatus && (
                <div className="bg-white border border-gray-200 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-2 h-2 rounded-full ${dsypStatus.active ? 'bg-green-500' : 'bg-red-500'}`} />
                    <h4 className="font-medium text-gray-900">System Status</h4>
                  </div>
                  <p className="text-sm text-gray-600">
                    AI Learning: {dsypStatus.active ? 'Active' : 'Inactive'}
                  </p>
                </div>
              )}

              {learningMetrics && (
                <div className="bg-white border border-gray-200 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingUp className="w-4 h-4 text-green-500" />
                    <h4 className="font-medium text-gray-900">Learning Metrics</h4>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Questions:</span>
                      <span className="font-medium">{learningMetrics.total_questions || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Avg. Rating:</span>
                      <span className="font-medium">{learningMetrics.avg_rating?.toFixed(1) || 'N/A'}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Recent History */}
            {(showHistory || history.length > 0) && (
              <div className="bg-white border border-gray-200 rounded-xl">
                <div className="p-4 border-b border-gray-200">
                  <h4 className="font-medium text-gray-900">Recent Questions</h4>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {history.length > 0 ? (
                    <div className="divide-y divide-gray-100">
                      {history.map((item, idx) => (
                        <div key={idx} className="p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Clock className="w-3 h-3 text-gray-400" />
                            <span className="text-xs text-gray-500">{item.timestamp}</span>
                            {item.enhanced && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full">
                                <Brain className="w-2.5 h-2.5" />
                                Enhanced
                              </span>
                            )}
                          </div>
                          <p className="text-sm font-medium text-gray-900 mb-1 line-clamp-2">
                            {item.question}
                          </p>
                          <p className="text-xs text-gray-600 line-clamp-3">
                            {item.answer}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-8 text-center">
                      <History className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                      <p className="text-sm text-gray-500">No questions yet</p>
                    </div>
                  )}
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