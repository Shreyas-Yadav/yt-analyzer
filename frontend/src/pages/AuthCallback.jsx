import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AuthService } from '../services/AuthService';

const AuthCallback = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [error, setError] = useState(null);

    const processed = React.useRef(false);

    useEffect(() => {
        const code = searchParams.get('code');
        if (code) {
            if (processed.current) return;
            processed.current = true;
            handleCodeExchange(code);
        } else {
            setError('No authorization code found');
        }
    }, [searchParams]);

    const handleCodeExchange = async (code) => {
        try {
            await AuthService.handleCodeExchange(code);
            navigate('/');
        } catch (err) {
            console.error('Error exchanging code:', err);
            setError('Failed to sign in. Please try again.');
        }
    };

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <h2 className="text-2xl font-bold text-red-600 mb-4">Authentication Error</h2>
                    <p className="text-gray-600 mb-4">{error}</p>
                    <button
                        onClick={() => navigate('/login')}
                        className="text-indigo-600 hover:text-indigo-500 font-medium"
                    >
                        Back to Login
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="text-center">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Signing in...</h2>
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            </div>
        </div>
    );
};

export default AuthCallback;
