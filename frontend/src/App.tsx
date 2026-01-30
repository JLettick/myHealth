/**
 * Main App component with routing configuration.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { WhoopProvider } from './contexts/WhoopContext';
import { GarminProvider } from './contexts/GarminContext';
import { NutritionProvider } from './contexts/NutritionContext';
import { Layout } from './components/layout/Layout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { DashboardPage } from './pages/DashboardPage';
import { NutritionPage } from './pages/NutritionPage';
import { NotFoundPage } from './pages/NotFoundPage';

/**
 * Root App component.
 */
function App(): JSX.Element {
  return (
    <BrowserRouter>
      <AuthProvider>
        <WhoopProvider>
          <GarminProvider>
            <NutritionProvider>
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

              {/* 404 catch-all */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
              </Layout>
            </NutritionProvider>
          </GarminProvider>
        </WhoopProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
