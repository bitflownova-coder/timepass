interface LogoProps {
  className?: string
}

export function Logo({ className = "" }: LogoProps) {
  return (
    <div className={`flex items-center ${className}`}>
      <svg 
        viewBox="0 0 800 200" 
        className="h-10 w-auto"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <g>
          <text x="40" y="50" fontFamily="monospace" fontSize="14" fill="currentColor" opacity="0.4" letterSpacing="2">
            000
          </text>
          <text x="40" y="65" fontFamily="monospace" fontSize="14" fill="currentColor" opacity="0.4" letterSpacing="2">
            000
          </text>
          <text x="40" y="80" fontFamily="monospace" fontSize="14" fill="currentColor" opacity="0.4" letterSpacing="2">
            010
          </text>
          <text x="40" y="95" fontFamily="monospace" fontSize="14" fill="currentColor" opacity="0.4" letterSpacing="2">
            01&#60;
          </text>
          <text x="40" y="110" fontFamily="monospace" fontSize="14" fill="currentColor" opacity="0.4" letterSpacing="2">
            101
          </text>
        </g>
        
        <g>
          <text x="150" y="65" fontFamily="monospace" fontSize="14" fill="currentColor" opacity="0.4" letterSpacing="2">
            011  010
          </text>
          <text x="150" y="80" fontFamily="monospace" fontSize="14" fill="currentColor" opacity="0.4" letterSpacing="2">
            000  100
          </text>
          <text x="150" y="95" fontFamily="monospace" fontSize="14" fill="currentColor" opacity="0.4" letterSpacing="2">
            010  000
          </text>
        </g>

        <text x="280" y="100" fontFamily="'Inter', sans-serif" fontSize="72" fill="#7dd3fc" fontWeight="700" letterSpacing="4">
          Flow
        </text>
        
        <text x="280" y="150" fontFamily="'Inter', sans-serif" fontSize="32" fill="currentColor" fontWeight="400" letterSpacing="8">
          N O V A
        </text>
      </svg>
    </div>
  )
}
