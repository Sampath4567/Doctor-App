import { useState, useEffect } from 'react'
import { doctorAPI, specAPI, userAPI, appointmentAPI } from '../services/api'
import toast from 'react-hot-toast'

function AddSpecModal({ onClose }) {
  const [form, setForm] = useState({ name: '', description: '', icon: '' })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await specAPI.create(form)
      toast.success('Specialization added!')
      onClose(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose(false)}>
      <div className="modal-box">
        <div className="modal-header">
          <span className="modal-title">Add Specialization</span>
          <button className="modal-close" onClick={() => onClose(false)}>×</button>
        </div>
        <div className="modal-body">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Name</label>
              <input className="form-control" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. Cardiology" required />
            </div>
            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea className="form-control" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} placeholder="Brief description…" />
            </div>
            <div className="form-group">
              <label className="form-label">Icon (emoji)</label>
              <input className="form-control" value={form.icon} onChange={e => setForm({ ...form, icon: e.target.value })} placeholder="❤️" maxLength={4} />
            </div>
            <button type="submit" className="btn btn-teal" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
              {loading ? 'Adding…' : 'Add Specialization'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

function AddDoctorModal({ specs, users, onClose }) {
  const [form, setForm] = useState({ user_id: '', specialization_id: '', bio: '', qualification: '', experience_years: 0, consultation_fee: 0 })
  const [loading, setLoading] = useState(false)

  // Filter out users who already have a doctor profile
  const doctorUsers = users.filter(u => u.role === 'doctor')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await doctorAPI.create({
        ...form,
        user_id: parseInt(form.user_id),
        specialization_id: parseInt(form.specialization_id),
        experience_years: parseInt(form.experience_years),
        consultation_fee: parseInt(form.consultation_fee),
      })
      toast.success('Doctor profile created!')
      onClose(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed')
    } finally { setLoading(false) }
  }

  const set = (k) => e => setForm({ ...form, [k]: e.target.value })

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose(false)}>
      <div className="modal-box">
        <div className="modal-header">
          <span className="modal-title">Add Doctor Profile</span>
          <button className="modal-close" onClick={() => onClose(false)}>×</button>
        </div>
        <div className="modal-body">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Doctor User</label>
              <select className="form-control" value={form.user_id} onChange={set('user_id')} required>
                <option value="">Select doctor user…</option>
                {doctorUsers.map(u => <option key={u.id} value={u.id}>{u.full_name} ({u.username})</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Specialization</label>
              <select className="form-control" value={form.specialization_id} onChange={set('specialization_id')} required>
                <option value="">Select specialization…</option>
                {specs.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Qualification</label>
              <input className="form-control" value={form.qualification} onChange={set('qualification')} placeholder="MBBS, MD etc." />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="form-group">
                <label className="form-label">Experience (years)</label>
                <input type="number" className="form-control" value={form.experience_years} onChange={set('experience_years')} min={0} />
              </div>
              <div className="form-group">
                <label className="form-label">Consultation Fee ($)</label>
                <input type="number" className="form-control" value={form.consultation_fee} onChange={set('consultation_fee')} min={0} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Bio</label>
              <textarea className="form-control" value={form.bio} onChange={set('bio')} rows={2} placeholder="Short bio…" />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
              {loading ? 'Creating…' : 'Create Doctor Profile'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default function AdminPage() {
  const [tab, setTab] = useState('overview')
  const [doctors, setDoctors] = useState([])
  const [specs, setSpecs] = useState([])
  const [users, setUsers] = useState([])
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const [d, s, u, a] = await Promise.all([
        doctorAPI.list(), specAPI.list(), userAPI.list(), appointmentAPI.all(),
      ])
      setDoctors(d.data)
      setSpecs(s.data)
      setUsers(u.data)
      setAppointments(a.data)
    } catch { toast.error('Load error') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleDeleteSpec = async (id) => {
    if (!confirm('Delete this specialization?')) return
    try {
      await specAPI.delete(id)
      setSpecs(prev => prev.filter(s => s.id !== id))
      toast.success('Deleted')
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed') }
  }

  if (loading) return <div className="main-content"><div className="loading-center"><div className="spinner"></div></div></div>

  const bookedCount = appointments.filter(a => a.status === 'booked').length
  const cancelledCount = appointments.filter(a => a.status === 'cancelled').length

  return (
    <div className="main-content">
      <div className="page-header">
        <h1 className="page-title">Admin Dashboard</h1>
        <p className="page-subtitle">Manage doctors, specializations, and appointments</p>
      </div>

      <div className="admin-grid">
        <div className="stat-card">
          <div className="stat-value">{users.length}</div>
          <div className="stat-label">Total Users</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{doctors.length}</div>
          <div className="stat-label">Doctors</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{appointments.length}</div>
          <div className="stat-label">Total Appointments</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--teal)' }}>{bookedCount}</div>
          <div className="stat-label">Active Bookings</div>
        </div>
      </div>

      <div className="tabs">
        {['overview', 'specializations', 'doctors', 'users'].map(t => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'specializations' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button className="btn btn-teal" onClick={() => setModal('spec')}>+ Add Specialization</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px,1fr))', gap: 14 }}>
            {specs.map(s => (
              <div key={s.id} className="card">
                <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 18px' }}>
                  <div>
                    <div style={{ fontSize: 20, marginBottom: 4 }}>{s.icon || '🏥'}</div>
                    <div style={{ fontWeight: 700, color: 'var(--navy)' }}>{s.name}</div>
                    {s.description && <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 2 }}>{s.description}</div>}
                  </div>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDeleteSpec(s.id)}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'doctors' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button className="btn btn-primary" onClick={() => setModal('doctor')}>+ Add Doctor Profile</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {doctors.map(d => (
              <div key={d.id} className="card">
                <div className="card-body" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--navy)', fontSize: 16 }}>Dr. {d.user?.full_name}</div>
                    <div style={{ fontSize: 13, color: 'var(--gray-400)' }}>{d.specialization?.name} · {d.qualification} · {d.experience_years} yrs</div>
                    <div style={{ fontSize: 13, color: 'var(--gray-400)' }}>{d.user?.email}</div>
                  </div>
                  <span className="meta-chip">${d.consultation_fee}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'users' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {users.map(u => (
            <div key={u.id} className="card">
              <div className="card-body" style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--navy)' }}>{u.full_name}</div>
                  <div style={{ fontSize: 13, color: 'var(--gray-400)' }}>@{u.username} · {u.email}</div>
                </div>
                <span className={`appt-status ${u.role === 'doctor' ? 'status-booked' : u.role === 'admin' ? 'status-completed' : 'status-cancelled'}`} style={{ textTransform: 'capitalize' }}>
                  {u.role}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'overview' && (
        <div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 20, color: 'var(--navy)', marginBottom: 16 }}>Recent Appointments</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {appointments.slice(0, 10).map(a => (
              <div key={a.id} className="card">
                <div className="card-body" style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--navy)' }}>{a.patient?.full_name} → Dr. {a.slot?.doctor?.user?.full_name}</div>
                    <div style={{ fontSize: 13, color: 'var(--gray-400)' }}>{a.slot?.slot_date} at {a.slot?.start_time}</div>
                    {a.reason && <div style={{ fontSize: 13, color: 'var(--gray-400)', fontStyle: 'italic' }}>{a.reason}</div>}
                  </div>
                  <span className={`appt-status status-${a.status}`}>{a.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {modal === 'spec' && <AddSpecModal onClose={(r) => { setModal(null); if (r) load() }} />}
      {modal === 'doctor' && <AddDoctorModal specs={specs} users={users} onClose={(r) => { setModal(null); if (r) load() }} />}
    </div>
  )
}
