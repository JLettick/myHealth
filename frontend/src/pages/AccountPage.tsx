import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useWhoop } from '../contexts/WhoopContext';
import { useGarmin } from '../contexts/GarminContext';
import { getProfile, updateProfile } from '../api/users';
import type { UserProfile } from '../api/users';

export function AccountPage(): JSX.Element {
  const { user } = useAuth();
  const { isConnected: whoopConnected } = useWhoop();
  const { isConnected: garminConnected } = useGarmin();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    async function fetchProfile() {
      try {
        const data = await getProfile();
        setProfile(data);
        setFullName(data.full_name || '');
      } catch {
        setMessage({ type: 'error', text: 'Failed to load profile.' });
      } finally {
        setLoading(false);
      }
    }
    fetchProfile();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const updated = await updateProfile({ full_name: fullName });
      setProfile(updated);
      setMessage({ type: 'success', text: 'Profile updated successfully.' });
    } catch {
      setMessage({ type: 'error', text: 'Failed to update profile.' });
    } finally {
      setSaving(false);
    }
  };

  const hasChanges = fullName !== (profile?.full_name || '');

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Account</h1>

      {/* Profile Section */}
      <div className="bg-white p-6 rounded-xl shadow-md mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile</h2>

        {message && (
          <div
            className={`mb-4 p-3 rounded-lg text-sm ${
              message.type === 'success'
                ? 'bg-green-50 text-green-700 border border-green-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}
          >
            {message.text}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              placeholder="Enter your name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <p className="text-gray-600 px-3 py-2 bg-gray-50 rounded-lg">
              {profile?.email || user?.email}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Member Since
            </label>
            <p className="text-gray-600 px-3 py-2 bg-gray-50 rounded-lg">
              {profile?.created_at
                ? new Date(profile.created_at).toLocaleDateString()
                : 'N/A'}
            </p>
          </div>

          <button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Connected Services Section */}
      <div className="bg-white p-6 rounded-xl shadow-md">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Connected Services
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <span className="text-gray-700 font-medium">Whoop</span>
            <span
              className={`text-sm font-medium px-2.5 py-0.5 rounded-full ${
                whoopConnected
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              {whoopConnected ? 'Connected' : 'Not Connected'}
            </span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-gray-700 font-medium">Garmin</span>
            <span
              className={`text-sm font-medium px-2.5 py-0.5 rounded-full ${
                garminConnected
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              {garminConnected ? 'Connected' : 'Not Connected'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
