import { useState, useEffect } from 'react'
import { slotAPI, doctorAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

const TIME_OPTIONS = []
for (let h = 8; h <= 18; h++) {
  TIME_OPTIONS.push(`${String(h).padStart(2, '0')}:00`)
  TIME_OPTIONS.push(`${String(h).padStart(2, '0')}:30`)
}

function groupSlotsByDate(slots) {
  return slots.reduce((acc, slot) => {
    if (!acc[slot.slot_date]) acc[slot.slot_date] = []
    acc[slot.slot_date].push(slot)
    return acc
  }, {})
}

const WEEKDAYS = [
  { label: 'Mon', value: 0 },
  { label: 'Tue', value: 1 },
  { label: 'Wed', value: 2 },
  { label: 'Thu', value: 3 },
  { label: 'Fri', value: 4 },
  { label: 'Sat', value: 5 },
  { label: 'Sun', value: 6 },
]

export default function MySlotsPage() {
  const { user } = useAuth()
  const [doctor, setDoctor] = useState(null)
  const [slots, setSlots] = useState([])
  const [loading, setLoading] = useState(true)
  const [bulkForm, setBulkForm] = useState({ 
    start_time: '09:00', 
    end_time: '17:00', 
    slot_duration: 30, 
    lunch_start: '13:00', 
    lunch_end: '14:00', 
    days_of_week: [0, 1, 2, 3, 4],
    weeks: 4
  })
  const [adding, setAdding] = useState(false)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    async function init() {
      try {
        const { data } = await doctorAPI.list()
        const mine = data.find(d => d.user_id === user.user_id)
        if (!mine) return toast.error('Doctor profile not found. Contact admin.')
        setDoctor(mine)
        fetchSlots(mine.id)
      } catch { toast.error('Failed to load data') }
      finally { setLoading(false) }
    }
    init()
  }, [user.user_id])

  const fetchSlots = async (doctorId) => {
    const { data } = await slotAPI.list(doctorId)
    setSlots(data)
  }

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!doctor) return
    setAdding(true)
    try {
      await slotAPI.createBulk(doctor.id, bulkForm)
      toast.success('Slots generated successfully!')
      fetchSlots(doctor.id)
      setShowForm(false)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add slot')
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async (slotId) => {
    if (!confirm('Delete this slot?')) return
    try {
      await slotAPI.delete(doctor.id, slotId)
      setSlots(prev => prev.filter(s => s.id !== slotId))
      toast.success('Slot deleted')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Cannot delete booked slot')
    }
  }

  const handleClearFuture = async () => {
    if (!confirm('This will delete ALL unbooked slots from today onwards. Booked appointments will not be affected. Continue?')) return
    setLoading(true)
    try {
      await slotAPI.clearFuture(doctor.id)
      toast.success('Future unbooked slots cleared')
      fetchSlots(doctor.id)
    } catch { toast.error('Failed to clear slots') }
    finally { setLoading(false) }
  }

  const today = new Date().toISOString().split('T')[0]
  // Only show slots from today onwards in the list
  const futureSlots = slots.filter(s => s.slot_date >= today)
  const grouped = groupSlotsByDate(futureSlots)

  if (loading) return <div className="main-content"><div className="loading-center"><div className="spinner"></div></div></div>

  return (
    <div className="main-content">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 className="page-title">My Slots</h1>
          <p className="page-subtitle">Manage your available appointment slots (30 min each)</p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-danger btn-outline" onClick={handleClearFuture} title="Clear all future unbooked slots">
            🗑️ Clear Future
          </button>
          <button className="btn btn-teal" onClick={() => setShowForm(!showForm)}>
            {showForm ? '✕ Cancel' : '+ Add Slot'}
          </button>
        </div>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: 28 }}>
          <div className="card-header">
            <strong style={{ fontSize: 15, color: 'var(--navy)' }}>Set Weekly Availability</strong>
          </div>
          <div className="card-body">
              <form onSubmit={handleAdd} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 16, alignItems: 'flex-end' }}>
                <div className="form-group" style={{ marginBottom: 0, gridColumn: '1 / -1' }}>
                  <label className="form-label">Available Days</label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 8 }}>
                    {WEEKDAYS.map(day => (
                      <label key={day.value} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 14 }}>
                        <input 
                          type="checkbox" 
                          checked={bulkForm.days_of_week.includes(day.value)} 
                          onChange={e => {
                            const next = e.target.checked 
                              ? [...bulkForm.days_of_week, day.value]
                              : bulkForm.days_of_week.filter(v => v !== day.value)
                            setBulkForm({ ...bulkForm, days_of_week: next })
                          }} 
                        />
                        {day.label}
                      </label>
                    ))}
                  </div>
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Start Time</label>
                  <select
                    className="form-control"
                    value={bulkForm.start_time}
                    onChange={e => setBulkForm({ ...bulkForm, start_time: e.target.value })}
                  >
                    {TIME_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">End Time</label>
                  <select
                    className="form-control"
                    value={bulkForm.end_time}
                    onChange={e => setBulkForm({ ...bulkForm, end_time: e.target.value })}
                  >
                    {TIME_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Duration (min)</label>
                  <input
                    type="number"
                    className="form-control"
                    value={bulkForm.slot_duration}
                    onChange={e => setBulkForm({ ...bulkForm, slot_duration: parseInt(e.target.value) })}
                    min="15" step="15"
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Lunch Start</label>
                  <select
                    className="form-control"
                    value={bulkForm.lunch_start}
                    onChange={e => setBulkForm({ ...bulkForm, lunch_start: e.target.value })}
                  >
                    <option value="">None</option>
                    {TIME_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Lunch End</label>
                  <select
                    className="form-control"
                    value={bulkForm.lunch_end}
                    onChange={e => setBulkForm({ ...bulkForm, lunch_end: e.target.value })}
                  >
                    <option value="">None</option>
                    {TIME_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Generate for (weeks)</label>
                  <input
                    type="number"
                    className="form-control"
                    value={bulkForm.weeks}
                    onChange={e => setBulkForm({ ...bulkForm, weeks: parseInt(e.target.value) })}
                    min="1" max="12"
                  />
                </div>
                <button type="submit" className="btn btn-teal" style={{ height: 42 }} disabled={adding || bulkForm.days_of_week.length === 0}>
                  {adding ? 'Generating…' : 'Generate Slots'}
                </button>
              </form>
            <p style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 10 }}>
              Slots will be generated for the selected days over the next {bulkForm.weeks} weeks.
            </p>
          </div>
        </div>
      )}

      {slots.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🗓️</div>
          <div className="empty-state-text">No slots yet. Add your first slot above.</div>
        </div>
      ) : (
        <div className="slots-container">
          {Object.entries(grouped).sort().map(([date, dateSlots]) => (
            <div key={date} className="slots-date-group">
              <div className="slots-date-label">
                {new Date(date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                {dateSlots.map(slot => (
                  <div
                    key={slot.id}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      padding: '9px 16px',
                      background: slot.is_booked ? 'var(--teal-light)' : 'var(--white)',
                      border: `2px solid ${slot.is_booked ? 'var(--teal)' : 'var(--gray-200)'}`,
                      borderRadius: 40,
                    }}
                  >
                    <span style={{ fontSize: 14, fontWeight: 600, color: slot.is_booked ? 'var(--teal)' : 'var(--gray-600)' }}>
                      {slot.start_time} – {slot.end_time}
                    </span>
                    {slot.is_booked ? (
                      <span style={{ fontSize: 11, background: 'var(--teal)', color: '#fff', padding: '2px 7px', borderRadius: 10, fontWeight: 600 }}>BOOKED</span>
                    ) : (
                      <button
                        onClick={() => handleDelete(slot.id)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--red)', fontSize: 16, lineHeight: 1, padding: '0 2px' }}
                        title="Delete slot"
                      >×</button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
