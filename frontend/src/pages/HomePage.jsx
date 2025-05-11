import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './HomePage.css';

function HomePage() {
  const { currentUser } = useAuth();
  const [hoveredButton, setHoveredButton] = useState(null);
  const canvasRef = useRef(null);
  
  // Initialize and animate the particle sphere
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const particles = [];
    let animationFrameId;
    let width = canvas.width;
    let height = canvas.height;
    
    // Set canvas dimensions
    const updateCanvasSize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      width = canvas.width;
      height = canvas.height;
    };
    
    updateCanvasSize();
    window.addEventListener('resize', updateCanvasSize);
    
    // Create particles
    const createParticles = () => {
      const particleCount = 200;
      
      for (let i = 0; i < particleCount; i++) {
        // Create points on a sphere using spherical coordinates
        const theta = Math.random() * Math.PI * 2; // Angle around y-axis
        const phi = Math.acos((Math.random() * 2) - 1); // Angle from y-axis
        const r = 150 + Math.random() * 30; // Base radius with some variance
        
        // Convert to Cartesian coordinates
        const x = r * Math.sin(phi) * Math.cos(theta);
        const y = r * Math.sin(phi) * Math.sin(theta);
        const z = r * Math.cos(phi);
        
        particles.push({
          x, y, z,
          size: 1 + Math.random() * 3,
          speed: 0.002 + Math.random() * 0.005,
          opacity: 0.3 + Math.random() * 0.7,
          offset: Math.random() * Math.PI * 2
        });
      }
    };
    
    createParticles();
    
    // Animation loop
    let time = 0;
    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      time += 0.01;
      
      // Draw glow in the center
      const gradient = ctx.createRadialGradient(
        width / 2, height / 2, 0,
        width / 2, height / 2, 150
      );
      gradient.addColorStop(0, 'rgba(56, 189, 248, 0.3)');
      gradient.addColorStop(1, 'rgba(56, 189, 248, 0)');
      
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(width / 2, height / 2, 150, 0, Math.PI * 2);
      ctx.fill();
      
      // Sort particles by z-index for proper rendering
      const sortedParticles = [...particles].sort((a, b) => b.z - a.z);
      
      // Draw particles
      sortedParticles.forEach(particle => {
        // Add wave movement
        const waveX = Math.sin(time + particle.offset) * 10;
        const waveY = Math.cos(time + particle.offset) * 10;
        
        // Simple perspective projection
        const scale = 1000 / (1000 - particle.z);
        const x = width / 2 + (particle.x + waveX) * scale;
        const y = height / 2 + (particle.y + waveY) * scale;
        const size = particle.size * scale;
        const opacity = particle.opacity * (1 + particle.z / 300);
        
        // Only draw particles that are in view
        if (x > -size && x < width + size && y > -size && y < height + size) {
          ctx.beginPath();
          ctx.arc(x, y, size, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(147, 197, 253, ${opacity})`;
          ctx.fill();
        }
      });
      
      // Connect nearby particles with lines
      sortedParticles.forEach((p1, i) => {
        for (let j = i + 1; j < Math.min(i + 5, sortedParticles.length); j++) {
          const p2 = sortedParticles[j];
          const dx = (p1.x + Math.sin(time + p1.offset) * 10) - (p2.x + Math.sin(time + p2.offset) * 10);
          const dy = (p1.y + Math.cos(time + p1.offset) * 10) - (p2.y + Math.cos(time + p2.offset) * 10);
          const dz = p1.z - p2.z;
          const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
          
          if (distance < 70) {
            const scale1 = 1000 / (1000 - p1.z);
            const scale2 = 1000 / (1000 - p2.z);
            
            const x1 = width / 2 + (p1.x + Math.sin(time + p1.offset) * 10) * scale1;
            const y1 = height / 2 + (p1.y + Math.cos(time + p1.offset) * 10) * scale1;
            
            const x2 = width / 2 + (p2.x + Math.sin(time + p2.offset) * 10) * scale2;
            const y2 = height / 2 + (p2.y + Math.cos(time + p2.offset) * 10) * scale2;
            
            const opacity = 0.5 * Math.max(0, 1 - distance / 70) * 
                            Math.min(p1.opacity, p2.opacity);
            
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = `rgba(147, 197, 253, ${opacity})`;
            ctx.stroke();
          }
        }
      });
      
      animationFrameId = requestAnimationFrame(animate);
    };
    
    animate();
    
    return () => {
      window.removeEventListener('resize', updateCanvasSize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);
  
  return (
    <div className="home-container">
      {/* Main content card with glass effect */}
      <div className="glass-card">
        {/* Content section */}
        <div className="content-section">
          <h1 className="main-heading">
            <span className="heading-welcome">Welcome to</span>
            <span className="heading-highlight">FutureSelf</span>
            <span className="heading-user">{currentUser?.username || 'User'}!</span>
          </h1>
          
          <p className="main-description">
            Begin your journey to connect with your future self and explore memories that haven't happened yet.
          </p>
          
          <div className="button-container">
            <Link 
              to="/memories" 
              className={`action-button memories-button ${hoveredButton === 'memories' ? 'hovered' : ''}`}
              onMouseEnter={() => setHoveredButton('memories')}
              onMouseLeave={() => setHoveredButton(null)}
            >
              <svg className="button-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" 
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              View Memories
            </Link>
            
            <Link 
              to="/conversation" 
              className={`action-button conversation-button ${hoveredButton === 'conversation' ? 'hovered' : ''}`}
              onMouseEnter={() => setHoveredButton('conversation')}
              onMouseLeave={() => setHoveredButton(null)}
            >
              <svg className="button-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" 
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Chat with Future Self
            </Link>
          </div>
          
          {/* Trust indicators */}
          <div className="trust-section">
            <p className="trust-heading">Trusted by forward-thinking individuals</p>
            <div className="trust-logos">
              <div className="trust-logo"></div>
              <div className="trust-logo"></div>
              <div className="trust-logo"></div>
              <div className="trust-logo"></div>
            </div>
          </div>
        </div>
        
        {/* Particle sphere visualization */}
        <div className="sphere-container">
          <canvas ref={canvasRef} className="particle-canvas"></canvas>
        </div>
      </div>
      
      {/* Background color blobs */}
      <div className="color-blob color-blob-1"></div>
      <div className="color-blob color-blob-2"></div>
    </div>
  );
}

export default HomePage;