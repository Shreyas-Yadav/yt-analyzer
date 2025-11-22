import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const Quiz = () => {
    const { videoId } = useParams();
    const navigate = useNavigate();
    const [videoTitle, setVideoTitle] = useState('');
    const [quiz, setQuiz] = useState(null);
    const [loading, setLoading] = useState(false);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [selectedAnswers, setSelectedAnswers] = useState({});
    const [showResults, setShowResults] = useState(false);

    useEffect(() => {
        // Fetch video details
        fetchVideoDetails();
    }, [videoId]);

    const fetchVideoDetails = async () => {
        try {
            const userEmail = localStorage.getItem('userEmail') || 'anonymous';
            const response = await fetch(`http://localhost:8000/videos?user_id=${userEmail}`);
            const data = await response.json();
            const video = data.videos.find(v => v.id === parseInt(videoId));
            if (video) {
                setVideoTitle(video.title);
            }
        } catch (error) {
            console.error('Error fetching video:', error);
        }
    };

    const handleGenerateQuiz = async () => {
        setLoading(true);
        toast.loading('Generating quiz...');

        // Placeholder - will be replaced with actual API call
        setTimeout(() => {
            toast.dismiss();
            toast.info('Quiz generation coming soon!');
            setLoading(false);
        }, 1000);
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

            <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
                <div className="px-4 py-6 sm:px-0">
                    <div className="mb-6">
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">{videoTitle}</h2>
                        <p className="text-gray-600">Test your knowledge with a quiz from the video transcript</p>
                    </div>

                    {!quiz ? (
                        <div className="bg-white shadow rounded-lg p-8 text-center">
                            <div className="mb-6">
                                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                                </svg>
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">No quiz yet</h3>
                            <p className="text-gray-600 mb-6">Click the button below to generate a quiz from the transcript</p>
                            <button
                                onClick={handleGenerateQuiz}
                                disabled={loading}
                                className="bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
                            >
                                {loading ? 'Generating...' : '✏️ Generate Quiz'}
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Quiz display area - for future implementation */}
                            <div className="bg-white shadow rounded-lg p-8">
                                <p className="text-gray-600">Quiz viewer coming soon...</p>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default Quiz;
