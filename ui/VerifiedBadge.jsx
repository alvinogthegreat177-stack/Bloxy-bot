import React from 'react';

export default function VerifiedBadge({ size = 20 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ flexShrink: 0 }}
    >
      <title>This checkmark is awarded to the rightful owner of the platform or the admin contributor</title>
      {/* Scalloped badge shape — 12 rounded bumps around a circle */}
      <path
        d="M50 3
          C54 3 56.5 7 60 8.5
          C63.5 10 67.5 8 71 10
          C74.5 12 75 16.5 78 19
          C81 21.5 85.5 21.5 87.5 25
          C89.5 28.5 88 33 89.5 36.5
          C91 40 95 42.5 95 46.5
          C95 50.5 91 53 89.5 56.5
          C88 60 89.5 64.5 87.5 68
          C85.5 71.5 81 72 78 74.5
          C75 77 74.5 81.5 71 83.5
          C67.5 85.5 63.5 83.5 60 85
          C56.5 86.5 54 90.5 50 90.5
          C46 90.5 43.5 86.5 40 85
          C36.5 83.5 32.5 85.5 29 83.5
          C25.5 81.5 25 77 22 74.5
          C19 72 14.5 71.5 12.5 68
          C10.5 64.5 12 60 10.5 56.5
          C9 53 5 50.5 5 46.5
          C5 42.5 9 40 10.5 36.5
          C12 33 10.5 28.5 12.5 25
          C14.5 21.5 19 21.5 22 19
          C25 16.5 25.5 12 29 10
          C32.5 8 36.5 10 40 8.5
          C43.5 7 46 3 50 3Z"
        fill="#F97316"
      />
      {/* Bold white checkmark */}
      <path
        d="M30 50 L43 64 L70 36"
        stroke="white"
        strokeWidth="9"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}
