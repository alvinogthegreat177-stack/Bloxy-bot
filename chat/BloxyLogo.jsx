import React from 'react';

export default function BloxyLogo({ size = 32, showText = true }) {
  return (
    <div className="flex items-center gap-2.5">
      <img
        src="https://media.base44.com/images/public/6a415277171cff3034584f35/6f17cca71_image.png"
        alt="Bloxy-bot"
        className="rounded-lg"
        style={{ width: size, height: size }}
      />
      {showText && (
        <span className="font-bold text-lg tracking-tight">
          <span className="gradient-text">Bloxy-bot</span>
          <span className="text-muted-foreground font-medium ml-1 text-sm">AI</span>
        </span>
      )}
    </div>
  );
}
