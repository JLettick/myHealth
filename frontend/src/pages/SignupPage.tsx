/**
 * Signup page component.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { SignupForm } from '../components/auth/SignupForm';
import type { SignupData } from '../types/auth';

/**
 * Signup page with registration form.
 */
export function SignupPage(): JSX.Element {
  const { signup, isLoading, error, clearError } = useAuth();
  const navigate = useNavigate();
  const [showConfirmation, setShowConfirmation] = useState(false);

  const handleSubmit = async (data: SignupData) => {
    try {
      await signup(data);
      // If we get here without being authenticated, email confirmation is required
      setShowConfirmation(true);
      // Otherwise, the auth context will update and we redirect
      navigate('/dashboard', { replace: true });
    } catch {
      // Error is handled by the auth context
    }
  };

  if (showConfirmation) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md text-center">
          <div className="text-5xl mb-4">&#9993;</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Check Your Email
          </h1>
          <p className="text-gray-600 mb-6">
            We've sent you a confirmation link. Please check your email to
            activate your account.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Create Account</h1>
          <p className="text-gray-600 mt-2">Start your health journey today</p>
        </div>
        <SignupForm
          onSubmit={handleSubmit}
          isLoading={isLoading}
          error={error}
          onClearError={clearError}
        />
      </div>
    </div>
  );
}
