import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Profile({ user }) {
  const [profile, setProfile] = useState(user);
  const [editing, setEditing] = useState(false);

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.put('/api/auth/profile/', profile);
      setProfile(res.data);
      setEditing(false);
    } catch (err) {
      alert('Update failed');
    }
  };

  if (!profile) return <div className="text-center">Loading...</div>;

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Profile</h2>
      {editing ? (
        <form onSubmit={handleUpdate}>
          <input name="first_name" value={profile.first_name} onChange={(e) => setProfile({ ...profile, first_name: e.target.value })} className="w-full p-2 border rounded mb-4" required />
          <input name="last_name" value={profile.last_name} onChange={(e) => setProfile({ ...profile, last_name: e.target.value })} className="w-full p-2 border rounded mb-4" required />
          <button type="submit" className="bg-blue-600 text-white p-2 rounded mr-2">Save</button>
          <button type="button" onClick={() => setEditing(false)} className="bg-gray-600 text-white p-2 rounded">Cancel</button>
        </form>
      ) : (
        <div>
          <p><strong>Username:</strong> {profile.username}</p>
          <p><strong>Email:</strong> {profile.email}</p>
          <p><strong>Name:</strong> {profile.first_name} {profile.last_name}</p>
          <p><strong>Vendor:</strong> {profile.is_vendor ? 'Yes' : 'No'}</p>
          <button onClick={() => setEditing(true)} className="bg-blue-600 text-white p-2 rounded mt-4">Edit Profile</button>
        </div>
      )}
      <Link to="/store-settings" className="block mt-4 text-blue-600">Edit Store Settings</Link>
    </div>
  );
}