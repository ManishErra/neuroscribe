import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import apiClient from '@/api/axiosClient';
import { Alert, AlertDescription } from '@/components/ui/alert';
import Spinner from '@/components/common/Spinner';
import { Mail, Lock, User as UserIcon, ArrowRight, ShieldCheck, Brain } from 'lucide-react';

const registerSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      name: '',
      password: '',
      confirmPassword: '',
    },
  });

  async function onSubmit(data: RegisterFormValues) {
    setError('');
    try {
      await apiClient.post('/auth/register', {
        email: data.email,
        password: data.password,
        name: data.name,
      });
      navigate('/login', { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Registration failed');
    }
  }

  return (
    <div className="min-h-screen w-full flex flex-col md:flex-row bg-[#faf9f6]">
      {/* ── LEFT HERO PANEL (Desktop only) ────────────────────────── */}
      <div className="hidden md:flex md:w-1/2 bg-[#466551] flex-col justify-between p-12 text-white relative overflow-hidden">
        {/* Subtle decorative grid/nodes overlay */}
        <div className="absolute inset-0 opacity-10 pointer-events-none">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="1" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        {/* Logo Icon and Branding */}
        <div className="flex items-center gap-3 relative z-10">
          <div className="w-10 h-10 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center shadow-lg backdrop-blur-sm">
            <Brain className="h-5.5 w-5.5 text-white stroke-[2.2]" />
          </div>
          <div>
            <p className="text-sm font-bold tracking-wider uppercase text-white">NeuroScribe</p>
            <p className="text-[10px] text-white/70 font-medium tracking-widest uppercase">Clinical AI Intelligence</p>
          </div>
        </div>

        {/* Central Illustration Area */}
        <div className="flex flex-col items-center justify-center my-auto py-12 relative z-10">
          <svg className="w-64 h-64 text-white/90 drop-shadow-2xl" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <radialGradient id="sparkGrad" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#ffffff" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
              </radialGradient>
            </defs>
            {/* Glowing background circles */}
            <circle cx="100" cy="100" r="80" fill="url(#sparkGrad)" />
            <circle cx="100" cy="100" r="60" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 4" className="opacity-40 animate-[spin_60s_linear_infinite]" />
            <circle cx="100" cy="100" r="45" stroke="currentColor" strokeWidth="1.5" className="opacity-20" />
            
            {/* Styled Brain / Network Nodes */}
            <path d="M70,80 Q100,50 130,80 T100,140 Z" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
            <path d="M75,95 Q100,70 125,95 T100,135 Z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="opacity-60" />
            
            {/* Central glowing pulses */}
            <circle cx="100" cy="90" r="6" fill="currentColor" />
            <circle cx="70" cy="80" r="4" fill="currentColor" className="opacity-80" />
            <circle cx="130" cy="80" r="4" fill="currentColor" className="opacity-80" />
            <circle cx="100" cy="140" r="5" fill="currentColor" />
            
            {/* Floating particles */}
            <circle cx="50" cy="110" r="2.5" fill="currentColor" className="opacity-40" />
            <circle cx="150" cy="110" r="2.5" fill="currentColor" className="opacity-40" />
            <circle cx="80" cy="60" r="3" fill="currentColor" className="opacity-50" />
            <circle cx="120" cy="60" r="3" fill="currentColor" className="opacity-50" />
            <line x1="70" y1="80" x2="100" y2="90" stroke="currentColor" strokeWidth="1.5" className="opacity-50" />
            <line x1="130" y1="80" x2="100" y2="90" stroke="currentColor" strokeWidth="1.5" className="opacity-50" />
            <line x1="100" y1="90" x2="100" y2="140" stroke="currentColor" strokeWidth="1.5" className="opacity-50" />
          </svg>
          <div className="text-center mt-8 max-w-sm">
            <h2 className="text-2xl font-bold tracking-tight mb-2">Elevating clinical clarity</h2>
            <p className="text-sm text-white/80 leading-relaxed font-medium">
              The professional clinical intelligence assistant designed to ease documentation load and elevate care.
            </p>
          </div>
        </div>

        {/* Footer branding */}
        <div className="flex items-center justify-between text-xs text-white/60 relative z-10 border-t border-white/10 pt-4">
          <span>Version 0.1.0</span>
          <span>Secure. Audited. Compliant.</span>
        </div>
      </div>

      {/* ── RIGHT AUTH PANEL (Sign-up form) ─────────────────────── */}
      <div className="w-full md:w-1/2 flex items-center justify-center p-6 md:p-12">
        <div className="w-full max-w-md bg-white border border-[#E2E8E4] shadow-xl rounded-2xl p-8 transition-all">
          
          {/* Mobile view Logo branding */}
          <div className="flex items-center gap-3 mb-6 md:hidden">
            <div className="w-9 h-9 rounded-lg bg-[#466551] flex items-center justify-center shadow-md">
              <Brain className="h-4.5 w-4.5 text-white stroke-[2.2]" />
            </div>
            <div>
              <p className="text-sm font-bold tracking-wider text-[#1a1c1a]">NeuroScribe</p>
              <p className="text-[10px] text-[#424843]/70 font-semibold tracking-widest uppercase">Clinical AI Intelligence</p>
            </div>
          </div>

          <div className="mb-6">
            <h1 className="text-xl font-bold text-[#1a1c1a]">Create Account</h1>
            <p className="text-xs text-[#424843] mt-1">
              Register your profile to begin managing clinical documentation.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {error && (
              <Alert variant="destructive" className="bg-rose-50 border-rose-100 text-rose-800 rounded-lg">
                <AlertDescription className="text-xs font-semibold">{error}</AlertDescription>
              </Alert>
            )}

            {/* Name Input */}
            <div className="space-y-1.5">
              <label htmlFor="name" className="text-xs font-bold uppercase tracking-wider text-[#424843]">
                Full Name
              </label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-[#424843]/60" />
                <input
                  id="name"
                  type="text"
                  {...register('name')}
                  placeholder="Dr. Jane Doe"
                  className="w-full bg-white border border-[#c3c6d6] rounded-lg pl-10 pr-4 py-2.5 text-sm text-[#1a1c1a] placeholder:text-[#424843]/40 focus:outline-none focus:border-[#466551] focus:ring-2 focus:ring-[#466551]/10 transition-all"
                />
              </div>
              {errors.name && (
                <p className="text-[10px] font-bold text-rose-500">{errors.name.message}</p>
              )}
            </div>

            {/* Email Input */}
            <div className="space-y-1.5">
              <label htmlFor="email" className="text-xs font-bold uppercase tracking-wider text-[#424843]">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-[#424843]/60" />
                <input
                  id="email"
                  type="email"
                  {...register('email')}
                  placeholder="doctor@hospital.org"
                  className="w-full bg-white border border-[#c3c6d6] rounded-lg pl-10 pr-4 py-2.5 text-sm text-[#1a1c1a] placeholder:text-[#424843]/40 focus:outline-none focus:border-[#466551] focus:ring-2 focus:ring-[#466551]/10 transition-all"
                />
              </div>
              {errors.email && (
                <p className="text-[10px] font-bold text-rose-500">{errors.email.message}</p>
              )}
            </div>

            {/* Password Input */}
            <div className="space-y-1.5">
              <label htmlFor="password" className="text-xs font-bold uppercase tracking-wider text-[#424843]">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-[#424843]/60" />
                <input
                  id="password"
                  type="password"
                  {...register('password')}
                  placeholder="••••••••"
                  className="w-full bg-white border border-[#c3c6d6] rounded-lg pl-10 pr-4 py-2.5 text-sm text-[#1a1c1a] placeholder:text-[#424843]/40 focus:outline-none focus:border-[#466551] focus:ring-2 focus:ring-[#466551]/10 transition-all"
                />
              </div>
              {errors.password && (
                <p className="text-[10px] font-bold text-rose-500">{errors.password.message}</p>
              )}
            </div>

            {/* Confirm Password Input */}
            <div className="space-y-1.5">
              <label htmlFor="confirmPassword" className="text-xs font-bold uppercase tracking-wider text-[#424843]">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-[#424843]/60" />
                <input
                  id="confirmPassword"
                  type="password"
                  {...register('confirmPassword')}
                  placeholder="••••••••"
                  className="w-full bg-white border border-[#c3c6d6] rounded-lg pl-10 pr-4 py-2.5 text-sm text-[#1a1c1a] placeholder:text-[#424843]/40 focus:outline-none focus:border-[#466551] focus:ring-2 focus:ring-[#466551]/10 transition-all"
                />
              </div>
              {errors.confirmPassword && (
                <p className="text-[10px] font-bold text-rose-500">{errors.confirmPassword.message}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="w-full bg-[#466551] hover:bg-[#3b5443] text-white font-bold h-11 flex items-center justify-center gap-2 rounded-lg transition-colors shadow-sm text-sm"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <Spinner size="sm" />
              ) : (
                <>
                  <span>Create Account</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
            
            {/* Login Link */}
            <p className="text-xs text-center text-[#424843] font-semibold mt-4">
              Already have an account?{' '}
              <Link to="/login" className="text-[#466551] hover:underline font-bold">
                Sign in
              </Link>
            </p>
          </form>

          {/* HIPAA & BAA Compliance Seal */}
          <div className="flex items-center justify-center gap-2 border-t border-[#E2E8E4] mt-6 pt-5 text-[#424843]/60 text-[10px] font-bold uppercase tracking-widest">
            <ShieldCheck className="h-4.5 w-4.5 text-[#466551]" />
            <span>HIPAA & BAA Compliant Workspace</span>
          </div>

        </div>
      </div>
    </div>
  );
}
