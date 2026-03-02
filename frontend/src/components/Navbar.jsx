import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const isActive = (path) => location.pathname === path ? 'nav-link active' : 'nav-link'

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  if (!user) return null

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        Doctor<span>Book</span>
      </Link>
      <div className="navbar-links">
        {user.role === 'patient' && (
          <>
            <Link to="/doctors" className={isActive('/doctors')}>Find Doctors</Link>
            <Link to="/appointments" className={isActive('/appointments')}>My Appointments</Link>
          </>
        )}
        {user.role === 'doctor' && (
          <>
            <Link to="/my-slots" className={isActive('/my-slots')}>My Slots</Link>
            <Link to="/appointments" className={isActive('/appointments')}>Appointments</Link>
          </>
        )}
        {user.role === 'admin' && (
          <>
            <Link to="/admin" className={isActive('/admin')}>
              Dashboard <span className="nav-badge">Admin</span>
            </Link>
            <Link to="/doctors" className={isActive('/doctors')}>Doctors</Link>
            <Link to="/appointments" className={isActive('/appointments')}>Appointments</Link>
          </>
        )}
        <button className="btn-logout" onClick={handleLogout}>Sign Out</button>
      </div>
    </nav>
  )
}
