import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { signUp, confirmSignUp, signInWithRedirect } from 'aws-amplify/auth';

const Signup = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [confirmationCode, setConfirmationCode] = useState('');
    const [needsConfirmation, setNeedsConfirmation] = useState(false);
    const navigate = useNavigate();

    const handleSignUp = async (e) => {
        e.preventDefault();
        if (password !== confirmPassword) {
            alert("Passwords don't match");
            return;
        }
        try {
            const { isSignUpComplete, userId, nextStep } = await signUp({
                username: email,
                password,
                options: {
                    userAttributes: {
                        email,
                    },
                },
            });
            console.log('Sign up success:', userId);
            if (nextStep.signUpStep === 'CONFIRM_SIGN_UP') {
                setNeedsConfirmation(true);
            }
        } catch (error) {
            console.error('Error signing up:', error);
            alert(`Error signing up: ${error.message}`);
        }
    };

    const handleConfirmSignUp = async (e) => {
        e.preventDefault();
        try {
            const { isSignUpComplete, nextStep } = await confirmSignUp({
                username: email,
                confirmationCode,
            });
            console.log('Confirm sign up success');
            if (isSignUpComplete) {
                navigate('/login');
            }
        } catch (error) {
            console.error('Error confirming sign up:', error);
            alert(`Error confirming sign up: ${error.message}`);
        }
    };

    const handleGoogleSignup = async () => {
        try {
            await signInWithRedirect({ provider: 'Google' });
        } catch (error) {
            console.error('Error signing up with Google:', error);
        }
    };

    if (needsConfirmation) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
                <div className="max-w-md w-full space-y-8">
                    <div>
                        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                            Confirm your account
                        </h2>
                        <p className="mt-2 text-center text-sm text-gray-600">
                            We sent a code to {email}
                        </p>
                    </div>
                    <form className="mt-8 space-y-6" onSubmit={handleConfirmSignUp}>
                        <div className="rounded-md shadow-sm -space-y-px">
                            <div>
                                <label htmlFor="confirmation-code" className="sr-only">
                                    Confirmation Code
                                </label>
                                <input
                                    id="confirmation-code"
                                    name="code"
                                    type="text"
                                    required
                                    className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                    placeholder="Confirmation Code"
                                    value={confirmationCode}
                                    onChange={(e) => setConfirmationCode(e.target.value)}
                                />
                            </div>
                        </div>

                        <div>
                            <button
                                type="submit"
                                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                            >
                                Confirm
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                        Create your account
                    </h2>
                    <p className="mt-2 text-center text-sm text-gray-600">
                        Or{' '}
                        <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
                            sign in to existing account
                        </Link>
                    </p>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleSignUp}>
                    <div className="rounded-md shadow-sm -space-y-px">
                        <div>
                            <label htmlFor="email-address" className="sr-only">
                                Email address
                            </label>
                            <input
                                id="email-address"
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                placeholder="Email address"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="sr-only">
                                Password
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                autoComplete="new-password"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                        <div>
                            <label htmlFor="confirm-password" className="sr-only">
                                Confirm Password
                            </label>
                            <input
                                id="confirm-password"
                                name="confirm-password"
                                type="password"
                                autoComplete="new-password"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                placeholder="Confirm Password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                            Sign up
                        </button>
                    </div>
                </form>

                <div className="mt-6">
                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-300" />
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-2 bg-gray-50 text-gray-500">Or continue with</span>
                        </div>
                    </div>

                    <div className="mt-6">
                        <button
                            onClick={handleGoogleSignup}
                            className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                            <img
                                className="h-5 w-5 mr-2"
                                src="https://www.svgrepo.com/show/475656/google-color.svg"
                                alt="Google logo"
                            />
                            Sign up with Google
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Signup;
