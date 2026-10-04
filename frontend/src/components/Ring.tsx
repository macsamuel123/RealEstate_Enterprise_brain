import { useEffect, useRef } from 'react';
import { RingState } from '@/types';
import './Ring.css';

interface RingProps {
  state: RingState;
  onClick?: () => void;
  volumeLevel?: number; // 0-1 for voice volume visualization in listening state
}

export const Ring = ({ state, onClick, volumeLevel = 0 }: RingProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const timeRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const animate = () => {
      timeRef.current += 1;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const baseRadius = 80;

      // Draw ring based on state
      if (state === 'idle') {
        drawIdleRing(ctx, centerX, centerY, baseRadius);
      } else if (state === 'listening') {
        drawListeningRing(ctx, centerX, centerY, baseRadius, timeRef.current, volumeLevel);
      } else if (state === 'speaking') {
        drawSpeakingRing(ctx, centerX, centerY, baseRadius, timeRef.current);
      }

      // Draw center dot
      ctx.fillStyle = '#00d4ff';
      ctx.beginPath();
      ctx.arc(centerX, centerY, 6, 0, Math.PI * 2);
      ctx.fill();

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [state, volumeLevel]);

  return (
    <div className={`ring-container ring-${state}`} onClick={onClick}>
      <canvas ref={canvasRef} width={280} height={280} className="ring-canvas" />
      <div className="ring-label">{state.charAt(0).toUpperCase() + state.slice(1)}</div>
    </div>
  );
};

function drawIdleRing(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  centerY: number,
  radius: number
) {
  // Static ring with subtle glow
  ctx.strokeStyle = 'rgba(0, 212, 255, 0.4)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
  ctx.stroke();

  // Outer faint ring
  ctx.strokeStyle = 'rgba(0, 212, 255, 0.2)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius + 12, 0, Math.PI * 2);
  ctx.stroke();
}

function drawListeningRing(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  centerY: number,
  radius: number,
  time: number,
  volumeLevel: number = 0
) {
  // Normalize volume to 0-1 range (RMS can go higher)
  const normalizedVolume = Math.min(volumeLevel * 50, 1);

  // Pulsing listening ring that expands with voice volume
  const basePulse = Math.sin(time * 0.05) * 0.2 + 0.6;
  const pulse = basePulse + normalizedVolume * 0.4;
  const ringRadius = radius + normalizedVolume * 8; // Expand ring with volume

  ctx.strokeStyle = `rgba(0, 212, 255, ${pulse * 0.8})`;
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(centerX, centerY, ringRadius, 0, Math.PI * 2);
  ctx.stroke();

  // Animated outer rings that pulse with voice
  for (let i = 1; i <= 3; i++) {
    const waveRadius = ringRadius + i * 15;
    const alpha = Math.max(0, 0.4 - (time % 20) / 50) * (1 - normalizedVolume * 0.5);
    ctx.strokeStyle = `rgba(0, 212, 255, ${alpha})`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(centerX, centerY, waveRadius, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Inner glow that brightens with speech
  ctx.fillStyle = `rgba(0, 212, 255, ${normalizedVolume * 0.15})`;
  ctx.beginPath();
  ctx.arc(centerX, centerY, ringRadius - 15, 0, Math.PI * 2);
  ctx.fill();
}

function drawSpeakingRing(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  centerY: number,
  radius: number,
  time: number
) {
  // Animated waveform ring for speaking
  const segments = 32;
  const waveHeight = 8;

  ctx.strokeStyle = '#00d4ff';
  ctx.lineWidth = 2;
  ctx.beginPath();

  for (let i = 0; i <= segments; i++) {
    const angle = (i / segments) * Math.PI * 2;
    const wave = Math.sin(angle * 3 + time * 0.1) * waveHeight;
    const x = centerX + Math.cos(angle) * (radius + wave);
    const y = centerY + Math.sin(angle) * (radius + wave);

    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  }

  ctx.stroke();

  // Pulse effect
  const pulse = Math.sin(time * 0.08) * 0.3 + 0.7;
  ctx.fillStyle = `rgba(0, 212, 255, ${pulse * 0.2})`;
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius - 15, 0, Math.PI * 2);
  ctx.fill();
}
