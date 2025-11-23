import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import LanguageSelector from '../components/LanguageSelector';
import { AuthService } from '../services/AuthService';

const Flashcards = () => {
    const { videoId } = useParams();
    const navigate = useNavigate();
    const [videoTitle, setVideoTitle] = useState('');
    const [selectedLanguage, setSelectedLanguage] = useState('en');
    const [flashcards, setFlashcards] = useState([]);
    const [loading, setLoading] = useState(false);
    const [currentCardIndex, setCurrentCardIndex] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);

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

    const handleGenerateFlashcards = async () => {
        setLoading(true);
        toast.loading(`Generating flashcards in ${selectedLanguage}...`);

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
                    target_language: selectedLanguage,
                    user_id: userEmail
                }),
            });

            if (!response.ok) {
                throw new Error('Translation failed');
            }

            const data = await response.json();
            console.log('Translation result:', data);
            toast.success(`Transcript translated to ${selectedLanguage}`);

            // Placeholder for actual flashcard generation
            setTimeout(() => {
                toast.dismiss();
                toast.info('Flashcard generation coming soon!');
                setLoading(false);
            }, 1000);

        } catch (error) {
            console.error('Error:', error);
            toast.error('Failed to process request');
            setLoading(false);
        }
    };

    const handleFlip = () => {
        setIsFlipped(!isFlipped);
    };

    const handleNext = () => {
        if (currentCardIndex < flashcards.length - 1) {
            setCurrentCardIndex(currentCardIndex + 1);
            setIsFlipped(false);
        }
    };

    const handlePrevious = () => {
        if (currentCardIndex > 0) {
            setCurrentCardIndex(currentCardIndex - 1);
            setIsFlipped(false);
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
                            <h1 className="text-xl font-bold text-gray-900">Flashcards</h1>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
                <div className="px-4 py-6 sm:px-0">
                    <div className="mb-6">
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">{videoTitle}</h2>
                        <p className="text-gray-600">Generate flashcards from the video transcript</p>
                    </div>

                    {flashcards.length === 0 ? (
                        <div className="bg-white shadow rounded-lg p-8 text-center">
                            <div className="mb-6">
                                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">No flashcards yet</h3>
                            <p className="text-gray-600 mb-6">Select a language and click the button below to generate flashcards from the transcript</p>

                            <div className="mb-6 flex justify-center">
                                <LanguageSelector
                                    selectedLanguage={selectedLanguage}
                                    onLanguageChange={setSelectedLanguage}
                                    disabled={loading}
                                />
                            </div>

                            <button
                                onClick={handleGenerateFlashcards}
                                disabled={loading}
                                className="bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
                            >
                                {loading ? 'Generating...' : '📚 Generate Flashcards'}
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Flashcard display area - for future implementation */}
                            <div className="bg-white shadow rounded-lg p-8">
                                <p className="text-gray-600">Flashcard viewer coming soon...</p>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default Flashcards;
