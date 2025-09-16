import { useState } from 'react';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const stripePromise = loadStripe('pk_test_your-public-key'); // Replace with your Stripe public key

function CheckoutForm({ cart, onSuccess }) {
  const stripe = useStripe();
  const elements = useElements();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const { error, paymentMethod } = await stripe.createPaymentMethod({
      type: 'card',
      card: elements.getElement(CardElement),
    });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    const total = cart.reduce((sum, item) => sum + (item.quantity * item.product.price), 0);
    try {
      const res = await axios.post('/api/payments/initiate/', { order_id: 'dummy-order-id', payment_method: 'stripe' }); // Replace with real order ID
      const { client_secret } = res.data;
      const result = await stripe.confirmCardPayment(client_secret, {
        payment_method: {
          card: elements.getElement(CardElement),
          billing_details: { name: 'Test User' },
        },
      });

      if (result.error) {
        setError(result.error.message);
      } else {
        onSuccess();
        navigate('/orders');
      }
    } catch (err) {
      setError(err.response.data.error || 'Payment failed');
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Checkout</h2>
      <CardElement className="p-3 border rounded mb-4" />
      <button type="submit" disabled={!stripe || loading} className="w-full bg-green-600 text-white p-3 rounded">
        {loading ? 'Processing...' : 'Pay Now'}
      </button>
      {error && <p className="text-red-500 mt-2">{error}</p>}
    </form>
  );
}

export default function Checkout({ cart }) {
  const total = cart.reduce((sum, item) => sum + (item.quantity * item.product.price), 0);

  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold mb-4">Checkout</h1>
      <p className="text-xl">Total: ${total.toFixed(2)}</p>
      <Elements stripe={stripePromise}>
        <CheckoutForm cart={cart} onSuccess={() => alert('Payment successful!')} />
      </Elements>
    </div>
  );
}