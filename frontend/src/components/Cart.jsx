import { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

export default function Cart({ cart, setCart }) {
  const [loading, setLoading] = useState(false);

  const removeFromCart = (productId) => {
    setLoading(true);
    axios.post('/api/cart/remove/', { product_id: productId }).then(res => setCart(res.data.items)).finally(() => setLoading(false));
  };

  const total = cart.reduce((sum, item) => sum + (item.quantity * item.product.price), 0);

  if (cart.length === 0) return <div className="text-center p-4">Your cart is empty. <Link to="/products" className="text-blue-600">Shop now</Link></div>;

  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold mb-4">Cart</h1>
      {cart.map(item => (
        <div key={item.id} className="flex justify-between p-4 bg-white rounded mb-2">
          <div>
            <h3 className="font-bold">{item.product.name}</h3>
            <p>${item.product.price} x {item.quantity}</p>
          </div>
          <button onClick={() => removeFromCart(item.product.id)} className="bg-red-600 text-white px-4 py-1 rounded" disabled={loading}>
            Remove
          </button>
        </div>
      ))}
      <div className="text-xl font-bold text-right">Total: ${total.toFixed(2)}</div>
      <Link to="/checkout" className="block w-full text-center bg-green-600 text-white p-3 rounded mt-4">Checkout</Link>
    </div>
  );
}