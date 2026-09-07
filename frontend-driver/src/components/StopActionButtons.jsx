import React, { useState } from 'react';
import { driverApi } from '../api/client';
import { Check, X, AlertTriangle, RefreshCw } from 'lucide-react';

export default function StopActionButtons({
  stopId,
  vehicleId,
  sessionId,
  currentStatus = 'pending', // 'pending' | 'delivered' | 'failed'
  onStatusUpdated,
}) {
  const [submitting, setSubmitting] = useState(false);
  const [showFailModal, setShowFailModal] = useState(false);
  const [failureReason, setFailureReason] = useState('Customer unavailable');
  const [errorMsg, setErrorMsg] = useState(null);

  // If already completed, show status badge
  if (currentStatus === 'delivered') {
    return (
      <span className="badge badge-success" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
        <Check size={14} /> Delivered
      </span>
    );
  }

  if (currentStatus === 'failed') {
    return (
      <span className="badge badge-danger" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
        <X size={14} /> Delivery Failed
      </span>
    );
  }

  const handleMarkDelivered = async () => {
    if (submitting) return; // Prevent double-tap
    setSubmitting(true);
    setErrorMsg(null);

    try {
      await driverApi.logDeliveryEvent({
        event_type: 'DELIVERED',
        parcel_id: stopId,
        vehicle_id: vehicleId,
        session_id: sessionId || null,
        failure_reason: null,
      });

      if (onStatusUpdated) {
        onStatusUpdated(stopId, 'delivered');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to record delivery event.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirmFailed = async () => {
    if (submitting) return;
    setSubmitting(true);
    setErrorMsg(null);

    try {
      await driverApi.logDeliveryEvent({
        event_type: 'FAILED',
        parcel_id: stopId,
        vehicle_id: vehicleId,
        session_id: sessionId || null,
        failure_reason: failureReason,
      });

      setShowFailModal(false);
      if (onStatusUpdated) {
        onStatusUpdated(stopId, 'failed');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to record delivery failure.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <button
          onClick={handleMarkDelivered}
          disabled={submitting}
          className="btn-success"
          style={{ padding: '0.5rem 0.85rem', fontSize: '0.8rem', flex: 1, justifyContent: 'center' }}
          title="Confirm Successful Delivery"
        >
          {submitting ? <RefreshCw className="animate-spin" size={14} /> : <Check size={14} />}
          <span>Delivered</span>
        </button>

        <button
          onClick={() => setShowFailModal(true)}
          disabled={submitting}
          className="btn-danger"
          style={{ padding: '0.5rem 0.85rem', fontSize: '0.8rem', justifyContent: 'center' }}
          title="Report Delivery Issue"
        >
          <X size={14} />
          <span>Failed</span>
        </button>
      </div>

      {errorMsg && (
        <div style={{ fontSize: '0.75rem', color: '#f87171' }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Confirmation Modal for Marking Stop Failed */}
      {showFailModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(9, 13, 22, 0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000,
          padding: '1rem',
        }}>
          <div className="glass-card" style={{
            width: '100%',
            maxWidth: '360px',
            padding: '1.5rem',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: '#f87171' }}>
              <AlertTriangle size={20} />
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>Confirm Delivery Failure</h4>
            </div>

            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.4 }}>
              Marking stop <strong>{stopId}</strong> as failed is irreversible for this active shift. Please specify the reason:
            </p>

            <select
              className="form-input"
              style={{ marginBottom: '1.25rem', fontSize: '0.85rem' }}
              value={failureReason}
              onChange={(e) => setFailureReason(e.target.value)}
            >
              <option value="Customer unavailable">Customer unavailable / Premises closed</option>
              <option value="Incorrect address / Inaccessible">Incorrect address / Road blocked</option>
              <option value="Customer refused package">Customer refused delivery</option>
              <option value="Damaged parcel">Damaged parcel on arrival</option>
            </select>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                type="button"
                onClick={() => setShowFailModal(false)}
                className="btn-secondary"
                disabled={submitting}
                style={{ fontSize: '0.8rem' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmFailed}
                className="btn-danger"
                disabled={submitting}
                style={{ fontSize: '0.8rem' }}
              >
                {submitting ? 'Recording...' : 'Confirm Failure'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
