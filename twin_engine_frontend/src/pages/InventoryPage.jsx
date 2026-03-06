import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import toast from 'react-hot-toast';
import { getInventory, updateInventoryItem, createInventoryItem, deleteInventoryItem } from '../services/api';
import { ROLES } from '../utils/AuthContext';

const CATEGORIES = [
  { value: 'PRODUCE', label: 'Fresh Produce' },
  { value: 'DAIRY', label: 'Dairy Products' },
  { value: 'MEAT', label: 'Meat & Poultry' },
  { value: 'DRY', label: 'Dry Goods' },
  { value: 'BEVERAGE', label: 'Beverages' },
  { value: 'SUPPLIES', label: 'Kitchen Supplies' },
];

const UNITS = [
  { value: 'KG', label: 'Kilograms' },
  { value: 'L', label: 'Liters' },
  { value: 'PCS', label: 'Pieces' },
  { value: 'BAGS', label: 'Bags' },
  { value: 'BOXES', label: 'Boxes' },
];

/*
 * Role behaviour:
 *  MANAGER  – full access: view + edit + add + remove
 *  CHEF     – view + edit + add + remove inventory items
 */

export default function InventoryPage() {
  const { outletId, role } = useOutletContext();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editQty, setEditQty] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [newItem, setNewItem] = useState({
    name: '', category: 'DRY', unit: 'KG',
    current_quantity: 0, reorder_threshold: 10, par_level: 50, unit_cost: 0,
  });
  const [adding, setAdding] = useState(false);
  const [deleting, setDeleting] = useState(null);

  const canEdit = role === ROLES.CHEF || role === ROLES.MANAGER;

  const fetchItems = () => {
    getInventory(outletId)
      .then((res) => setItems(res.data.results || res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchItems();
  }, [outletId]);

  const startEdit = (item) => {
    setEditingId(item.id);
    setEditQty(String(item.current_quantity));
  };

  const saveEdit = async (itemId) => {
    try {
      await updateInventoryItem(itemId, { current_quantity: Number(editQty) });
      setItems((prev) =>
        prev.map((i) =>
          i.id === itemId ? { ...i, current_quantity: Number(editQty) } : i
        )
      );
      setEditingId(null);
      toast.success('Quantity updated');
    } catch {
      toast.error('Failed to update quantity');
    }
  };

  const cancelEdit = () => setEditingId(null);

  const handleAddItem = async (e) => {
    e.preventDefault();
    setAdding(true);
    try {
      const payload = {
        outlet: outletId,
        name: newItem.name,
        category: newItem.category,
        unit: newItem.unit,
        current_quantity: Number(newItem.current_quantity),
        reorder_threshold: Number(newItem.reorder_threshold),
        par_level: Number(newItem.par_level),
        unit_cost: Number(newItem.unit_cost),
      };
      await createInventoryItem(payload);
      setShowAdd(false);
      setNewItem({ name: '', category: 'DRY', unit: 'KG', current_quantity: 0, reorder_threshold: 10, par_level: 50, unit_cost: 0 });
      fetchItems();
      toast.success('Item added');
    } catch (err) {
      toast.error(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Failed');
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (itemId) => {
    if (!window.confirm('Are you sure you want to remove this item?')) return;
    setDeleting(itemId);
    try {
      await deleteInventoryItem(itemId);
      setItems((prev) => prev.filter((i) => i.id !== itemId));
      toast.success('Item removed');
    } catch {
      toast.error('Failed to delete item');
    } finally {
      setDeleting(null);
    }
  };

  if (loading) return <div className="spinner-wrap"><div className="spinner" /><span>Loading inventory...</span></div>;

  const lowStockCount = items.filter((i) => i.current_quantity <= (i.reorder_threshold || 0)).length;

  return (
    <div>
      <div className="flex-between">
        <h2>📦 Inventory ({items.length} items)</h2>
        {canEdit && (
          <button className="btn-sm" onClick={() => setShowAdd(!showAdd)}>
            {showAdd ? '✕ Close' : '+ Add Item'}
          </button>
        )}
      </div>

      {/* Summary cards */}
      <div className="flex-row" style={{ gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <div className="summary-card">
          <span className="summary-card-label">Total Items</span>
          <strong className="summary-card-value">{items.length}</strong>
        </div>
        <div className="summary-card" style={{ borderColor: lowStockCount > 0 ? 'var(--danger)' : 'var(--gray-200)' }}>
          <span className="summary-card-label">Low Stock</span>
          <strong className="summary-card-value" style={{ color: lowStockCount > 0 ? 'var(--danger)' : 'var(--success)' }}>
            {lowStockCount}
          </strong>
        </div>
      </div>

      {/* Add Item Form */}
      {showAdd && (
        <form className="create-form" onSubmit={handleAddItem}>
          <h3>Add New Inventory Item</h3>
          <div className="form-grid">
            <label>
              Name *
              <input
                type="text" value={newItem.name} required
                onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
                placeholder="e.g. Basmati Rice"
              />
            </label>
            <label>
              Category
              <select value={newItem.category} onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}>
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </label>
            <label>
              Unit
              <select value={newItem.unit} onChange={(e) => setNewItem({ ...newItem, unit: e.target.value })}>
                {UNITS.map((u) => (
                  <option key={u.value} value={u.value}>{u.label}</option>
                ))}
              </select>
            </label>
            <label>
              Quantity
              <input type="number" min="0" step="0.01" value={newItem.current_quantity}
                onChange={(e) => setNewItem({ ...newItem, current_quantity: e.target.value })} />
            </label>
            <label>
              Reorder Threshold
              <input type="number" min="0" step="0.01" value={newItem.reorder_threshold}
                onChange={(e) => setNewItem({ ...newItem, reorder_threshold: e.target.value })} />
            </label>
            <label>
              Par Level
              <input type="number" min="0" step="0.01" value={newItem.par_level}
                onChange={(e) => setNewItem({ ...newItem, par_level: e.target.value })} />
            </label>
            <label>
              Unit Cost (₹)
              <input type="number" min="0" step="0.01" value={newItem.unit_cost}
                onChange={(e) => setNewItem({ ...newItem, unit_cost: e.target.value })} />
            </label>
          </div>
          <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <button type="submit" disabled={adding}>
              {adding ? 'Adding...' : 'Add Item'}
            </button>
            <button type="button" style={{ background: 'var(--gray-400)' }} onClick={() => setShowAdd(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      {canEdit && (
        <p className="text-hint">
          Click a quantity to edit. Use the actions column to remove items.
        </p>
      )}

      {items.length === 0 && (
        <div className="empty-state">
          <h3>No inventory items</h3>
          <p>Add items using the button above.</p>
        </div>
      )}

      {items.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Quantity</th>
              <th>Unit</th>
              <th>Reorder At</th>
              <th>Par Level</th>
              <th>Cost</th>
              <th>Status</th>
              {canEdit && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const low = item.current_quantity <= (item.reorder_threshold || 0);
              const isEditing = editingId === item.id;
              return (
                <tr key={item.id}>
                  <td style={{ fontWeight: 500 }}>{item.name}</td>
                  <td>{CATEGORIES.find((c) => c.value === item.category)?.label || item.category}</td>
                  <td style={low ? { color: 'var(--danger)', fontWeight: 600 } : {}}>
                    {isEditing ? (
                      <input
                        type="number"
                        value={editQty}
                        onChange={(e) => setEditQty(e.target.value)}
                        style={{ width: 70 }}
                        min="0"
                        autoFocus
                      />
                    ) : (
                      <span
                        style={canEdit ? { cursor: 'pointer', textDecoration: 'underline dotted' } : {}}
                        onClick={() => canEdit && startEdit(item)}
                      >
                        {parseFloat(Number(item.current_quantity).toFixed(1))}
                      </span>
                    )}
                  </td>
                  <td>{item.unit}</td>
                  <td>{parseFloat(Number(item.reorder_threshold).toFixed(1))}</td>
                  <td>{parseFloat(Number(item.par_level).toFixed(1))}</td>
                  <td>₹{parseFloat(Number(item.unit_cost).toFixed(2))}</td>
                  <td>
                    <span
                      className="badge"
                      style={{
                        background: low ? 'var(--danger)' : 'var(--success)',
                        color: '#fff',
                      }}
                    >
                      {low ? 'Low Stock' : 'OK'}
                    </span>
                  </td>
                  {canEdit && (
                    <td>
                      <div className="flex-row" style={{ gap: 4 }}>
                        {isEditing ? (
                          <>
                            <button className="btn-sm" onClick={() => saveEdit(item.id)}>Save</button>
                            <button className="btn-sm" style={{ background: 'var(--gray-400)' }} onClick={cancelEdit}>✕</button>
                          </>
                        ) : (
                          <>
                            <button className="btn-sm" onClick={() => startEdit(item)}>Edit</button>
                            <button
                              className="btn-sm"
                              style={{ background: 'var(--danger)' }}
                              onClick={() => handleDelete(item.id)}
                              disabled={deleting === item.id}
                            >
                              {deleting === item.id ? '...' : 'Remove'}
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
