import { useState, useEffect } from 'react';

const TranscriptSidebar = ({ videoId, userEmail, onSelect, selectedTranscriptId }) => {
    const [transcripts, setTranscripts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchTranscripts();
    }, [videoId]);

    const fetchTranscripts = async () => {
        try {
            setLoading(true);
            const response = await fetch(
                `http://localhost:8000/videos/${videoId}/transcripts?user_id=${userEmail}`
            );
            const data = await response.json();
            setTranscripts(data.transcripts || []);
        } catch (error) {
            console.error('Error fetching transcripts:', error);
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

    return (
        <div className="w-full bg-white shadow-lg rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                📝 Available Transcripts
            </h3>

            {loading ? (
                <div className="text-center text-gray-500">Loading...</div>
            ) : transcripts.length === 0 ? (
                <div className="text-center text-gray-500 text-sm">
                    No transcripts available
                </div>
            ) : (
                <ul className="space-y-2">
                    {transcripts.map((transcript) => (
                        <li
                            key={transcript.id}
                            onClick={() => onSelect && onSelect(transcript)}
                            className={`p-3 rounded-md border cursor-pointer transition-colors ${selectedTranscriptId === transcript.id
                                ? 'bg-indigo-50 border-indigo-500 ring-1 ring-indigo-500'
                                : 'bg-gray-50 border-gray-200 hover:bg-indigo-50 hover:border-indigo-300'
                                }`}
                        >
                            <div className="font-medium text-gray-900 text-sm">
                                {getLanguageName(transcript.language)}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                                {new Date(transcript.created_at).toLocaleDateString()}
                            </div>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default TranscriptSidebar;
