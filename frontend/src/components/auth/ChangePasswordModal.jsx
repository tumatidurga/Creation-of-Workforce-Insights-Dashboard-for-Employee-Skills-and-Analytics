import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { api } from '../../services/api';

export function ChangePasswordModal({ show, onClose, currentPasswordPrefill, onPasswordChanged }) {
  const [currentPassword, setCurrentPassword] = useState(currentPasswordPrefill || '');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  if (!show) return null;

  const submit = async () => {
    setError(null);
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('All fields are required.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('New password and confirmation do not match.');
      return;
    }

    setLoading(true);
    try {
      await api.changePassword({ currentPassword, newPassword, confirmPassword });
      setSuccess(true);
      setLoading(false);
      if (onPasswordChanged) onPasswordChanged();
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Failed to change password.';
      setError(msg);
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="mx-auto w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h3 className="mb-2 text-lg font-semibold">Change Password</h3>
        <p className="mb-4 text-sm text-slate-500">Your account is currently using the default Employee ID password. You may change it now or keep using the default.</p>

        {error && <div className="mb-3 rounded border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700">{error}</div>}
        {success && <div className="mb-3 rounded border border-green-200 bg-green-50 p-2 text-xs text-green-700">Password changed successfully. Please sign in again with your new password.</div>}

        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-700">Current password</label>
            <div className="relative">
              <input type={showCurrent ? 'text' : 'password'} value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className="w-full rounded-md border border-slate-200 py-2 px-3 text-sm" />
              <button type="button" onClick={() => setShowCurrent(!showCurrent)} className="absolute right-2 top-2 text-slate-500">
                {showCurrent ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-700">New password</label>
            <div className="relative">
              <input type={showNew ? 'text' : 'password'} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full rounded-md border border-slate-200 py-2 px-3 text-sm" />
              <button type="button" onClick={() => setShowNew(!showNew)} className="absolute right-2 top-2 text-slate-500">
                {showNew ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-700">Confirm password</label>
            <div className="relative">
              <input type={showConfirm ? 'text' : 'password'} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full rounded-md border border-slate-200 py-2 px-3 text-sm" />
              <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute right-2 top-2 text-slate-500">
                {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-md bg-slate-100 px-3 py-1 text-sm text-slate-700">Cancel</button>
          <button onClick={submit} disabled={loading} className="rounded-md bg-indigo-600 px-3 py-1 text-sm text-white">{loading ? 'Updating...' : 'Update Password'}</button>
        </div>
      </div>
    </div>
  );
}
