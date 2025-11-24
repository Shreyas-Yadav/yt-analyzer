import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import LanguageSelector from '../components/LanguageSelector';
import TranscriptSidebar from '../components/TranscriptSidebar';
import { AuthService } from '../services/AuthService';

const Quiz = () => {
    const { videoId } = useParams();
    const navigate = useNavigate();
    const [videoTitle, setVideoTitle] = useState('');
    const [selectedTranscript, setSelectedTranscript] = useState(null);
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
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';
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
        if (!selectedTranscript) {
            toast.error('Please select a transcript first');
            return;
        }

        setLoading(true);
        toast.loading(`Generating quiz in ${selectedTranscript.language}...`);

        try {
            // Always call translate API to handle non-English videos
            // if (selectedLanguage !== 'en') {
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';
            const response = await fetch('http://localhost:8000/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_id: parseInt(videoId),
                    target_language: selectedTranscript.language,
                    user_id: userEmail
                }),
            });

            if (!response.ok) {
                throw new Error('Translation failed');
            }

            const data = await response.json();
            console.log('Translation result:', data);
            toast.success(`Transcript translated to ${selectedLanguage}`);

            // Placeholder for actual quiz generation
            setTimeout(() => {
                toast.dismiss();
                toast.info('Quiz generation coming soon!');
                setLoading(false);
            }, 1000);

        } catch (error) {
            console.error('Error:', error);
            toast.error('Failed to process request');
            setLoading(false);
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
                    {/* Sidebar */}
                    <TranscriptSidebar
                        videoId={videoId}
                        userEmail={AuthService.getUser()?.email || 'anonymous'}
                        onSelect={setSelectedTranscript}
                        selectedTranscriptId={selectedTranscript?.id}
                    />

                    {/* Main Content */}
                    <div className="flex-1 px-4 py-6 sm:px-0">
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
                                <p className="text-gray-600 mb-6">
                                    {selectedTranscript
                                        ? `Generate quiz from the ${selectedTranscript.language} transcript`
                                        : "Select a transcript from the sidebar to start"}
                                </p>

                                <button
                                    onClick={handleGenerateQuiz}
                                    disabled={loading || !selectedTranscript}
                                    className="bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
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
                </div>
            </main>
        </div>
    );
};

export default Quiz;
