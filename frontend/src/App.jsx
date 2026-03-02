import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'
import ChatBot from './components/ChatBot';
import Navbar from './components/Navbar'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DoctorsPage from './pages/DoctorsPage'
import AppointmentsPage from './pages/AppointmentsPage'
import MySlotsPage from './pages/MySlotsPage'
import AdminPage from './pages/AdminPage'

function PrivateRoute({ children, roles }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="loading-center"><div className="spinner"></div></div>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return children
}

function DefaultRedirect() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'admin') return <Navigate to="/admin" replace />
  if (user.role === 'doctor') return <Navigate to="/my-slots" replace />
  return <Navigate to="/doctors" replace />
}

function AppShell() {
  const { user } = useAuth()
  return (
    <div className="app-shell">
      <Navbar />
      <Routes>
        <Route path="/" element={<DefaultRedirect />} />
        <Route path="/login" element={user ? <DefaultRedirect /> : <LoginPage />} />
        <Route path="/register" element={user ? <DefaultRedirect /> : <RegisterPage />} />
        <Route path="/doctors" element={<PrivateRoute roles={['patient', 'admin']}><DoctorsPage /></PrivateRoute>} />
        <Route path="/appointments" element={<PrivateRoute><AppointmentsPage /></PrivateRoute>} />
        <Route path="/my-slots" element={<PrivateRoute roles={['doctor', 'admin']}><MySlotsPage /></PrivateRoute>} />
        <Route path="/admin" element={<PrivateRoute roles={['admin']}><AdminPage /></PrivateRoute>} />
        <Route path="*" element={<DefaultRedirect />} />
      </Routes>
      <ChatBot /> {/* <--- Add this line at the bottom */}
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppShell />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              fontFamily: 'DM Sans, sans-serif',
              borderRadius: '10px',
              fontSize: '14px',
              boxShadow: '0 8px 32px rgba(10,37,64,0.15)',
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  )
}
