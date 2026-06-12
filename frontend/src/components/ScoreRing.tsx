import { useEffect, useState } from 'react'

interface ScoreRingProps {
  score: number
  maxScore?: number
  size?: number
  label?: string
}

export default function ScoreRing({ score, maxScore = 100, size = 100, label }: ScoreRingProps) {
  const [animated, setAnimated] = useState(0)
  const radius = 40
  const circumference = 2 * Math.PI * radius
  const percentage = score / maxScore

  const strokeColor =
    percentage >= 0.8 ? '#10B981' :
    percentage >= 0.6 ? '#F59E0B' :
    '#EF4444'

  const glowColor = strokeColor

  useEffect(() => {
    const timeout = setTimeout(() => setAnimated(score), 100)
    return () => clearTimeout(timeout)
  }, [score])

  const offset = circumference - (animated / maxScore) * circumference

  return (
    <div className="score-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 100 100">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <circle className="score-ring-track" cx="50" cy="50" r={radius} />
        <circle
          className="score-ring-fill"
          cx="50" cy="50" r={radius}
          stroke={strokeColor}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          filter="url(#glow)"
          style={{
            transition: 'stroke-dashoffset 1.2s cubic-bezier(0.34, 1.56, 0.64, 1)',
            filter: `drop-shadow(0 0 6px ${glowColor})`
          }}
        />
      </svg>
      <div className="score-ring-label">
        <div className="score-number" style={{ color: strokeColor }}>{score}</div>
        <div className="score-unit">{label || `/ ${maxScore}`}</div>
      </div>
    </div>
  )
}
