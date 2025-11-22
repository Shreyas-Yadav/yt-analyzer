import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthService } from '../services/AuthService';
import YouTubeInput from '../components/YouTubeInput';
import toast from 'react-hot-toast';

const Dashboard = () => {
    const [userEmail, setUserEmail] = useState('');
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    const [currentStage, setCurrentStage] = useState('Initializing...');
    const [videos, setVideos] = useState([]);
    const navigate = useNavigate();

    const fetchVideos = async () => {
        if (!userEmail) return;
        try {
            const response = await fetch(`http://localhost:8000/videos?user_id=${userEmail}`);
            if (response.ok) {
                const data = await response.json();
                setVideos(data.videos);
            }
        } catch (error) {
            console.error('Error fetching videos:', error);
        }
    };

    const handleUrlSubmit = async (url) => {
        console.log('Submitted URL:', url);
        setProcessing(true);

        // Create EventSource for Server-Sent Events
        const eventSource = new EventSource(
            `http://localhost:8000/analyze?${new URLSearchParams({ url, user_id: userEmail })}`,
            { withCredentials: false }
        );

        // Handle incoming messages
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('SSE Event:', data);

            if (data.stage === 1) {
                setCurrentStage('Stage 1/3: Downloading video...');
            } else if (data.stage === 2) {
                setCurrentStage('Stage 2/3: Extracting audio...');
            } else if (data.stage === 3) {
                setCurrentStage('Stage 3/3: Generating transcript...');
            } else if (data.stage === 'complete') {
                toast.success('Video analyzed successfully! Transcript ready.');
                fetchVideos();
                eventSource.close();
                setProcessing(false);
            } else if (data.stage === 'error') {
                toast.error(`Error: ${data.message}`);
                eventSource.close();
                setProcessing(false);
            }
        };

        // Handle errors
        eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            toast.error('Error analyzing video. Please try again.');
            eventSource.close();
            setProcessing(false);
        };
    };


    const handleDelete = async (videoId) => {
        if (!confirm('Are you sure you want to delete this video and all related files?')) return;

        try {
            const response = await fetch(`http://localhost:8000/videos/${videoId}?user_id=${userEmail}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                toast.success('Video deleted successfully');
                fetchVideos();
            } else {
                throw new Error('Failed to delete video');
            }
        } catch (error) {
            console.error('Error deleting video:', error);
            toast.error('Error deleting video');
        }
    };


    useEffect(() => {
        checkUser();
    }, []);

    useEffect(() => {
        if (userEmail) {
            fetchVideos();
        }
    }, [userEmail]);

    const checkUser = async () => {
        try {
            if (!AuthService.isAuthenticated()) {
                throw new Error('Not authenticated');
            }
            const user = AuthService.getUser();
            if (user && user.email) {
                setUserEmail(user.email);
            }
            setLoading(false);
        } catch (error) {
            console.error('Error fetching user:', error);
            navigate('/login');
        }
    };

    const handleSignOut = async () => {
        try {
            await AuthService.signOut();
            navigate('/login');
        } catch (error) {
            console.error('Error signing out:', error);
        }
    };

    if (loading) {
        return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
    }

    return (
        <div className="min-h-screen bg-gray-100">
            <nav className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center">
                            <h1 className="text-xl font-bold text-indigo-600">YT Analyzer</h1>
                        </div>
                        <div className="flex items-center">
                            <span className="mr-4 text-gray-700">
                                {userEmail || "Hello, User"}
                            </span>
                            <button
                                onClick={handleSignOut}
                                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                            >
                                Sign Out
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <div className="px-4 py-6 sm:px-0">
                    <div className="flex flex-col items-center justify-center space-y-8">
                        <YouTubeInput onSubmit={handleUrlSubmit} />

                        {processing && (
                            <div className="flex flex-col items-center space-y-2">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                                <p className="text-gray-600">{currentStage}</p>
                            </div>
                        )}

                        {/* Video List */}
                        <div className="w-full max-w-4xl">
                            <h2 className="text-2xl font-bold text-gray-900 mb-4">Analyzed Videos</h2>
                            {videos.length === 0 ? (
                                <p className="text-gray-500">No videos downloaded yet.</p>
                            ) : (
                                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                                    <ul className="divide-y divide-gray-200">
                                        {videos.map((video) => (
                                            <li key={video.id}>
                                                <div className="px-4 py-4 flex items-center justify-between sm:px-6">
                                                    <div className="flex-1 min-w-0">
                                                        <h3 className="text-lg font-medium text-indigo-600 truncate" title={video.title}>
                                                            {video.title}
                                                        </h3>
                                                        <p className="mt-1 text-sm text-gray-500">
                                                            Downloaded on {new Date(video.created_at).toLocaleDateString()}
                                                        </p>
                                                    </div>
                                                    <div className="ml-4 flex-shrink-0 flex items-center space-x-2">
                                                        <button
                                                            onClick={() => navigate(`/flashcards/${video.id}`)}
                                                            className="text-sm font-medium text-indigo-600 hover:text-indigo-800 px-3 py-1 rounded border border-indigo-600 hover:bg-indigo-50"
                                                            title="Generate Flashcards"
                                                        >
                                                            📚 Flashcards
                                                        </button>

                                                        <button
                                                            onClick={() => navigate(`/quiz/${video.id}`)}
                                                            className="text-sm font-medium text-purple-600 hover:text-purple-800 px-3 py-1 rounded border border-purple-600 hover:bg-purple-50"
                                                            title="Generate Quiz"
                                                        >
                                                            ✏️ Quiz
                                                        </button>

                                                        <button
                                                            onClick={() => handleDelete(video.id)}
                                                            className="font-medium text-red-600 hover:text-red-500"
                                                        >
                                                            Delete
                                                        </button>
                                                    </div>
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Dashboard;
