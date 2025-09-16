import { useState, useEffect } from 'react';
import axios from 'axios';

export default function StoreSettings() {
  const [storeName, setStoreName] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/api/store-settings/').then(res => {
      setStoreName(res.data.store_name);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.put('/api/store-settings/', { store_name: storeName });
      alert('Store name updated!');
    } catch (err) {
      alert('Update failed');
    }
  };

  if (loading) return <div className="text-center">Loading...</div>;

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Store Settings</h2>
      <form onSubmit={handleUpdate}>
        <input type="text" value={storeName} onChange={(e) => setStoreName(e.target.value)} placeholder="Store Name" className="w-full p-2 border rounded mb-4" required />
        <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded">Update Store Name</button>
      </form>
    </div>
  );
}