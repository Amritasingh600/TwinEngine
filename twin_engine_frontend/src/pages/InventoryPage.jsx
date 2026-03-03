import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { getInventory } from '../services/api';

export default function InventoryPage() {
  const { outletId } = useOutletContext();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getInventory(outletId)
      .then((res) => setItems(res.data.results || res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [outletId]);

  if (loading) return <p>Loading inventory...</p>;

  return (
    <div>
      <h2>Inventory ({items.length} items)</h2>
      {items.length === 0 && <p>No inventory data.</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Quantity</th>
            <th>Unit</th>
            <th>Reorder At</th>
            <th>Par Level</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const low = item.current_quantity <= item.reorder_threshold;
            return (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td>{item.category}</td>
                <td style={low ? { color: '#EF4444', fontWeight: 600 } : {}}>
                  {item.current_quantity}
                </td>
                <td>{item.unit}</td>
                <td>{item.reorder_threshold}</td>
                <td>{item.par_level}</td>
                <td>
                  <span
                    className="badge"
                    style={{
                      background: low ? '#EF4444' : '#22C55E',
                      color: '#fff',
                    }}
                  >
                    {low ? 'Low Stock' : 'OK'}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
