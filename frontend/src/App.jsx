import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Landing from './pages/Landing';
import Analyze from './pages/Analyze';
import Results from './pages/Results';
import Chat from './pages/Chat';
import Benefits from './pages/Benefits';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

function RequireAuth({ children }) {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return children;
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Navbar />
          <main>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/analyze" element={<Analyze />} />
              <Route path="/results" element={<Results />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/benefits" element={<Benefits />} />
              <Route path="/login" element={<Login />} />
              <Route
                path="/dashboard"
                element={
                  <RequireAuth>
                    <Dashboard />
                  </RequireAuth>
                }
              />
            </Routes>
          </main>
          <Footer />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
