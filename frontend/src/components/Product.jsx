import { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

export default function Products({ onAddToCart }) {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let url = '/api/products/';
    if (search) url += `?search=${search}`;
    if (category) url += `&category=${category}`;
    axios.get(url).then(res => {
      setProducts(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [search, category]);

  if (loading) return <div className="text-center">Loading...</div>;

  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold mb-4">Products</h1>
      <div className="mb-4">
        <input type="text" placeholder="Search products..." value={search} onChange={(e) => setSearch(e.target.value)} className="p-2 border rounded mr-4" />
        <select value={category} onChange={(e) => setCategory(e.target.value)} className="p-2 border rounded">
          <option value="">All Categories</option>
          <option value="Electronics">Electronics</option>
          <option value="Clothing">Clothing</option>
          <option value="Books">Books</option>
        </select>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {products.map(product => (
          <div key={product.id} className="bg-white p-4 rounded shadow">
            {product.image && <img src={product.image} alt={product.name} className="w-full h-48 object-cover mb-2" />}
            <h3 className="text-xl font-bold">{product.name}</h3>
            <p className="text-gray-600">${product.price}</p>
            <p className="text-sm text-gray-500">{product.description.substring(0, 100)}...</p>
            <div className="flex justify-between mt-2">
              <Link to={`/products/${product.id}`} className="text-blue-600">View Details</Link>
              <button onClick={() => onAddToCart(product.id)} className="bg-blue-600 text-white px-4 py-1 rounded">Add to Cart</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}