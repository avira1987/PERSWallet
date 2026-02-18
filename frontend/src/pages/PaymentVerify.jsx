import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import client from '../api/client';

export default function PaymentVerify() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('verifying');
  const [result, setResult] = useState(null);

  useEffect(() => {
    const verify = async () => {
      const authority = searchParams.get('Authority') || searchParams.get('authority') || searchParams.get('id');
      const paymentStatus = searchParams.get('Status') || searchParams.get('status');

      if (!authority) {
        setStatus('error');
        return;
      }

      if (paymentStatus === 'NOK') {
        setStatus('cancelled');
        return;
      }

      try {
        const res = await client.post('/payments/verify/', { authority });
        setResult(res.data);
        setStatus('success');
      } catch (err) {
        setResult(err.response?.data);
        setStatus('failed');
      }
    };
    verify();
  }, [searchParams]);

  const formatAmount = (val) => Number(val).toLocaleString('fa-IR');

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4">
      <div className="bg-white rounded-2xl border border-gray-200 p-8 w-full max-w-md text-center">
        {status === 'verifying' && (
          <>
            <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-4"></div>
            <h2 className="text-xl font-bold text-gray-800">در حال تایید پرداخت...</h2>
            <p className="text-gray-500 mt-2">لطفا صبر کنید.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-green-700">پرداخت موفق!</h2>
            {result && (
              <div className="mt-4 space-y-2 text-gray-600">
                <p>مبلغ: <strong>{formatAmount(result.amount)} ریال</strong></p>
                <p>شماره مرجع: <strong dir="ltr">{result.ref_id}</strong></p>
                <p>موجودی جدید: <strong>{formatAmount(result.new_balance)} ریال</strong></p>
              </div>
            )}
            <Link to="/wallet"
              className="inline-block mt-6 bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-700">
              بازگشت به کیف پول
            </Link>
          </>
        )}

        {status === 'failed' && (
          <>
            <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-red-700">پرداخت ناموفق</h2>
            <p className="text-gray-500 mt-2">{result?.error || result?.detail || 'تایید پرداخت با مشکل مواجه شد.'}</p>
            <Link to="/wallet"
              className="inline-block mt-6 bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-700">
              تلاش مجدد
            </Link>
          </>
        )}

        {status === 'cancelled' && (
          <>
            <div className="w-16 h-16 bg-gray-100 text-gray-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-700">پرداخت لغو شد</h2>
            <p className="text-gray-500 mt-2">شما پرداخت را لغو کردید.</p>
            <Link to="/wallet"
              className="inline-block mt-6 bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-700">
              بازگشت به کیف پول
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <h2 className="text-xl font-bold text-red-700">خطا</h2>
            <p className="text-gray-500 mt-2">اطلاعات پرداخت نامعتبر است.</p>
            <Link to="/wallet"
              className="inline-block mt-6 bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-700">
              بازگشت
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
