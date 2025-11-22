import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthService } from '../services/AuthService';
import YouTubeInput from '../components/YouTubeInput';
import toast from 'react-hot-toast';

const Dashboard = () => {
    const [userEmail, setUserEmail] = useState('');
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
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
        try {
            const response = await fetch('http://localhost:8000/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url, user_id: userEmail }),
            });

            if (!response.ok) {
                throw new Error('Analysis failed');
            }

            const data = await response.json();
            console.log('Success:', data);
            toast.success(data.message || 'Video downloaded successfully!');
            fetchVideos(); // Refresh list after download
        } catch (error) {
            console.error('Error:', error);
            toast.error('Error analyzing video. Please try again.');
        } finally {
            setProcessing(false);
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
                                <p className="text-gray-600">Downloading video...</p>
                            </div>
                        )}

                        {/* Video List */}
                        <div className="w-full max-w-4xl">
                            <h2 className="text-2xl font-bold text-gray-900 mb-4">Downloaded Videos</h2>
                            {videos.length === 0 ? (
                                <p className="text-gray-500">No videos downloaded yet.</p>
                            ) : (
                                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                    {videos.map((video, index) => (
                                        <div key={index} className="bg-white overflow-hidden shadow rounded-lg">
                                            <div className="px-4 py-5 sm:p-6">
                                                <h3 className="text-lg leading-6 font-medium text-gray-900 truncate" title={video}>
                                                    {video}
                                                </h3>
                                                {/* Placeholder for video player or actions */}
                                                <div className="mt-2 max-w-xl text-sm text-gray-500">
                                                    <p>Video file available locally.</p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
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
