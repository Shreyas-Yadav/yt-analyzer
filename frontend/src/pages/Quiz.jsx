import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import TranscriptSidebar from '../components/TranscriptSidebar';
import { AuthService } from '../services/AuthService';
import { API_BASE_URL } from '../config/api';

const Quiz = () => {
    const { videoId } = useParams();
    const navigate = useNavigate();
    const [videoTitle, setVideoTitle] = useState('');
    const [selectedTranscript, setSelectedTranscript] = useState(null);
    const [quiz, setQuiz] = useState([]);
    const [loading, setLoading] = useState(false);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [selectedAnswers, setSelectedAnswers] = useState({});
    const [showResults, setShowResults] = useState(false);
    const [savedQuizzes, setSavedQuizzes] = useState([]);

    const fetchVideoDetails = async () => {
        try {
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';
            const response = await fetch(`${API_BASE_URL}/videos?user_id=${userEmail}`);
            const data = await response.json();
            const video = data.videos.find(v => v.id === parseInt(videoId));
            if (video) {
                setVideoTitle(video.title);
            }
        } catch (error) {
            console.error('Error fetching video:', error);
        }
    };

    const fetchSavedQuizzes = async () => {
        try {
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';
            const response = await fetch(`${API_BASE_URL}/videos/${videoId}/quizzes?user_id=${userEmail}`);
            if (response.ok) {
                const data = await response.json();
                setSavedQuizzes(data.quizzes || []);
            }
        } catch (error) {
            console.error('Error fetching saved quizzes:', error);
        }
    };

    useEffect(() => {
        if (videoId) {
            fetchVideoDetails();
            fetchSavedQuizzes();
        }
    }, [videoId]);

    const loadSavedQuiz = async (quizId) => {
        setLoading(true);
        try {
            // Add 3 second delay for testing loading animation
            await new Promise(resolve => setTimeout(resolve, 3000));

            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';
            const response = await fetch(`${API_BASE_URL}/quiz/${quizId}/content?user_id=${userEmail}`);

            if (!response.ok) {
                throw new Error('Failed to load quiz');
            }

            const data = await response.json();
            setQuiz(data.quiz);
            setCurrentQuestionIndex(0);
            setSelectedAnswers({});
            setShowResults(false);
            toast.success('Loaded saved quiz!');
        } catch (error) {
            console.error('Error loading quiz:', error);
            toast.error('Failed to load quiz');
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateQuiz = async () => {
        if (!selectedTranscript) {
            toast.error('Please select a transcript first');
            return;
        }

        setLoading(true);
        toast.loading(`Generating quiz in ${selectedTranscript.language}...`);

        try {
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';

            const response = await fetch(`${API_BASE_URL}/quiz/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_id: parseInt(videoId),
                    language: selectedTranscript.language,
                    user_id: userEmail
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Generation failed');
            }

            const data = await response.json();

            if (data.quiz && data.quiz.length > 0) {
                setQuiz(data.quiz);
                setCurrentQuestionIndex(0);
                setSelectedAnswers({});
                setShowResults(false);
                toast.dismiss();
                toast.success(`Generated ${data.quiz.length} questions!`);
            } else {
                toast.dismiss();
                toast.error('No questions were generated.');
            }

        } catch (error) {
            console.error('Error:', error);
            toast.dismiss();
            toast.error(`Failed to generate quiz: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveQuiz = async () => {
        if (quiz.length === 0) {
            toast.error('No quiz to save');
            return;
        }

        try {
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';

            const response = await fetch(`${API_BASE_URL}/quiz/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_id: parseInt(videoId),
                    user_id: userEmail,
                    language: selectedTranscript.language,
                    quiz: quiz
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to save quiz');
            }

            toast.success('Quiz saved successfully!');
            // Refresh the saved quizzes list
            await fetchSavedQuizzes();
        } catch (error) {
            console.error('Error saving quiz:', error);
            toast.error('Failed to save quiz');
        }
    };

    const handleDeleteQuiz = async (quizId) => {
        if (!window.confirm('Are you sure you want to delete this quiz?')) {
            return;
        }

        try {
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';
            const response = await fetch(`${API_BASE_URL}/quiz/${quizId}?user_id=${userEmail}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error('Failed to delete quiz');
            }

            toast.success('Quiz deleted!');
            // Refresh the list
            await fetchSavedQuizzes();
            // Clear current quiz if we deleted the one being viewed
            if (quiz.length > 0) {
                setQuiz([]);
                setSelectedAnswers({});
                setShowResults(false);
            }
        } catch (error) {
            console.error('Error deleting quiz:', error);
            toast.error('Failed to delete quiz');
        }
    };

    const handleAnswerSelect = (answer) => {
        if (showResults) return; // Don't allow changes after showing results

        setSelectedAnswers({
            ...selectedAnswers,
            [currentQuestionIndex]: answer
        });
    };

    const handleNext = () => {
        if (currentQuestionIndex < quiz.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
        }
    };

    const handlePrevious = () => {
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex(currentQuestionIndex - 1);
        }
    };

    const handleSubmit = () => {
        setShowResults(true);
        const correct = quiz.filter((q, idx) => selectedAnswers[idx] === q.correct_answer).length;
        toast.success(`You scored ${correct} out of ${quiz.length}!`);
    };

    const getScore = () => {
        return quiz.filter((q, idx) => selectedAnswers[idx] === q.correct_answer).length;
    };

    const getLanguageName = (code) => {
        try {
            return new Intl.DisplayNames(['en'], { type: 'language' }).of(code);
        } catch (error) {
            return code;
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            <nav className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center">
                            <button
                                onClick={() => navigate('/dashboard')}
                                className="text-indigo-600 hover:text-indigo-800 font-medium"
                            >
                                ← Back to Dashboard
                            </button>
                        </div>
                        <div className="flex items-center">
                            <h1 className="text-xl font-bold text-gray-900">Quiz</h1>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <div className="flex gap-6">
                    {/* Sidebar - Always show */}
                    <div className="w-1/3 space-y-6">
                        {/* Transcript Selection */}
                        <TranscriptSidebar
                            videoId={videoId}
                            userEmail={AuthService.getUser()?.email || 'anonymous'}
                            onSelect={setSelectedTranscript}
                            selectedTranscriptId={selectedTranscript?.id}
                        />

                        {/* Saved Quizzes List */}
                        {Array.isArray(savedQuizzes) && savedQuizzes.length > 0 && (
                            <div className="bg-white shadow rounded-lg p-4">
                                <h3 className="text-lg font-medium text-gray-900 mb-4">Saved Quizzes</h3>
                                <div className="space-y-2">
                                    {savedQuizzes.map((q) => (
                                        <div
                                            key={q.id}
                                            className="p-3 rounded-md border border-gray-200 hover:bg-gray-50 transition-colors flex justify-between items-center"
                                        >
                                            <button
                                                onClick={() => loadSavedQuiz(q.id)}
                                                className="flex-1 text-left flex justify-between items-center"
                                            >
                                                <span className="font-medium text-gray-700">
                                                    {getLanguageName(q.language)}
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    {new Date(q.created_at).toLocaleDateString()}
                                                </span>
                                            </button>
                                            <button
                                                onClick={() => handleDeleteQuiz(q.id)}
                                                className="ml-2 p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                                                title="Delete"
                                            >
                                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Main Content */}
                    <div className="flex-1 px-4 py-6 sm:px-0">
                        <div className="mb-6">
                            <h2 className="text-2xl font-bold text-gray-900 mb-2">{videoTitle}</h2>
                            <p className="text-gray-600">Test your knowledge with a quiz from the video transcript</p>
                        </div>

                        <div className="bg-white shadow rounded-lg p-8 text-center mb-6">
                            <div className="mb-6">
                                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                                </svg>
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">
                                {quiz.length > 0 ? 'Regenerate Quiz' : 'No quiz yet'}
                            </h3>
                            <p className="text-gray-600 mb-6">
                                {selectedTranscript
                                    ? `Generate a quiz from the ${selectedTranscript.language} transcript`
                                    : "Select a transcript or load a saved quiz"}
                            </p>

                            <button
                                onClick={handleGenerateQuiz}
                                disabled={loading || !selectedTranscript}
                                className="bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Generating...' : '✏️ Generate Quiz'}
                            </button>
                        </div>

                        {loading && (
                            <div className="bg-white shadow rounded-lg p-12 text-center">
                                <div className="flex flex-col items-center justify-center">
                                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mb-4"></div>
                                    <p className="text-gray-600">Loading quiz...</p>
                                </div>
                            </div>
                        )}

                        {!loading && quiz.length > 0 && (
                            <div className="space-y-6">
                                {/* Quiz display area */}
                                <div className="max-w-2xl mx-auto">
                                    <div className="mb-4 flex justify-between items-center text-sm text-gray-500">
                                        <span>Question {currentQuestionIndex + 1} of {quiz.length}</span>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={handleSaveQuiz}
                                                className="text-indigo-600 hover:text-indigo-800 font-medium"
                                            >
                                                Save Quiz
                                            </button>
                                            <button
                                                onClick={() => {
                                                    setQuiz([]);
                                                    setSelectedAnswers({});
                                                    setShowResults(false);
                                                }}
                                                className="text-gray-600 hover:text-gray-800"
                                            >
                                                Clear & Select New
                                            </button>
                                        </div>
                                    </div>

                                    {/* Question Card */}
                                    <div className="bg-white shadow-xl rounded-xl p-8 mb-6 border-2 border-indigo-100">
                                        <h3 className="text-xl font-semibold text-gray-900 mb-6">
                                            {quiz[currentQuestionIndex].question}
                                        </h3>

                                        <div className="space-y-3">
                                            {quiz[currentQuestionIndex].options.map((option, idx) => {
                                                const isSelected = selectedAnswers[currentQuestionIndex] === idx;
                                                const isCorrect = idx === quiz[currentQuestionIndex].correct_answer;
                                                const showCorrect = showResults && isCorrect;
                                                const showIncorrect = showResults && isSelected && !isCorrect;

                                                return (
                                                    <button
                                                        key={idx}
                                                        onClick={() => handleAnswerSelect(idx)}
                                                        disabled={showResults}
                                                        className={`w-full text-left p-4 rounded-lg border-2 transition-all ${showCorrect
                                                            ? 'bg-green-50 border-green-500'
                                                            : showIncorrect
                                                                ? 'bg-red-50 border-red-500'
                                                                : isSelected
                                                                    ? 'bg-indigo-50 border-indigo-500'
                                                                    : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                                                            } ${showResults ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                                                    >
                                                        <div className="flex items-center justify-between">
                                                            <span className="font-medium text-gray-900">{option}</span>
                                                            {showCorrect && <span className="text-green-600">✓ Correct</span>}
                                                            {showIncorrect && <span className="text-red-600">✗ Wrong</span>}
                                                        </div>
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>

                                    {/* Navigation & Submit */}
                                    <div className="flex justify-between items-center">
                                        <button
                                            onClick={handlePrevious}
                                            disabled={currentQuestionIndex === 0}
                                            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                                        >
                                            Previous
                                        </button>

                                        {!showResults && currentQuestionIndex === quiz.length - 1 && (
                                            <button
                                                onClick={handleSubmit}
                                                className="px-6 py-2 bg-green-600 text-white rounded-md shadow-sm text-sm font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                                            >
                                                Submit Quiz
                                            </button>
                                        )}

                                        {showResults && (
                                            <div className="text-center">
                                                <span className="text-lg font-bold text-indigo-600">
                                                    Score: {getScore()}/{quiz.length}
                                                </span>
                                            </div>
                                        )}

                                        <button
                                            onClick={handleNext}
                                            disabled={currentQuestionIndex === quiz.length - 1}
                                            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                                        >
                                            Next
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Quiz;
