/**
 * Home page component.
 */

import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/common/Button';

/**
 * Public home page with app introduction.
 */
export function HomePage(): JSX.Element {
  const { isAuthenticated } = useAuth();

  return (
    <div className="text-center py-12">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">
        Welcome to myHealth
      </h1>
      <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
        Your personal health tracking companion. Monitor your wellness journey
        with ease and stay on top of your health goals.
      </p>

      {isAuthenticated ? (
        <Link to="/dashboard">
          <Button className="text-lg px-8 py-3">Go to Dashboard</Button>
        </Link>
      ) : (
        <div className="flex justify-center space-x-4">
          <Link to="/signup">
            <Button className="text-lg px-8 py-3">Get Started</Button>
          </Link>
          <Link to="/login">
            <Button variant="secondary" className="text-lg px-8 py-3">
              Sign In
            </Button>
          </Link>
        </div>
      )}

      <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="text-3xl mb-4">&#128202;</div>
          <h3 className="text-lg font-semibold mb-2">Track Progress</h3>
          <p className="text-gray-600">
            Monitor your health metrics and see your progress over time.
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="text-3xl mb-4">&#128274;</div>
          <h3 className="text-lg font-semibold mb-2">Secure & Private</h3>
          <p className="text-gray-600">
            Your health data is encrypted and securely stored.
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="text-3xl mb-4">&#128241;</div>
          <h3 className="text-lg font-semibold mb-2">Access Anywhere</h3>
          <p className="text-gray-600">
            Check your health data from any device, anytime.
          </p>
        </div>
      </div>
    </div>
  );
}
