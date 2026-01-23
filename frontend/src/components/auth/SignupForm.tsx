/**
 * Signup form component.
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { ErrorMessage } from '../common/ErrorMessage';
import {
  validateEmail,
  validatePassword,
  validatePasswordMatch,
  validateFullName,
} from '../../utils/validators';
import type { SignupData } from '../../types/auth';

interface SignupFormProps {
  onSubmit: (data: SignupData) => Promise<void>;
  isLoading: boolean;
  error: string | null;
  onClearError: () => void;
}

/**
 * Signup form with validation.
 */
export function SignupForm({
  onSubmit,
  isLoading,
  error,
  onClearError,
}: SignupFormProps): JSX.Element {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    onClearError();

    // Validate all fields
    const errors: Record<string, string> = {};

    const emailValidation = validateEmail(email);
    if (!emailValidation.isValid) {
      errors.email = emailValidation.error!;
    }

    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
      errors.password = passwordValidation.error!;
    }

    const matchValidation = validatePasswordMatch(password, confirmPassword);
    if (!matchValidation.isValid) {
      errors.confirmPassword = matchValidation.error!;
    }

    const nameValidation = validateFullName(fullName);
    if (!nameValidation.isValid) {
      errors.fullName = nameValidation.error!;
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setFieldErrors({});
    await onSubmit({
      email,
      password,
      full_name: fullName || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <ErrorMessage message={error} onDismiss={onClearError} />
      )}

      <Input
        label="Full Name"
        type="text"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        error={fieldErrors.fullName}
        placeholder="John Doe"
        autoComplete="name"
        disabled={isLoading}
      />

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
        placeholder="Create a strong password"
        autoComplete="new-password"
        disabled={isLoading}
      />

      <Input
        label="Confirm Password"
        type="password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        error={fieldErrors.confirmPassword}
        placeholder="Confirm your password"
        autoComplete="new-password"
        disabled={isLoading}
      />

      <div className="text-xs text-gray-500">
        Password must be at least 8 characters with uppercase, lowercase, number, and special character.
      </div>

      <Button
        type="submit"
        className="w-full"
        isLoading={isLoading}
        disabled={isLoading}
      >
        Create Account
      </Button>

      <p className="text-center text-sm text-gray-600">
        Already have an account?{' '}
        <Link to="/login" className="text-blue-600 hover:text-blue-800 font-medium">
          Sign in
        </Link>
      </p>
    </form>
  );
}
