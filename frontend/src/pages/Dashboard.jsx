import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthService } from '../services/AuthService';

const Dashboard = () => {
    const [userEmail, setUserEmail] = useState('');
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        checkUser();
    }, []);

    const checkUser = async () => {
        try {
            if (!AuthService.isAuthenticated()) {
                throw new Error('Not authenticated');
            }
            // Since we don't have a way to get attributes easily without an API call or decoding token,
            // we'll just use the stored email if we saved it, or decode the token.
            // For now, let's just show "User" or try to get it from localStorage if we saved it there.
            // In a real app, we'd decode the ID token.
            // Let's update AuthService to expose a way to get user details if possible, 
            // but for now we'll just check if we have tokens.

            // A better approach for "Hello, User" is to decode the idToken.
            // For this migration, I'll just set a placeholder or decode if I added a decoder.
            // I didn't add a decoder to AuthService. I'll just show "User" for now or 
            // if I want to be fancy, I could add a simple decode method to AuthService later.

            // Let's assume we are good if isAuthenticated returns true.
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
                                Hello, User
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
                    <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
                        <p className="text-gray-500 text-xl">Dashboard Content Goes Here</p>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Dashboard;
