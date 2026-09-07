import React, { useState } from 'react';
import {
  Truck,
  User,
  Scale,
  Edit2,
  Check,
  X,
  Filter,
  ArrowUpDown,
  Radio,
} from 'lucide-react';

const DRIVER_OPTIONS = [
  { id: '', label: '— Unassigned —' },
  { id: 'driver1', label: 'driver1 (Ramesh Pawar)' },
  { id: 'driver2', label: 'driver2 (Suresh Gaikwad)' },
  { id: 'driver3', label: 'driver3 (Amit Kulkarni)' },
];

const STATUS_OPTIONS = [
  { value: 'idle', label: 'Idle' },
  { value: 'en_route', label: 'En Route' },
  { value: 'delivering', label: 'Delivering' },
  { value: 'complete', label: 'Complete' },
];

export default function VehicleTable({
  vehicles = [],
  onUpdateVehicle,
  loading = false,
}) {
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortField, setSortField] = useState('label');
  const [sortAsc, setSortAsc] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});

  const startEdit = (v) => {
    setEditingId(v.id || v._id);
    setEditForm({
      label: v.label,
      capacity_kg: v.capacity_kg,
      status: v.status,
      driver_id: v.driver_id || '',
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };

  const saveEdit = async (id) => {
    if (!editForm.capacity_kg || Number(editForm.capacity_kg) <= 0) {
      alert('Capacity must be a positive number.');
      return;
    }
    await onUpdateVehicle(id, {
      label: editForm.label,
      capacity_kg: parseFloat(editForm.capacity_kg),
      status: editForm.status,
      driver_id: editForm.driver_id || null,
    });
    setEditingId(null);
  };

  const handleQuickDriverChange = async (vehicle, newDriverId) => {
    const id = vehicle.id || vehicle._id;
    await onUpdateVehicle(id, {
      driver_id: newDriverId || null,
    });
  };

  const handleQuickStatusChange = async (vehicle, newStatus) => {
    const id = vehicle.id || vehicle._id;
    await onUpdateVehicle(id, {
      status: newStatus,
    });
  };

  // Filter
  const filtered = vehicles.filter((v) => {
    if (statusFilter === 'ALL') return true;
    return v.status === statusFilter;
  });

  // Sort
  const sorted = [...filtered].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];
    if (typeof aVal === 'string') aVal = aVal.toLowerCase();
    if (typeof bVal === 'string') bVal = bVal.toLowerCase();
    if (aVal < bVal) return sortAsc ? -1 : 1;
    if (aVal > bVal) return sortAsc ? 1 : -1;
    return 0;
  });

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Table Controls (Filter & Stats) */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={16} color="var(--text-dim)" />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Status Filter:</span>
          <div style={{ display: 'flex', gap: '0.25rem' }}>
            {['ALL', 'idle', 'en_route', 'delivering', 'complete'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                style={{
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  border: statusFilter === st ? '1px solid var(--primary)' : '1px solid var(--border-card)',
                  background: statusFilter === st ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.02)',
                  color: statusFilter === st ? '#818cf8' : 'var(--text-muted)',
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                  fontWeight: statusFilter === st ? 600 : 400,
                }}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
          Showing <strong>{sorted.length}</strong> of {vehicles.length} vehicles
        </div>
      </div>

      {/* Vehicles Table */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid var(--border-card)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: 'rgba(255, 255, 255, 0.03)', borderBottom: '1px solid var(--border-card)', color: 'var(--text-muted)' }}>
              <th
                onClick={() => toggleSort('label')}
                style={{ padding: '0.85rem 1rem', cursor: 'pointer', userSelect: 'none' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Vehicle Identifier</span>
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th
                onClick={() => toggleSort('capacity_kg')}
                style={{ padding: '0.85rem 1rem', cursor: 'pointer', userSelect: 'none' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Capacity</span>
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th
                onClick={() => toggleSort('status')}
                style={{ padding: '0.85rem 1rem', cursor: 'pointer', userSelect: 'none' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>Live Status</span>
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th style={{ padding: '0.85rem 1rem' }}>Assigned Driver Account</th>
              <th style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((v) => {
              const id = v.id || v._id;
              const isEditing = editingId === id;
              const isEnRoute = v.status === 'en_route' || v.status === 'delivering';

              return (
                <tr
                  key={id}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                    background: isEditing ? 'rgba(99, 102, 241, 0.06)' : 'transparent',
                    transition: 'background 0.15s ease',
                  }}
                >
                  {/* Vehicle Identifier */}
                  <td style={{ padding: '0.85rem 1rem' }}>
                    {isEditing ? (
                      <input
                        type="text"
                        className="form-input"
                        style={{ padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
                        value={editForm.label}
                        onChange={(e) => setEditForm({ ...editForm, label: e.target.value })}
                        required
                      />
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <div style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: 'var(--radius-sm)',
                          background: isEnRoute ? 'rgba(16, 185, 129, 0.15)' : 'rgba(99, 102, 241, 0.15)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}>
                          <Truck size={14} color={isEnRoute ? '#34d399' : '#818cf8'} />
                        </div>
                        <div>
                          <div style={{ fontWeight: 700, color: '#fff' }}>{v.label}</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>ID: {id}</div>
                        </div>
                      </div>
                    )}
                  </td>

                  {/* Capacity */}
                  <td style={{ padding: '0.85rem 1rem' }}>
                    {isEditing ? (
                      <input
                        type="number"
                        className="form-input"
                        style={{ padding: '0.4rem 0.6rem', fontSize: '0.85rem', width: '100px' }}
                        value={editForm.capacity_kg}
                        onChange={(e) => setEditForm({ ...editForm, capacity_kg: e.target.value })}
                        min="1"
                        step="1"
                        required
                      />
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#cbd5e1' }}>
                        <Scale size={13} color="var(--text-dim)" />
                        <span><strong>{v.capacity_kg}</strong> kg</span>
                      </div>
                    )}
                  </td>

                  {/* Status Dropdown */}
                  <td style={{ padding: '0.85rem 1rem' }}>
                    {isEditing ? (
                      <select
                        className="form-input"
                        style={{ padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
                        value={editForm.status}
                        onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                      >
                        {STATUS_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    ) : (
                      <select
                        value={v.status}
                        onChange={(e) => handleQuickStatusChange(v, e.target.value)}
                        style={{
                          background: v.status === 'en_route' ? 'rgba(16, 185, 129, 0.15)' :
                                      v.status === 'delivering' ? 'rgba(59, 130, 246, 0.15)' :
                                      v.status === 'complete' ? 'rgba(139, 92, 246, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                          color: v.status === 'en_route' ? '#34d399' :
                                 v.status === 'delivering' ? '#60a5fa' :
                                 v.status === 'complete' ? '#a78bfa' : '#94a3b8',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '0.3rem 0.5rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        {STATUS_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value} style={{ background: '#121a2b', color: '#fff' }}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>

                  {/* Assigned Driver */}
                  <td style={{ padding: '0.85rem 1rem' }}>
                    {isEditing ? (
                      <select
                        className="form-input"
                        style={{ padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
                        value={editForm.driver_id}
                        onChange={(e) => setEditForm({ ...editForm, driver_id: e.target.value })}
                      >
                        {DRIVER_OPTIONS.map((d) => (
                          <option key={d.id} value={d.id}>{d.label}</option>
                        ))}
                      </select>
                    ) : (
                      <select
                        value={v.driver_id || ''}
                        onChange={(e) => handleQuickDriverChange(v, e.target.value)}
                        style={{
                          background: 'rgba(255, 255, 255, 0.03)',
                          border: '1px solid var(--border-card)',
                          color: v.driver_id ? '#fff' : 'var(--text-dim)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '0.35rem 0.6rem',
                          fontSize: '0.8rem',
                          cursor: 'pointer',
                          width: '100%',
                          maxWidth: '220px',
                        }}
                      >
                        {DRIVER_OPTIONS.map((d) => (
                          <option key={d.id} value={d.id} style={{ background: '#121a2b', color: '#fff' }}>
                            {d.label}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>

                  {/* Actions */}
                  <td style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>
                    {isEditing ? (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.4rem' }}>
                        <button
                          onClick={() => saveEdit(id)}
                          className="btn-primary"
                          style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                          title="Save Changes"
                        >
                          <Check size={14} /> Save
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="btn-secondary"
                          style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                          title="Cancel"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => startEdit(v)}
                        className="btn-secondary"
                        style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                      >
                        <Edit2 size={12} /> Edit
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}

            {!sorted.length && !loading && (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-dim)' }}>
                  No vehicles found matching current filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
