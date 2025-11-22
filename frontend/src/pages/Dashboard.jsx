import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser, fetchUserAttributes, signOut } from 'aws-amplify/auth';
import { Hub } from 'aws-amplify/utils';

const Dashboard = () => {
    const [userEmail, setUserEmail] = useState('');
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const unsubscribe = Hub.listen('auth', ({ payload }) => {
            switch (payload.event) {
                case 'signInWithRedirect':
                    checkUser();
                    break;
                case 'signInWithRedirect_failure':
                    console.error('Sign in failure', payload.data);
                    navigate('/login');
                    break;
                case 'signedOut':
                    navigate('/login');
                    break;
            }
        });

        checkUser();

        return unsubscribe;
    }, []);

    const checkUser = async () => {
        try {
            const user = await getCurrentUser();
            const attributes = await fetchUserAttributes();
            setUserEmail(attributes.email);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching user:', error);
            // Only redirect if we are not in the middle of a redirect flow?
            // Actually, if getCurrentUser fails, we are likely not logged in.
            // But let's give it a moment if it's a redirect.
            // However, Hub should catch the success event.
            // We'll set loading to false and redirect if error persists.
            setLoading(false);
            // navigate('/login'); // Don't redirect immediately, let the user see the error or wait for Hub?
            // Better: if error, redirect. But maybe the error is "No current user" which is valid if not logged in.
            if (error.name !== 'UserUnAuthenticatedException') { // Check specific error if possible
                navigate('/login');
            }
        }
    };

    const handleSignOut = async () => {
        try {
            await signOut();
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
                                Hello, {userEmail || 'User'}
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
