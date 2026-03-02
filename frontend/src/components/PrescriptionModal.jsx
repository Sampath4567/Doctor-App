// frontend/src/components/PrescriptionModal.jsx
import { useState } from 'react'

export default function PrescriptionModal({ appointment, onClose, onSubmit }) {
  const [medications, setMedications] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    // Call the parent onSubmit function with the ID and data
    await onSubmit(appointment.id, { medications, prescription_notes: notes })
    setLoading(false)
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div style={{ backgroundColor: 'white', padding: 24, borderRadius: 8, width: '100%', maxWidth: 500, boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
        <h3 style={{ marginTop: 0, marginBottom: 16, color: 'var(--navy)' }}>Complete Visit</h3>
        <p style={{ color: '#666', fontSize: 14, marginBottom: 20 }}>
          Patient: <strong>{appointment.patient?.full_name}</strong>
        </p>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={{ display: 'block', marginBottom: 6, fontWeight: 500, fontSize: 14 }}>Medications</label>
            <textarea 
              required 
              className="form-control"
              value={medications} 
              onChange={e => setMedications(e.target.value)}
              placeholder="e.g. Paracetamol 500mg (1-0-1) after food..."
              rows={4}
              style={{ width: '100%', padding: 10, borderRadius: 6, border: '1px solid #ddd' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 6, fontWeight: 500, fontSize: 14 }}>Doctor's Notes</label>
            <textarea 
              required 
              className="form-control"
              value={notes} 
              onChange={e => setNotes(e.target.value)}
              placeholder="Diagnosis, advice, or next steps..."
              rows={3}
              style={{ width: '100%', padding: 10, borderRadius: 6, border: '1px solid #ddd' }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
            <button type="button" className="btn" onClick={onClose} disabled={loading} style={{ padding: '8px 16px', border: '1px solid #ddd', borderRadius: 6, background: 'white' }}>
              Cancel
            </button>
            <button type="submit" className="btn btn-teal" disabled={loading} style={{ padding: '8px 16px', borderRadius: 6, background: 'var(--teal)', color: 'white', border: 'none' }}>
              {loading ? 'Sending...' : 'Complete & Send Email'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
