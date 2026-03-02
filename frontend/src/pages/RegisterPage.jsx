import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const [form, setForm] = useState({
    full_name: '', username: '', email: '', password: '', phone: '', role: 'patient'
  })
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await authAPI.register(form)
      login(data)
      toast.success('Account created successfully!')
      if (data.role === 'doctor') navigate('/my-slots')
      else navigate('/doctors')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div className="auth-page">
      <div className="auth-side">
        <h1 className="auth-side-title">
          Join <em>thousands</em><br />of patients.
        </h1>
        <p className="auth-side-sub">
          Register as a patient to book appointments, or as a doctor to manage your availability and patients.
        </p>
      </div>

      <div className="auth-form-wrap">
        <div className="auth-form-box">
          <div className="auth-logo">Doctor<span>Book</span></div>
          <h2 className="auth-title">Create account</h2>
          <p className="auth-sub">Get started in seconds</p>

          <div className="role-selector">
            {[
              { value: 'patient', icon: '🏥', label: 'Patient' },
              { value: 'doctor', icon: '👨‍⚕️', label: 'Doctor' },
            ].map(r => (
              <div
                key={r.value}
                className={`role-option ${form.role === r.value ? 'selected' : ''}`}
                onClick={() => setForm({ ...form, role: r.value })}
              >
                <div className="role-option-icon">{r.icon}</div>
                <div className="role-option-label">{r.label}</div>
              </div>
            ))}
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-control" placeholder="Dr. Jane Doe" value={form.full_name} onChange={set('full_name')} required />
            </div>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input className="form-control" placeholder="jane_doe" value={form.username} onChange={set('username')} required />
            </div>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input type="email" className="form-control" placeholder="jane@example.com" value={form.email} onChange={set('email')} required />
            </div>
            <div className="form-group">
              <label className="form-label">Phone (optional)</label>
              <input className="form-control" placeholder="+1 555 000 0000" value={form.phone} onChange={set('phone')} />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input type="password" className="form-control" placeholder="At least 8 characters" value={form.password} onChange={set('password')} required minLength={6} />
            </div>
            <button type="submit" className="btn btn-teal" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
              {loading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>

          <div className="auth-footer">
            Already have an account? <Link to="/login">Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
