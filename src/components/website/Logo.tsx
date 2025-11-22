interface LogoProps {
  className?: string
}

export function Logo({ className = "" }: LogoProps) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg 
        width="40" 
        height="40" 
        viewBox="0 0 40 40" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
      >
        <rect width="40" height="40" rx="8" fill="url(#gradient)" />
        <path 
          d="M20 10 L28 20 L20 30 L12 20 Z" 
          fill="white" 
          opacity="0.9"
        />
        <circle cx="20" cy="20" r="4" fill="white" />
        <defs>
          <linearGradient id="gradient" x1="0" y1="0" x2="40" y2="40">
            <stop offset="0%" stopColor="oklch(0.42 0.18 264)" />
            <stop offset="100%" stopColor="oklch(0.87 0.15 95)" />
          </linearGradient>
        </defs>
      </svg>
      <div className="flex flex-col">
        <span className="text-lg font-bold tracking-tight">BITFLOW NOVA</span>
        <span className="text-xs text-muted-foreground font-medium">Design. Protect. automate.</span>
      </div>
    </div>
  )
}
