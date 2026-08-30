export const AVATAR_IDS = [
  'avatar-01',
  'avatar-02',
  'avatar-03',
  'avatar-04',
  'avatar-05',
  'avatar-06',
  'avatar-07',
  'avatar-08',
];

export const DEFAULT_AVATAR_ID = 'avatar-01';

export function normalizeAvatarId(value) {
  if (typeof value !== 'string') return null;
  const normalized = value.trim().toLowerCase();
  return AVATAR_IDS.includes(normalized) ? normalized : null;
}

export function getAvatarAssetPath(avatarId) {
  const normalized = normalizeAvatarId(avatarId) || DEFAULT_AVATAR_ID;
  return `/avatars/${normalized}.svg`;
}

export function getAvatarSource(value) {
  if (!value) return getAvatarAssetPath(DEFAULT_AVATAR_ID);
  if (typeof value === 'string') {
    const normalized = normalizeAvatarId(value);
    return normalized ? getAvatarAssetPath(normalized) : getAvatarAssetPath(DEFAULT_AVATAR_ID);
  }
  if (typeof value === 'object') {
    const localId = value.avatarId || value.avatar;
    return getAvatarSource(localId);
  }
  return getAvatarAssetPath(DEFAULT_AVATAR_ID);
}
