import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [form, setForm] = useState({ username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await authAPI.login(form)
      login(data)
      toast.success(`Welcome back, ${data.full_name}!`)
      if (data.role === 'admin') navigate('/admin')
      else if (data.role === 'doctor') navigate('/my-slots')
      else navigate('/doctors')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-side">
        <h1 className="auth-side-title">
          Your health,<br /><em>simplified.</em>
        </h1>
        <p className="auth-side-sub">
          Book appointments with top specialists, track your health history, and get reminded — all in one place.
        </p>
      </div>

      <div className="auth-form-wrap">
        <div className="auth-form-box">
          <div className="auth-logo">Doctor<span>Book</span></div>
          <h2 className="auth-title">Welcome back</h2>
          <p className="auth-sub">Sign in to your account</p>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input
                className="form-control"
                placeholder="your_username"
                value={form.username}
                onChange={e => setForm({ ...form, username: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-control"
                placeholder="••••••••"
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <div className="auth-footer">
            Don't have an account? <Link to="/register">Create one</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
