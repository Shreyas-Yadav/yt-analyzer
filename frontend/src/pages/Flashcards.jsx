import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

import TranscriptSidebar from '../components/TranscriptSidebar';
import { AuthService } from '../services/AuthService';

const Flashcards = () => {
    const { videoId } = useParams();
    const navigate = useNavigate();
    const [videoTitle, setVideoTitle] = useState('');
    const [selectedTranscript, setSelectedTranscript] = useState(null);
    const [flashcards, setFlashcards] = useState([]);
    const [loading, setLoading] = useState(false);
    const [currentCardIndex, setCurrentCardIndex] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);
    const [savedFlashcards, setSavedFlashcards] = useState([]);

    console.log('Rendering Flashcards component', { videoId, savedFlashcards });

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

    const fetchSavedFlashcards = async () => {
        try {
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';
            const response = await fetch(`http://localhost:8000/videos/${videoId}/flashcards?user_id=${userEmail}`);
            if (response.ok) {
                const data = await response.json();
                console.log('Fetched saved flashcards:', data);
                setSavedFlashcards(data.flashcards || []);
            }
        } catch (error) {
            console.error('Error fetching saved flashcards:', error);
        }
    };

    useEffect(() => {
        if (videoId) {
            // Fetch video details
            fetchVideoDetails();
            // Fetch saved flashcards
            fetchSavedFlashcards();
        }
    }, [videoId]);

    const loadSavedFlashcards = async (flashcardId) => {
        setLoading(true);
        try {
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';
            const response = await fetch(`http://localhost:8000/flashcards/${flashcardId}/content?user_id=${userEmail}`);

            if (!response.ok) {
                throw new Error('Failed to load flashcards');
            }

            const data = await response.json();
            setFlashcards(data.flashcards);
            setCurrentCardIndex(0);
            setIsFlipped(false);
            toast.success('Loaded saved flashcards!');
        } catch (error) {
            console.error('Error loading flashcards:', error);
            toast.error('Failed to load flashcards');
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateFlashcards = async () => {
        if (!selectedTranscript) {
            toast.error('Please select a transcript first');
            return;
        }

        setLoading(true);
        toast.loading(`Generating flashcards in ${selectedTranscript.language}...`);

        try {
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';

            const response = await fetch('http://localhost:8000/flashcards/generate', {
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
            console.log('Flashcards generated:', data);

            if (data.flashcards && data.flashcards.length > 0) {
                setFlashcards(data.flashcards);
                setCurrentCardIndex(0);
                setIsFlipped(false);
                toast.dismiss();
                toast.success(`Generated ${data.flashcards.length} flashcards!`);
            } else {
                toast.dismiss();
                toast.error('No flashcards were generated.');
            }

        } catch (error) {
            console.error('Error:', error);
            toast.dismiss();
            toast.error(`Failed to generate flashcards: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveFlashcards = async () => {
        if (flashcards.length === 0) {
            toast.error('No flashcards to save');
            return;
        }

        try {
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';

            const response = await fetch('http://localhost:8000/flashcards/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_id: parseInt(videoId),
                    user_id: userEmail,
                    language: selectedTranscript.language,
                    flashcards: flashcards
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to save flashcards');
            }

            toast.success('Flashcards saved successfully!');
        } catch (error) {
            console.error('Error saving flashcards:', error);
            toast.error('Failed to save flashcards');
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
                            <h1 className="text-xl font-bold text-gray-900">Flashcards</h1>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <div className="flex gap-6">
                    {/* Sidebar - Show if no flashcards loaded OR if we want to show saved list */}
                    {flashcards.length === 0 && (
                        <div className="w-1/3 space-y-6">
                            {/* Transcript Selection */}
                            <TranscriptSidebar
                                videoId={videoId}
                                userEmail={AuthService.getUser()?.email || 'anonymous'}
                                onSelect={setSelectedTranscript}
                                selectedTranscriptId={selectedTranscript?.id}
                            />

                            {/* Saved Flashcards List */}
                            {Array.isArray(savedFlashcards) && savedFlashcards.length > 0 && (
                                <div className="bg-white shadow rounded-lg p-4">
                                    <h3 className="text-lg font-medium text-gray-900 mb-4">Saved Flashcards</h3>
                                    <div className="space-y-2">
                                        {savedFlashcards.map((fc) => (
                                            <button
                                                key={fc.id}
                                                onClick={() => loadSavedFlashcards(fc.id)}
                                                className="w-full text-left p-3 rounded-md border border-gray-200 hover:bg-gray-50 transition-colors flex justify-between items-center"
                                            >
                                                <span className="font-medium text-gray-700">
                                                    {getLanguageName(fc.language)}
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    {new Date(fc.created_at).toLocaleDateString()}
                                                </span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Main Content */}
                    <div className="flex-1 px-4 py-6 sm:px-0">
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
                                <p className="text-gray-600 mb-6">
                                    {selectedTranscript
                                        ? `Generate flashcards from the ${selectedTranscript.language} transcript`
                                        : "Select a transcript or load a saved set"}
                                </p>

                                <button
                                    onClick={handleGenerateFlashcards}
                                    disabled={loading || !selectedTranscript}
                                    className="bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                                >
                                    {loading ? 'Generating...' : '📚 Generate Flashcards'}
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                {/* Flashcard display area */}
                                <div className="max-w-2xl mx-auto">
                                    <div className="mb-4 flex justify-between items-center text-sm text-gray-500">
                                        <span>Card {currentCardIndex + 1} of {flashcards.length}</span>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={handleSaveFlashcards}
                                                className="text-indigo-600 hover:text-indigo-800 font-medium"
                                            >
                                                Save Flashcards
                                            </button>
                                            <button
                                                onClick={() => setFlashcards([])}
                                                className="text-gray-600 hover:text-gray-800"
                                            >
                                                Generate New
                                            </button>
                                        </div>
                                    </div>

                                    <div
                                        className="relative h-96 w-full cursor-pointer perspective-1000"
                                        onClick={handleFlip}
                                    >
                                        <div className={`relative w-full h-full transition-transform duration-500 transform-style-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
                                            {/* Front */}
                                            <div className="absolute w-full h-full bg-white shadow-xl rounded-xl p-8 flex flex-col items-center justify-center backface-hidden border-2 border-indigo-100">
                                                <span className="text-xs font-semibold text-indigo-500 uppercase tracking-wide mb-4">Question</span>
                                                <p className="text-2xl text-center font-medium text-gray-900">
                                                    {flashcards[currentCardIndex].front}
                                                </p>
                                                <p className="absolute bottom-6 text-sm text-gray-400">Click to flip</p>
                                            </div>

                                            {/* Back */}
                                            <div className="absolute w-full h-full bg-indigo-600 shadow-xl rounded-xl p-8 flex flex-col items-center justify-center backface-hidden rotate-y-180">
                                                <span className="text-xs font-semibold text-indigo-200 uppercase tracking-wide mb-4">Answer</span>
                                                <p className="text-xl text-center text-white">
                                                    {flashcards[currentCardIndex].back}
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-8 flex justify-center gap-4">
                                        <button
                                            onClick={handlePrevious}
                                            disabled={currentCardIndex === 0}
                                            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                                        >
                                            Previous
                                        </button>
                                        <button
                                            onClick={handleNext}
                                            disabled={currentCardIndex === flashcards.length - 1}
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

export default Flashcards;
