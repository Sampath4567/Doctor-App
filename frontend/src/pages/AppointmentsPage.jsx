// // frontend/src/pages/MyAppointmentsPage.jsx
import { useState, useEffect } from 'react'
import { appointmentAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import PrescriptionModal from '../components/PrescriptionModal'

export default function MyAppointmentsPage() {
  const { user } = useAuth()
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedAppt, setSelectedAppt] = useState(null)

  useEffect(() => {
    fetchAppointments()
  }, [])

  const fetchAppointments = async () => {
    try {
      const { data } = await appointmentAPI.my()
      setAppointments(data)
    } catch (err) {
      toast.error('Failed to load appointments')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async (id) => {
    if (!confirm('Are you sure you want to cancel this appointment?')) return
    try {
      await appointmentAPI.cancel(id)
      toast.success('Appointment cancelled')
      fetchAppointments()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to cancel')
    }
  }

  const handleComplete = async (id, data) => {
    try {
      await appointmentAPI.complete(id, data)
      toast.success('Visit completed & prescription sent!')
      setSelectedAppt(null)
      fetchAppointments()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to complete')
    }
  }

  if (loading) return <div className="main-content"><div className="loading-center"><div className="spinner"></div></div></div>

  return (
    <div className="main-content">
      <h1 className="page-title">My Appointments</h1>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {appointments.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-text">No appointments found.</div>
          </div>
        ) : (
          appointments.map(appt => (
            <div key={appt.id} className="card">
              <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 4, color: 'var(--navy)' }}>
                    {new Date(appt.slot.slot_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })} at {appt.slot.start_time}
                  </div>
                  <div style={{ color: '#666', fontSize: 14 }}>
                    {user.role === 'doctor' ? (
                      <>Patient: <strong>{appt.patient?.full_name}</strong></>
                    ) : (
                      <>Doctor: <strong>Dr. {appt.slot.doctor?.user?.full_name}</strong></>
                    )}
                  </div>
                  <div style={{ fontSize: 14, marginTop: 4, color: '#555' }}>Reason: {appt.reason}</div>
                  <div style={{ marginTop: 8 }}>
                    <span style={{ 
                      padding: '4px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                      backgroundColor: appt.status === 'booked' ? '#e0f2fe' : appt.status === 'cancelled' ? '#fee2e2' : '#dcfce7',
                      color: appt.status === 'booked' ? '#0369a1' : appt.status === 'cancelled' ? '#b91c1c' : '#15803d'
                    }}>
                      {appt.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 10 }}>
                  {appt.status === 'booked' && (
                    <>
                      <button 
                        className="btn" 
                        onClick={() => handleCancel(appt.id)} 
                        style={{ fontSize: 13, padding: '8px 16px', border: '1px solid #fee2e2', color: '#b91c1c', background: '#fff' }}
                      >
                        Cancel
                      </button>
                      {user.role === 'doctor' && (
                        <button 
                          className="btn btn-teal" 
                          onClick={() => setSelectedAppt(appt)} 
                          style={{ fontSize: 13, padding: '8px 16px' }}
                        >
                          Complete Visit
                        </button>
                      )}
                    </>
                  )}
                  
                  {/* View Prescription Button for both Doctor and Patient */}
                  {appt.status === 'completed' && (
                    <button 
                      className="btn" 
                      onClick={() => alert(`MEDICATIONS:\n${appt.medications}\n\nNOTES:\n${appt.prescription_notes}`)} 
                      style={{ fontSize: 13, padding: '8px 16px', border: '1px solid #ddd', background: '#f8fafc', color: '#333' }}
                    >
                      View Prescription
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {selectedAppt && (
        <PrescriptionModal 
          appointment={selectedAppt} 
          onClose={() => setSelectedAppt(null)} 
          onSubmit={handleComplete} 
        />
      )}
    </div>
  )
}
