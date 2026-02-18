import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import EnamadBadge from '../components/EnamadBadge';
import { HiShieldCheck, HiCurrencyDollar, HiUserGroup, HiLightningBolt } from 'react-icons/hi';

export default function Landing() {
  const { user } = useAuth();

  const features = [
    {
      icon: <HiCurrencyDollar className="w-8 h-8" />,
      title: 'کیف پول هوشمند',
      desc: 'شارژ آسان حساب از طریق درگاه‌های معتبر بانکی شاپرک',
    },
    {
      icon: <HiLightningBolt className="w-8 h-8" />,
      title: 'انتقال سریع',
      desc: 'ارسال و دریافت شارژ بین کاربران به صورت آنی و امن',
    },
    {
      icon: <HiShieldCheck className="w-8 h-8" />,
      title: 'امنیت بالا',
      desc: 'رمزنگاری Argon2 و احراز هویت دو مرحله‌ای (Google Authenticator)',
    },
    {
      icon: <HiUserGroup className="w-8 h-8" />,
      title: 'افیلیت پروگرام',
      desc: 'با معرفی کاربران جدید، از هر تراکنش آن‌ها پورسیون دریافت کنید',
    },
  ];

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-bl from-primary-600 via-primary-700 to-primary-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-28">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight mb-6">
              سیستم مدیریت حساب کاربری
            </h1>
            <p className="text-lg md:text-xl text-primary-100 leading-8 mb-10">
              پلتفرم جامع شارژ حساب، انتقال وجه و مدیریت کیف پول با بالاترین استانداردهای امنیتی.
              به جمع هزاران کاربر ما بپیوندید.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {user ? (
                <Link to="/dashboard"
                  className="bg-white text-primary-700 px-8 py-3 rounded-xl font-semibold hover:bg-gray-100 transition-colors text-lg">
                  ورود به داشبورد
                </Link>
              ) : (
                <>
                  <Link to="/register"
                    className="bg-white text-primary-700 px-8 py-3 rounded-xl font-semibold hover:bg-gray-100 transition-colors text-lg">
                    شروع رایگان
                  </Link>
                  <Link to="/login"
                    className="border-2 border-white text-white px-8 py-3 rounded-xl font-semibold hover:bg-white/10 transition-colors text-lg">
                    ورود به حساب
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">امکانات و ویژگی‌ها</h2>
            <p className="text-gray-500 text-lg">هر آنچه برای مدیریت حساب کاربری خود نیاز دارید</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((f, i) => (
              <div key={i} className="card-hover bg-gray-50 rounded-2xl p-6 text-center border border-gray-100">
                <div className="w-16 h-16 bg-primary-100 text-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  {f.icon}
                </div>
                <h3 className="font-bold text-lg mb-2 text-gray-800">{f.title}</h3>
                <p className="text-gray-500 text-sm leading-6">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About Company */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-6">درباره ما</h2>
              <p className="text-gray-600 leading-8 mb-4">
                شرکت ما با هدف ارائه خدمات مالی نوین و امن، پلتفرمی جامع برای مدیریت حساب‌های کاربری 
                ایجاد کرده است. تمامی عملیات مالی با استفاده از درگاه‌های معتبر شاپرک و با رعایت 
                بالاترین استانداردهای امنیتی انجام می‌شود.
              </p>
              <p className="text-gray-600 leading-8 mb-6">
                ما متعهد به ارائه خدمات با کیفیت و قابل اعتماد هستیم. حریم خصوصی و امنیت اطلاعات 
                کاربران اولویت اصلی ماست.
              </p>
              <div className="flex gap-4">
                <EnamadBadge />
              </div>
            </div>
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200">
              <div className="grid grid-cols-2 gap-6">
                <div className="text-center p-4">
                  <div className="text-3xl font-bold text-primary-600 mb-1">+۱۰۰۰</div>
                  <div className="text-sm text-gray-500">کاربر فعال</div>
                </div>
                <div className="text-center p-4">
                  <div className="text-3xl font-bold text-primary-600 mb-1">+۵۰۰۰</div>
                  <div className="text-sm text-gray-500">تراکنش موفق</div>
                </div>
                <div className="text-center p-4">
                  <div className="text-3xl font-bold text-primary-600 mb-1">۹۹.۹٪</div>
                  <div className="text-sm text-gray-500">آپتایم سرور</div>
                </div>
                <div className="text-center p-4">
                  <div className="text-3xl font-bold text-primary-600 mb-1">۲۴/۷</div>
                  <div className="text-sm text-gray-500">پشتیبانی</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-primary-700">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">همین الان شروع کنید</h2>
          <p className="text-primary-100 text-lg mb-8">ثبت‌نام رایگان است و تنها چند دقیقه زمان می‌برد.</p>
          {!user && (
            <Link to="/register"
              className="inline-block bg-white text-primary-700 px-10 py-3 rounded-xl font-bold text-lg hover:bg-gray-100 transition-colors">
              ایجاد حساب رایگان
            </Link>
          )}
        </div>
      </section>
    </div>
  );
}
