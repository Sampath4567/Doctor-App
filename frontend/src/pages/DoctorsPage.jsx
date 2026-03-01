import { useState, useEffect } from 'react'
import { doctorAPI, specAPI, slotAPI, appointmentAPI } from '../services/api'
import toast from 'react-hot-toast'

function groupSlotsByDate(slots) {
  return slots.reduce((acc, slot) => {
    if (!acc[slot.slot_date]) acc[slot.slot_date] = []
    acc[slot.slot_date].push(slot)
    return acc
  }, {})
}

function BookingModal({ doctor, onClose }) {
  const [slots, setSlots] = useState([])
  const [loadingSlots, setLoadingSlots] = useState(true)
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [reason, setReason] = useState('')
  const [booking, setBooking] = useState(false)

  useEffect(() => {
    slotAPI.list(doctor.id, {}).then(({ data }) => {
      setSlots(data)
    }).catch(() => toast.error('Could not load slots')).finally(() => setLoadingSlots(false))
  }, [doctor.id])

  const grouped = groupSlotsByDate(slots)

  const handleBook = async () => {
    if (!selectedSlot) return toast.error('Select a time slot first')
    setBooking(true)
    try {
      await appointmentAPI.book({ slot_id: selectedSlot.id, reason })
      toast.success('🎉 Appointment booked! Check your email.')
      onClose(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Booking failed')
    } finally {
      setBooking(false)
    }
  }

  const formatDate = (d) => {
    const dt = new Date(d)
    return dt.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose(false)}>
      <div className="modal-box">
        <div className="modal-header">
          <div>
            <div className="modal-title">Book Appointment</div>
            <div style={{ fontSize: 14, color: 'var(--gray-400)', marginTop: 2 }}>
              Dr. {doctor.user?.full_name} · {doctor.specialization?.name}
            </div>
          </div>
          <button className="modal-close" onClick={() => onClose(false)}>×</button>
        </div>
        <div className="modal-body">
          {loadingSlots ? (
            <div className="spinner"></div>
          ) : slots.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📅</div>
              <div className="empty-state-text">No available slots at the moment</div>
            </div>
          ) : (
            <div className="slots-container">
              {Object.entries(grouped).map(([date, dateSlots]) => (
                <div key={date} className="slots-date-group">
                  <div className="slots-date-label">{formatDate(date)}</div>
                  <div className="slots-grid">
                    {dateSlots.map((slot) => (
                      <button
                        key={slot.id}
                        className={`slot-pill ${slot.is_booked ? 'booked' : ''} ${selectedSlot?.id === slot.id ? 'selected' : ''}`}
                        onClick={() => !slot.is_booked && setSelectedSlot(slot)}
                        disabled={slot.is_booked}
                      >
                        {slot.start_time} – {slot.end_time}
                        {slot.is_booked && <span style={{ fontSize: 11, marginLeft: 4 }}>Taken</span>}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {selectedSlot && (
            <div style={{ marginTop: 20, padding: 14, background: 'var(--teal-light)', borderRadius: 'var(--radius-sm)', border: '1px solid #a7f3d0', fontSize: 14, color: 'var(--gray-600)', marginBottom: 16 }}>
              ✅ Selected: <strong>{selectedSlot.slot_date}</strong> at <strong>{selectedSlot.start_time}</strong>
            </div>
          )}

          <div className="form-group" style={{ marginTop: 16 }}>
            <label className="form-label">Reason for visit (optional)</label>
            <textarea
              className="form-control"
              placeholder="Describe your symptoms or reason…"
              value={reason}
              onChange={e => setReason(e.target.value)}
              rows={3}
            />
          </div>

          <button
            className="btn btn-teal"
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={handleBook}
            disabled={!selectedSlot || booking}
          >
            {booking ? 'Booking…' : 'Confirm Appointment'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function DoctorsPage() {
  const [doctors, setDoctors] = useState([])
  const [specs, setSpecs] = useState([])
  const [selectedSpec, setSelectedSpec] = useState(null)
  const [loading, setLoading] = useState(true)
  const [bookingDoctor, setBookingDoctor] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const [docsRes, specsRes] = await Promise.all([
        doctorAPI.list(selectedSpec),
        specAPI.list(),
      ])
      setDoctors(docsRes.data)
      setSpecs(specsRes.data)
    } catch { toast.error('Failed to load doctors') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [selectedSpec])

  const getInitials = (name) => name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || '??'

  return (
    <div className="main-content">
      <div className="page-header">
        <h1 className="page-title">Find a Doctor</h1>
        <p className="page-subtitle">Browse available specialists and book your appointment</p>
      </div>

      <div className="filter-row">
        <button className={`filter-chip ${!selectedSpec ? 'active' : ''}`} onClick={() => setSelectedSpec(null)}>All Specialties</button>
        {specs.map(s => (
          <button key={s.id} className={`filter-chip ${selectedSpec === s.id ? 'active' : ''}`} onClick={() => setSelectedSpec(s.id)}>
            {s.icon && <span>{s.icon} </span>}{s.name}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-center"><div className="spinner"></div></div>
      ) : doctors.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <div className="empty-state-text">No doctors found for this specialty</div>
        </div>
      ) : (
        <div className="doctors-grid">
          {doctors.map(doc => (
            <div key={doc.id} className="doctor-card" onClick={() => setBookingDoctor(doc)}>
              <div className="doctor-card-top">
                <div className="doctor-avatar">{getInitials(doc.user?.full_name)}</div>
                <div>
                  <div className="doctor-name">Dr. {doc.user?.full_name}</div>
                  <div className="doctor-spec">{doc.specialization?.name}</div>
                </div>
              </div>
              <div className="doctor-card-body">
                <div className="doctor-meta">
                  {doc.experience_years > 0 && (
                    <span className="meta-chip"><span className="icon">🏅</span>{doc.experience_years} yrs exp</span>
                  )}
                  {doc.qualification && (
                    <span className="meta-chip"><span className="icon">🎓</span>{doc.qualification}</span>
                  )}
                  {doc.consultation_fee > 0 && (
                    <span className="meta-chip"><span className="icon">💳</span>${doc.consultation_fee}</span>
                  )}
                </div>
                {doc.bio && (
                  <p style={{ fontSize: 13, color: 'var(--gray-400)', lineHeight: 1.6, marginBottom: 16 }}>
                    {doc.bio.length > 100 ? doc.bio.slice(0, 100) + '…' : doc.bio}
                  </p>
                )}
                <button className="btn btn-teal btn-sm" style={{ width: '100%', justifyContent: 'center' }}>
                  Book Appointment →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {bookingDoctor && (
        <BookingModal
          doctor={bookingDoctor}
          onClose={(refreshed) => {
            setBookingDoctor(null)
            if (refreshed) load()
          }}
        />
      )}
    </div>
  )
}
