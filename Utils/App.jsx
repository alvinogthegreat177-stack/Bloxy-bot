import { Toaster } from "@/components/ui/toaster"
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClientInstance } from '@/lib/query-client'
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import PageNotFound from '../lib/PageNotFound.jsx';
import { AuthProvider, useAuth } from '../lib/AuthContext.jsx';
import UserNotRegisteredError from '../components/UserNotRegisteredError.jsx';
import ScrollToTop from '../components/ScrollToTop.jsx';
import ProtectedRoute from '../components/ProtectedRoute.jsx';
import { LanguageProvider } from '../lib/LanguageContext.jsx';

import Login from '../pages/Login.jsx';
import Register from '../pages/Register.jsx';
import ForgotPassword from '../pages/ForgotPassword.jsx';
import ResetPassword from '../pages/ResetPassword.jsx';
import Home from '../pages/Home.jsx';
import SearchPage from '../pages/SearchPage.jsx';
import KnowledgePage from '../pages/KnowledgePage.jsx';
import Dashboard from '../pages/Dashboard.jsx';
import SettingsPage from '../pages/SettingsPage.jsx';
import AdminPage from '../pages/AdminPage.jsx';
import LibraryPage from '../pages/LibraryPage.jsx';

const AuthenticatedApp = () => {
  const { isLoadingAuth, isLoadingPublicSettings, authError, navigateToLogin } = useAuth();

  if (isLoadingPublicSettings || isLoadingAuth) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <img
            src="https://media.base44.com/images/public/6a415277171cff3034584f35/6f17cca71_image.png"
            alt="Bloxy-bot"
            className="w-12 h-12 rounded-xl animate-pulse"
          />
          <div className="w-6 h-6 border-2 border-orange-500/30 border-t-orange-500 rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (authError) {
    if (authError.type === 'user_not_registered') {
      return <UserNotRegisteredError />;
    } else if (authError.type === 'auth_required') {
      navigateToLogin();
      return null;
    }
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route element={<ProtectedRoute unauthenticatedElement={<Navigate to="/login" replace />} />}>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/library" element={<LibraryPage />} />
      </Route>
      <Route path="*" element={<PageNotFound />} />
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <LanguageProvider>
      <QueryClientProvider client={queryClientInstance}>
        <Router>
          <ScrollToTop />
          <AuthenticatedApp />
        </Router>
        <Toaster />
      </QueryClientProvider>
      </LanguageProvider>
    </AuthProvider>
  )
}

export default App
