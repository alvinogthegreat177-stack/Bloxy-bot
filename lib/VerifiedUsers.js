// Add the email addresses that should show the verified badge.
// The badge only appears for users whose email matches one of these (case-insensitive).
export const VERIFIED_EMAILS = [
  "alvinogthegreat177@gmail.com",
  "alvinogthegreat177@outlook.com",
];

export function isVerifiedUser(email) {
  if (!email) return false;
  return VERIFIED_EMAILS.includes(email.toLowerCase());
}
