import React from 'react';
import { getAvatarSource } from '../../utils/avatars';

const sizeMap = {
  xs: 'h-6 w-6 text-[10px]',
  sm: 'h-8 w-8 text-[11px]',
  md: 'h-10 w-10 text-xs',
  lg: 'h-14 w-14 text-lg',
  xl: 'h-20 w-20 text-2xl',
};

export function AvatarDisplay({
  profile = null,
  avatarId = null,
  name = 'User',
  size = 'md',
  className = '',
  fallbackText = null,
}) {
  const value = profile && (profile.avatarId || profile.avatar) ? (profile.avatarId || profile.avatar) : avatarId;
  const src = getAvatarSource(value);
  const initial = (fallbackText ?? name ?? 'U').toString().trim().charAt(0).toUpperCase() || 'U';
  const sizeClass = sizeMap[size] || sizeMap.md;

  return (
    <div className={`relative inline-flex items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-gradient-to-br from-indigo-100 to-sky-100 text-indigo-700 shadow-sm ${sizeClass} ${className}`}>
      <img
        src={src}
        alt={name || 'User avatar'}
        className="h-full w-full object-cover"
        onError={(event) => {
          event.currentTarget.style.display = 'none';
          const fallback = event.currentTarget.parentElement?.querySelector('[data-fallback]');
          if (fallback) fallback.style.display = 'flex';
        }}
      />
      <div data-fallback className="hidden h-full w-full items-center justify-center text-center font-bold" aria-hidden="true">
        {initial}
      </div>
    </div>
  );
}
