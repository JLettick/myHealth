/**
 * Login form component.
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { ErrorMessage } from '../common/ErrorMessage';
import { validateEmail } from '../../utils/validators';
import type { LoginData } from '../../types/auth';

interface LoginFormProps {
  onSubmit: (data: LoginData) => Promise<void>;
  isLoading: boolean;
  error: string | null;
  onClearError: () => void;
}

/**
 * Login form with email and password fields.
 */
export function LoginForm({
  onSubmit,
  isLoading,
  error,
  onClearError,
}: LoginFormProps): JSX.Element {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    onClearError();

    // Validate fields
    const errors: Record<string, string> = {};

    const emailValidation = validateEmail(email);
    if (!emailValidation.isValid) {
      errors.email = emailValidation.error!;
    }

    if (!password) {
      errors.password = 'Password is required';
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setFieldErrors({});
    await onSubmit({ email, password });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <ErrorMessage message={error} onDismiss={onClearError} />
      )}

      <Input
        label="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={fieldErrors.email}
        placeholder="you@example.com"
        autoComplete="email"
        disabled={isLoading}
      />

      <Input
        label="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={fieldErrors.password}
        placeholder="Enter your password"
        autoComplete="current-password"
        disabled={isLoading}
      />

      <Button
        type="submit"
        className="w-full"
        isLoading={isLoading}
        disabled={isLoading}
      >
        Sign In
      </Button>

      <p className="text-center text-sm text-gray-600">
        Don't have an account?{' '}
        <Link to="/signup" className="text-blue-600 hover:text-blue-800 font-medium">
          Sign up
        </Link>
      </p>
    </form>
  );
}
