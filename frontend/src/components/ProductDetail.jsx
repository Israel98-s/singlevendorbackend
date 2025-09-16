import { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';

export default function ProductDetail({ onAddToCart }) {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`/api/products/${id}/`).then(res => {
      setProduct(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="text-center">Loading...</div>;
  if (!product) return <div className="text-center">Product not found</div>;

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">{product.name}</h1>
      {product.image && <img src={product.image} alt={product.name} className="w-full h-64 object-cover mb-4" />}
      <p className="text-gray-600 mb-4">${product.price}</p>
      <p className="text-gray-800 mb-4">{product.description}</p>
      <p className="text-gray-600 mb-4">Stock: {product.stock}</p>
      <button onClick={() => onAddToCart(product.id)} className="bg-blue-600 text-white px-6 py-2 rounded">Add to Cart</button>
    </div>
  );
}