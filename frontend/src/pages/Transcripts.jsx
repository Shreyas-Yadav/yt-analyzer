import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import LanguageSelector from '../components/LanguageSelector';
import { AuthService } from '../services/AuthService';

const Transcripts = () => {
    const { videoId } = useParams();
    const navigate = useNavigate();
    const [videoTitle, setVideoTitle] = useState('');
    const [transcripts, setTranscripts] = useState([]);
    const [selectedLanguage, setSelectedLanguage] = useState('en');
    const [loading, setLoading] = useState(false);
    const [fetchingTranscripts, setFetchingTranscripts] = useState(true);

    useEffect(() => {
        fetchVideoDetails();
        fetchTranscripts();
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

    const fetchTranscripts = async () => {
        try {
            setFetchingTranscripts(true);
            const user = AuthService.getUser();
            const userEmail = user ? user.email : 'anonymous';
            const response = await fetch(
                `http://localhost:8000/videos/${videoId}/transcripts?user_id=${userEmail}`
            );
            const data = await response.json();
            setTranscripts(data.transcripts || []);
        } catch (error) {
            console.error('Error fetching transcripts:', error);
            toast.error('Failed to load transcripts');
        } finally {
            setFetchingTranscripts(false);
        }
    };

    const handleGenerateTranslation = async () => {
        // Check if translation already exists
        const existingTranslation = transcripts.find(t => t.language === selectedLanguage);
        if (existingTranslation) {
            toast.error(`Translation for ${selectedLanguage} already exists!`);
            return;
        }

        setLoading(true);
        toast.loading(`Generating ${selectedLanguage} translation...`);

        try {
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
            toast.dismiss();
            toast.success(`Transcript translated to ${selectedLanguage}`);

            // Refresh transcripts list
            fetchTranscripts();
        } catch (error) {
            console.error('Error:', error);
            toast.dismiss();
            toast.error('Failed to generate translation');
        } finally {
            setLoading(false);
        }
    };

    const getLanguageName = (code) => {
        const languageNames = {
            'en': '🇬🇧 English',
            'es': '🇪🇸 Spanish',
            'fr': '🇫🇷 French',
            'de': '🇩🇪 German',
            'it': '🇮🇹 Italian',
            'pt': '🇵🇹 Portuguese',
            'hi': '🇮🇳 Hindi',
            'ja': '🇯🇵 Japanese',
            'zh-CN': '🇨🇳 Chinese (Simplified)',
            'zh-TW': '🇹🇼 Chinese (Traditional)',
            'zh': '🇨🇳 Chinese',
            'ru': '🇷🇺 Russian',
            'ko': '🇰🇷 Korean',
            'ar': '🇸🇦 Arabic',
            'nl': '🇳🇱 Dutch',
            'tr': '🇹🇷 Turkish',
            'pl': '🇵🇱 Polish',
            'vi': '🇻🇳 Vietnamese',
            'th': '🇹🇭 Thai',
        };
        return languageNames[code] || `🌍 ${code.toUpperCase()}`;
    };

    // Helper to check if transcript is original (first one created for video)
    const isOriginalTranscript = (transcript, allTranscripts) => {
        // Find the earliest transcript for this video
        const sortedTranscripts = [...allTranscripts].sort((a, b) =>
            new Date(a.created_at) - new Date(b.created_at)
        );
        return sortedTranscripts[0]?.id === transcript.id;
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
                            <h1 className="text-xl font-bold text-gray-900">Transcripts</h1>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
                <div className="px-4 py-6 sm:px-0">
                    <div className="mb-6">
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">{videoTitle}</h2>
                        <p className="text-gray-600">Manage and generate transcripts in different languages</p>
                    </div>

                    {/* Generate New Translation Section */}
                    <div className="bg-white shadow rounded-lg p-6 mb-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Generate New Translation</h3>
                        <div className="flex gap-4 items-end">
                            <div className="flex-1">
                                <LanguageSelector
                                    selectedLanguage={selectedLanguage}
                                    onLanguageChange={setSelectedLanguage}
                                    disabled={loading}
                                />
                            </div>
                            <button
                                onClick={handleGenerateTranslation}
                                disabled={loading}
                                className="bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
                            >
                                {loading ? 'Generating...' : '🌍 Generate Translation'}
                            </button>
                        </div>
                    </div>

                    {/* Available Transcripts Section */}
                    <div className="bg-white shadow rounded-lg p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Transcripts</h3>

                        {fetchingTranscripts ? (
                            <div className="text-center py-8 text-gray-500">Loading transcripts...</div>
                        ) : transcripts.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">
                                No transcripts available yet. Generate one to get started!
                            </div>
                        ) : (
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                {transcripts.map((transcript) => (
                                    <div
                                        key={transcript.id}
                                        className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-md transition-all"
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-2xl">
                                                {isOriginalTranscript(transcript, transcripts) ? '🎬' : '🌍'}
                                            </span>
                                            <span className={`px-2 py-1 text-xs rounded-full ${isOriginalTranscript(transcript, transcripts)
                                                    ? 'bg-blue-100 text-blue-800'
                                                    : 'bg-green-100 text-green-800'
                                                }`}>
                                                {isOriginalTranscript(transcript, transcripts) ? 'Original' : 'Translation'}
                                            </span>
                                        </div>
                                        <h4 className="font-semibold text-gray-900 mb-1">
                                            {getLanguageName(transcript.language)}
                                        </h4>
                                        <p className="text-xs text-gray-500">
                                            Created: {new Date(transcript.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Transcripts;
