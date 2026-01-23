/**
 * Login page component.
 */

import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LoginForm } from '../components/auth/LoginForm';
import type { LoginData } from '../types/auth';

interface LocationState {
  from?: { pathname: string };
}

/**
 * Login page with form.
 */
export function LoginPage(): JSX.Element {
  const { login, isLoading, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Get the page user was trying to access before redirect
  const state = location.state as LocationState;
  const from = state?.from?.pathname || '/dashboard';

  const handleSubmit = async (data: LoginData) => {
    try {
      await login(data);
      // Redirect to intended page or dashboard
      navigate(from, { replace: true });
    } catch {
      // Error is handled by the auth context
    }
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Welcome Back</h1>
          <p className="text-gray-600 mt-2">Sign in to your account</p>
        </div>
        <LoginForm
          onSubmit={handleSubmit}
          isLoading={isLoading}
          error={error}
          onClearError={clearError}
        />
      </div>
    </div>
  );
}
