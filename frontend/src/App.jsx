import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import axios from 'axios';
import Login from "./components/Login.jsx";
import Register from "./components/Register.jsx";
import Products from "./components/Product.jsx";       // not Products.jsx
import ProductDetail from "./components/ProductDetail.jsx";
import Cart from "./components/Cart.jsx";
import Checkout from "./components/Checkout.jsx";
import Orders from "./components/Orders.jsx";
import Profile from "./components/Profile.jsx";
import StoreSettings from "./components/StoreSetting.jsx"; // file is StoreSetting.jsx, not StoreSettings.jsx


function App() {
  const [user, setUser] = useState(null);
  const [cart, setCart] = useState([]);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const navigate = useNavigate();

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      axios.get('/api/auth/profile/').then(res => setUser(res.data)).catch(() => {
        localStorage.removeItem('token');
        setToken(null);
      });
      axios.get('/api/cart/').then(res => setCart(res.data.items));
    }
  }, [token]);

  const handleLogin = (loginToken) => {
    localStorage.setItem('token', loginToken);
    setToken(loginToken);
    navigate('/');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setCart([]);
    navigate('/');
  };

  const addToCart = (productId) => {
    axios.post('/api/cart/add/', { product_id: productId }).then(res => setCart(res.data.items));
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-blue-600 p-4 text-white">
        <div className="container mx-auto flex justify-between">
          <Link to="/" className="text-xl font-bold">Kbrands Ecommerce</Link>
          <div>
            <Link to="/" className="mr-4">Home</Link>
            <Link to="/products" className="mr-4">Products</Link>
            <Link to="/cart" className="mr-4">Cart ({cart.length})</Link>
            {user ? (
              <>
                <Link to="/profile" className="mr-4">Profile</Link>
                <Link to="/orders" className="mr-4">Orders</Link>
                <button onClick={handleLogout}>Logout</button>
              </>
            ) : (
              <>
                <Link to="/login" className="mr-4">Login</Link>
                <Link to="/register">Register</Link>
              </>
            )}
          </div>
        </div>
      </nav>
      <main className="container mx-auto p-4">
        <Routes>
          <Route path="/" element={<Products onAddToCart={addToCart} />} />
          <Route path="/products" element={<Products onAddToCart={addToCart} />} />
          <Route path="/products/:id" element={<ProductDetail onAddToCart={addToCart} />} />
          <Route path="/cart" element={<Cart cart={cart} setCart={setCart} />} />
          <Route path="/checkout" element={<Checkout cart={cart} />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/profile" element={<Profile user={user} />} />
          <Route path="/store-settings" element={<StoreSettings />} />
          <Route path="/login" element={<Login onLogin={handleLogin} />} />
          <Route path="/register" element={<Register onRegister={handleLogin} />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;