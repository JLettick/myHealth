/**
 * Main App component with routing configuration.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { WhoopProvider } from './contexts/WhoopContext';
import { NutritionProvider } from './contexts/NutritionContext';
import { AgentProvider } from './contexts/AgentContext';
import { WorkoutProvider } from './contexts/WorkoutContext';
import { Layout } from './components/layout/Layout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { DashboardPage } from './pages/DashboardPage';
import { NutritionPage } from './pages/NutritionPage';
import { AgentPage } from './pages/AgentPage';
import { WorkoutPage } from './pages/WorkoutPage';
import { AccountPage } from './pages/AccountPage';
import { NotFoundPage } from './pages/NotFoundPage';

/**
 * Root App component.
 */
function App(): JSX.Element {
  return (
    <BrowserRouter>
      <AuthProvider>
        <WhoopProvider>
            <NutritionProvider>
              <AgentProvider>
                <WorkoutProvider>
                <Layout>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignupPage />} />

              {/* Protected routes */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/nutrition"
                element={
                  <ProtectedRoute>
                    <NutritionPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/agent"
                element={
                  <ProtectedRoute>
                    <AgentPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workout"
                element={
                  <ProtectedRoute>
                    <WorkoutPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/account"
                element={
                  <ProtectedRoute>
                    <AccountPage />
                  </ProtectedRoute>
                }
              />

              {/* 404 catch-all */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
                </Layout>
                </WorkoutProvider>
              </AgentProvider>
            </NutritionProvider>
        </WhoopProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
