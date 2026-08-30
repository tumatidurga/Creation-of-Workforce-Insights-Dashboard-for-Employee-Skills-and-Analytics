import React, { useMemo, useState } from 'react';
import { ArrowRight, LockKeyhole, UserRound, Eye, EyeOff } from 'lucide-react';

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function isValidEmpId(value) {
  return /^EMP\d{6,}$/.test(value);
}

function isValidManagerId(value) {
  return /^MGR\d{6,}$/.test(value);
}

function isValidWorkforceIdentifier(value) {
  return isValidEmpId(value) || isValidManagerId(value);
}

export function LoginPage({ onLogin, isLoading = false, authError = null }) {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotIdentifier, setForgotIdentifier] = useState('');
  const [forgotSent, setForgotSent] = useState(false);

  const identifierLabel = useMemo(() => {
    const trimmed = identifier.trim();
    if (!trimmed) return 'Employee ID, Manager ID, or email is required.';
    if (trimmed.includes('@')) {
      return isValidEmail(trimmed) ? '' : 'Please enter a valid email address.';
    }
    return isValidWorkforceIdentifier(trimmed) ? '' : 'Employee ID or Manager ID format is invalid.';
  }, [identifier]);

  const validateForm = () => {
    const nextErrors = {};
    const trimmedIdentifier = identifier.trim();
    if (!trimmedIdentifier) {
      nextErrors.identifier = 'Employee ID, Manager ID, or email is required.';
    } else if (trimmedIdentifier.includes('@') && !isValidEmail(trimmedIdentifier)) {
      nextErrors.identifier = 'Please enter a valid email address.';
    } else if (!trimmedIdentifier.includes('@') && !isValidWorkforceIdentifier(trimmedIdentifier)) {
      nextErrors.identifier = 'Employee ID or Manager ID format is invalid.';
    }

    if (!password.trim()) {
      nextErrors.password = 'Password is required.';
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!validateForm()) {
      return;
    }

    await onLogin({
      identifier: identifier.trim(),
      password: password.trim()
    });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-10">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-lg shadow-slate-200/70 ring-1 ring-slate-100">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-md shadow-indigo-200">
            <LockKeyhole className="h-7 w-7" />
          </div>
          <div className="text-xs font-bold uppercase tracking-[0.26em] text-indigo-600">NEXUS.AI</div>
          <div className="mt-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Enterprise HRMS</div>
        </div>

        <div className="mb-8 text-left">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Welcome back</h1>
          <p className="mt-2 text-sm text-slate-500">Sign in to your workforce workspace</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <div>
            <label htmlFor="identifier" className="mb-2 block text-sm font-semibold text-slate-700">
              Employee ID / Manager ID / Email
            </label>
            <div className="relative">
              <UserRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="identifier"
                name="identifier"
                type="text"
                autoComplete="username"
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
                className={`w-full rounded-xl border bg-slate-50 py-3 pl-10 pr-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-200 ${errors.identifier ? 'border-rose-300 bg-rose-50' : 'border-slate-200'}`}
                placeholder="EMP000001, MGR000001, or name@company.com"
                aria-invalid={Boolean(errors.identifier)}
                aria-describedby={errors.identifier ? 'identifier-error' : undefined}
              />
            </div>
            {(errors.identifier || identifierLabel) && (
              <div id="identifier-error" className="mt-2 text-xs text-rose-600">
                {errors.identifier || identifierLabel}
              </div>
            )}
          </div>

          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-semibold text-slate-700">
              Password
            </label>
            <div className="relative">
              <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className={`w-full rounded-xl border bg-slate-50 py-3 pl-10 pr-10 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-200 ${errors.password ? 'border-rose-300 bg-rose-50' : 'border-slate-200'}`}
                placeholder="Enter your password"
                aria-invalid={Boolean(errors.password)}
                aria-describedby={errors.password ? 'password-error' : undefined}
              />

              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 inline-flex items-center justify-center rounded focus:outline-none focus:ring-2 focus:ring-indigo-200 p-1 text-slate-500 hover:text-slate-700"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.password && (
              <div id="password-error" className="mt-2 text-xs text-rose-600">
                {errors.password}
              </div>
            )}

            <div className="mt-2 text-right">
              <button
                type="button"
                onClick={() => { setShowForgot(true); setForgotSent(false); }}
                className="text-xs font-medium text-indigo-600 hover:underline"
              >
                Forgot Password?
              </button>
            </div>

            {showForgot && (
              <div className="mt-3 rounded-lg border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
                {!forgotSent ? (
                  <>
                    <div className="mb-2 font-semibold">Password reset (not implemented)</div>
                    <p className="mb-2 text-xs text-slate-500">The backend password-reset endpoint is not available. To enable secure password resets, implement a server-side flow (POST /api/auth/password-reset-request and POST /api/auth/password-reset/confirm) that sends a time-limited token to the user's email. Do not reveal account existence in responses.</p>
                    <label className="sr-only" htmlFor="forgot-identifier">Employee ID or email</label>
                    <input id="forgot-identifier" type="text" value={forgotIdentifier} onChange={(e) => setForgotIdentifier(e.target.value)} placeholder="EMP000001 or name@company.com" className="w-full rounded-md border border-slate-200 bg-white py-2 px-3 text-sm" />
                    <div className="mt-2 flex justify-end gap-2">
                      <button type="button" onClick={() => { setShowForgot(false); setForgotIdentifier(''); setForgotSent(false); }} className="text-xs text-slate-500 hover:underline">Cancel</button>
                      <button type="button" onClick={() => { setForgotSent(true); }} className="rounded-md bg-indigo-600 px-3 py-1 text-xs text-white">Request reset</button>
                    </div>
                  </>
                ) : (
                  <div className="text-sm text-slate-700">If the account exists, a password reset link would be sent to the associated email. Implement server-side endpoints to enable this flow.</div>
                )}
              </div>
            )}
          </div>

          {authError && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {authError}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-indigo-400"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
            {!isLoading && <ArrowRight className="h-4 w-4" />}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500">Secure Workforce Access</div>
      </div>
    </div>
  );
}
