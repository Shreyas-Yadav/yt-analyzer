import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthService } from '../services/AuthService';
import YouTubeInput from '../components/YouTubeInput';
import toast from 'react-hot-toast';
import { API_BASE_URL } from '../config/api';

const Dashboard = () => {
    const [userEmail, setUserEmail] = useState('');
    const [loading, setLoading] = useState(true);
    const [videos, setVideos] = useState([]);
    const navigate = useNavigate();

    const fetchVideos = async () => {
        if (!userEmail) return;
        try {
            const response = await fetch(`${API_BASE_URL}/videos?user_id=${userEmail}`);
            if (response.ok) {
                const data = await response.json();
                // Sort by created_at desc
                const sortedVideos = data.videos.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                setVideos(sortedVideos);
            }
        } catch (error) {
            console.error('Error fetching videos:', error);
        }
    };

    // Polling logic: Poll if any video is in 'queued' or 'processing' state
    useEffect(() => {
        const hasPending = videos.some(v => v.status === 'queued' || v.status === 'processing');
        let interval;
        if (hasPending) {
            interval = setInterval(fetchVideos, 3000);
        }
        return () => clearInterval(interval);
    }, [videos, userEmail]);

    const handleUrlSubmit = async (url) => {
        try {
            const response = await fetch(`${API_BASE_URL}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    user_id: userEmail
                })
            });

            if (!response.ok) {
                throw new Error('Failed to queue video');
            }

            toast.success('Video queued for processing');
            fetchVideos(); // Update list immediately

        } catch (error) {
            console.error('Error submitting video:', error);
            toast.error('Error submitting video');
        }
    };


    const handleDelete = async (videoId) => {
        if (!confirm('Are you sure you want to delete this video and all related files?')) return;

        try {
            const response = await fetch(`${API_BASE_URL}/videos/${videoId}?user_id=${userEmail}`, {
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

    const getStatusBadge = (status) => {
        switch (status) {
            case 'completed':
                return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Completed</span>;
            case 'processing':
                return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800 animate-pulse">Processing...</span>;
            case 'queued':
                return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">Queued</span>;
            case 'failed':
                return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Failed</span>;
            default:
                return null;
        }
    };

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
                                                        <div className="flex items-center space-x-2">
                                                            <h3 className="text-lg font-medium text-indigo-600 truncate" title={video.title}>
                                                                {video.title}
                                                            </h3>
                                                            {getStatusBadge(video.status)}
                                                        </div>
                                                        <p className="mt-1 text-sm text-gray-500">
                                                            Added on {new Date(video.created_at).toLocaleDateString()}
                                                        </p>
                                                    </div>
                                                    <div className="ml-4 flex-shrink-0 flex items-center space-x-2">
                                                        {video.status === 'completed' && (
                                                            <>
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
                                                                    onClick={() => navigate(`/transcripts/${video.id}`)}
                                                                    className="text-sm font-medium text-green-600 hover:text-green-800 px-3 py-1 rounded border border-green-600 hover:bg-green-50"
                                                                    title="Manage Transcripts"
                                                                >
                                                                    🌍 Transcripts
                                                                </button>
                                                            </>
                                                        )}

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
