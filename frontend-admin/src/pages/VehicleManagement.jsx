import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import VehicleTable from '../components/VehicleTable';
import {
  Truck,
  Plus,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Users,
  Layers,
  X,
} from 'lucide-react';

export default function VehicleManagement() {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // New vehicle modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [newCapacity, setNewCapacity] = useState('500');
  const [newDriver, setNewDriver] = useState('');
  const [formError, setFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchVehicles = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getVehicles();
      setVehicles(data || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch fleet vehicles.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVehicles();
  }, []);

  const handleCreateVehicle = async (e) => {
    e.preventDefault();
    setFormError(null);

    if (!newLabel.trim()) {
      setFormError('Vehicle label/identifier is required.');
      return;
    }

    const cap = parseFloat(newCapacity);
    if (isNaN(cap) || cap <= 0) {
      setFormError('Capacity must be a positive number greater than 0.');
      return;
    }

    setSubmitting(true);
    try {
      await api.createVehicle({
        label: newLabel.trim(),
        capacity_kg: cap,
        status: 'idle',
        driver_id: newDriver || null,
      });

      setSuccessMsg(`Vehicle "${newLabel.trim()}" successfully registered to fleet!`);
      setShowAddModal(false);
      setNewLabel('');
      setNewCapacity('500');
      setNewDriver('');
      await fetchVehicles();
    } catch (err) {
      setFormError(err.message || 'Failed to create vehicle.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateVehicle = async (id, updatePayload) => {
    try {
      await api.updateVehicle(id, updatePayload);
      setSuccessMsg(`Vehicle updated successfully.`);
      await fetchVehicles();
    } catch (err) {
      setError(err.message || 'Failed to update vehicle.');
    }
  };

  // Fleet Statistics
  const totalVehicles = vehicles.length;
  const activeCount = vehicles.filter((v) => v.status === 'en_route' || v.status === 'delivering').length;
  const idleCount = vehicles.filter((v) => v.status === 'idle').length;
  const assignedDriversCount = vehicles.filter((v) => Boolean(v.driver_id)).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner / KPIs */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '1rem',
      }}>
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Truck size={14} /> Total Fleet
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', marginTop: '0.25rem' }}>
            {totalVehicles}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
          <div style={{ fontSize: '0.75rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Truck size={14} /> Active / En Route
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34d399', marginTop: '0.25rem' }}>
            {activeCount}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Layers size={14} /> Idle Staged
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            {idleCount}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Users size={14} /> Assigned Drivers
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#818cf8', marginTop: '0.25rem' }}>
            {assignedDriversCount} / {totalVehicles}
          </div>
        </div>
      </div>

      {/* Main Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff' }}>Fleet & Driver Roster</h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
            Manage vehicle capacities, real-time operating states, and driver assignments.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={fetchVehicles}
            className="btn-secondary"
            style={{ padding: '0.65rem 1rem' }}
            title="Refresh Fleet Data"
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary"
            style={{ padding: '0.65rem 1.25rem' }}
          >
            <Plus size={16} />
            <span>Add Vehicle</span>
          </button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '0.85rem 1rem',
          color: '#f87171',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '0.85rem 1rem',
          color: '#34d399',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle2 size={18} />
            <span>{successMsg}</span>
          </div>
          <button
            onClick={() => setSuccessMsg(null)}
            style={{ background: 'none', border: 'none', color: '#34d399', cursor: 'pointer' }}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Vehicles Table */}
      <div className="glass-card" style={{ padding: '1.25rem' }}>
        <VehicleTable
          vehicles={vehicles}
          onUpdateVehicle={handleUpdateVehicle}
          loading={loading}
        />
      </div>

      {/* Modal: Add New Vehicle */}
      {showAddModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(9, 13, 22, 0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem',
        }}>
          <div className="glass-card" style={{
            width: '100%',
            maxWidth: '460px',
            padding: '2rem',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Truck size={20} color="var(--primary)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff' }}>Register New Vehicle</h3>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            {formError && (
              <div style={{
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.6rem 0.8rem',
                color: '#f87171',
                fontSize: '0.8rem',
                marginBottom: '1rem',
              }}>
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateVehicle} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                  Vehicle Identifier / Label *
                </label>
                <input
                  type="text"
                  className="form-input"
                  value={newLabel}
                  onChange={(e) => setNewLabel(e.target.value)}
                  placeholder="e.g. Van-4, Truck-02"
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                  Payload Capacity (kg) *
                </label>
                <input
                  type="number"
                  className="form-input"
                  value={newCapacity}
                  onChange={(e) => setNewCapacity(e.target.value)}
                  placeholder="500"
                  min="1"
                  step="1"
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                  Assign Driver Account (Optional)
                </label>
                <select
                  className="form-input"
                  value={newDriver}
                  onChange={(e) => setNewDriver(e.target.value)}
                >
                  <option value="">— Unassigned —</option>
                  <option value="driver1">driver1 (Ramesh Pawar)</option>
                  <option value="driver2">driver2 (Suresh Gaikwad)</option>
                  <option value="driver3">driver3 (Amit Kulkarni)</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'Creating...' : 'Register Vehicle'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
