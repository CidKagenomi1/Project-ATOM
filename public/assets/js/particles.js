/**
 * A.T.O.M. Vapor Chamber Background Particle Simulator
 * Mimics decay tracks of uranium inside a cloud/vapor chamber.
 * Generates alpha (thick/straight), beta (thin/erratic), and gamma (faint sparks) paths.
 */
class VaporChamber {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.tracks = [];
    this.animationFrameId = null;
    this.resizeObserver = null;
    
    this.init();
  }
  
  init() {
    this.resize();
    const container = this.canvas.parentElement;
    if (container && window.ResizeObserver) {
      this.resizeObserver = new ResizeObserver(() => this.resize());
      this.resizeObserver.observe(container);
    } else {
      window.addEventListener('resize', () => this.resize());
    }
    
    // Start simulation loop
    this.animate();
  }
  
  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
  }
  
  spawnTrack(fromCenter = false) {
    const w = this.canvas.width;
    const h = this.canvas.height;
    if (w === 0 || h === 0) return;
    
    let x, y;
    if (fromCenter) {
      x = w / 2;
      y = h / 2;
    } else {
      x = Math.random() * w;
      y = Math.random() * h;
    }
    
    const r = Math.random();
    // 30% alpha, 50% beta, 20% gamma
    const type = r < 0.3 ? 'alpha' : (r < 0.8 ? 'beta' : 'gamma');
    
    let angle = Math.random() * Math.PI * 2;
    let speed, maxAge, decay, curve;
    
    if (type === 'alpha') {
      // Alpha: thick, straight, fast, short path
      speed = 3.5 + Math.random() * 3.5;
      maxAge = 15 + Math.random() * 15;
      decay = 0.97;
      curve = 0;
    } else if (type === 'beta') {
      // Beta: medium speed, thin, highly erratic/curly, longer path
      speed = 2.0 + Math.random() * 2.0;
      maxAge = 35 + Math.random() * 25;
      decay = 0.98;
      curve = 0.18; // Angle perturbation magnitude
    } else {
      // Gamma: thin, short faint sparks
      speed = 1.0 + Math.random() * 1.5;
      maxAge = 10 + Math.random() * 10;
      decay = 0.94;
      curve = 0.4;
    }
    
    this.tracks.push({
      type,
      points: [{x, y}],
      curX: x,
      curY: y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      angle,
      speed,
      decay,
      curve,
      maxAge,
      age: 0,
      active: true,
      opacity: 1.0,
      fadeSpeed: 0.006 + Math.random() * 0.008
    });
  }
  
  update() {
    // Spawn ambient & core decay tracks
    if (Math.random() < 0.035 && this.tracks.length < 25) {
      // 65% spawn from center logo, 35% from ambient positions
      const fromCenter = Math.random() < 0.65;
      this.spawnTrack(fromCenter);
    }
    
    for (let i = this.tracks.length - 1; i >= 0; i--) {
      const t = this.tracks[i];
      
      if (t.active) {
        t.age++;
        
        // Beta erratic curvature logic
        if (t.curve > 0) {
          t.angle += (Math.random() - 0.5) * t.curve;
          t.vx = Math.cos(t.angle) * t.speed;
          t.vy = Math.sin(t.angle) * t.speed;
        }
        
        t.curX += t.vx;
        t.curY += t.vy;
        t.points.push({x: t.curX, y: t.curY});
        
        t.speed *= t.decay;
        t.vx *= t.decay;
        t.vy *= t.decay;
        
        if (t.age >= t.maxAge || t.speed < 0.15) {
          t.active = false;
        }
      } else {
        // Fade out finished tracks
        t.opacity -= t.fadeSpeed;
        if (t.opacity <= 0) {
          this.tracks.splice(i, 1);
        }
      }
    }
  }
  
  draw() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    for (const t of this.tracks) {
      if (t.points.length < 2) continue;
      
      // 1. Draw wide blurry condensation glow
      this.ctx.beginPath();
      this.ctx.moveTo(t.points[0].x, t.points[0].y);
      for (let i = 1; i < t.points.length; i++) {
        this.ctx.lineTo(t.points[i].x, t.points[i].y);
      }
      this.ctx.strokeStyle = `rgba(255, 255, 255, ${t.opacity * 0.045})`;
      this.ctx.lineWidth = t.type === 'alpha' ? 8.0 : 4.0;
      this.ctx.lineCap = 'round';
      this.ctx.lineJoin = 'round';
      this.ctx.stroke();
      
      // 2. Draw thin sharp core line
      this.ctx.beginPath();
      this.ctx.moveTo(t.points[0].x, t.points[0].y);
      for (let i = 1; i < t.points.length; i++) {
        this.ctx.lineTo(t.points[i].x, t.points[i].y);
      }
      this.ctx.strokeStyle = `rgba(255, 255, 255, ${t.opacity * 0.2})`;
      this.ctx.lineWidth = t.type === 'alpha' ? 2.0 : 0.8;
      this.ctx.stroke();
      
      // 3. Draw random droplet sparks along the active tip
      if (t.active && Math.random() < 0.35) {
        this.ctx.beginPath();
        this.ctx.arc(t.curX, t.curY, (t.type === 'alpha' ? 1.5 : 0.8) * Math.random(), 0, Math.PI * 2);
        this.ctx.fillStyle = `rgba(255, 255, 255, ${t.opacity * 0.35})`;
        this.ctx.fill();
      }
    }
  }
  
  animate() {
    this.update();
    this.draw();
    this.animationFrameId = requestAnimationFrame(() => this.animate());
  }
  
  destroy() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  }
}
window.VaporChamber = VaporChamber;

class BubblesFog {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.animationFrameId = null;
    this.resizeObserver = null;
    
    this.init();
  }

  init() {
    this.resize();
    const container = this.canvas.parentElement;
    if (container && window.ResizeObserver) {
      this.resizeObserver = new ResizeObserver(() => this.resize());
      this.resizeObserver.observe(container);
    } else {
      window.addEventListener('resize', () => this.resize());
    }

    // Initialize particles
    this.spawnParticles(15);
    
    this.animate();
  }

  resize() {
    const parent = this.canvas.parentElement;
    // Set canvas size to the scrollable content size of parent container so it covers everything
    this.canvas.width = parent.scrollWidth || parent.clientWidth;
    this.canvas.height = parent.scrollHeight || parent.clientHeight;
  }

  spawnParticles(count) {
    for (let i = 0; i < count; i++) {
      this.particles.push(this.createParticle(true));
    }
  }

  createParticle(randomY = false) {
    const w = this.canvas.width || window.innerWidth;
    const h = this.canvas.height || window.innerHeight;
    
    // Position primarily at the bottom half of the container, but drift up
    const minY = h * 0.4;
    const maxY = h;
    const y = randomY ? (minY + Math.random() * (maxY - minY)) : (h + 100);
    
    return {
      x: Math.random() * w,
      y: y,
      vx: (Math.random() - 0.5) * 0.5, // Horizontal drift speed
      vy: -0.05 - Math.random() * 0.1,  // Slow vertical drift upwards
      radius: 100 + Math.random() * 100,
      opacity: 0.01 + Math.random() * 0.04,
      maxOpacity: 0.03 + Math.random() * 0.05,
      colorType: Math.random() < 0.4 ? 'gold' : 'white',
      growth: 0.005 + Math.random() * 0.005,
      age: 0,
      maxAge: 1200 + Math.random() * 800
    };
  }

  update() {
    const w = this.canvas.width;
    const h = this.canvas.height;
    if (w === 0 || h === 0) return;

    // Maintain around 15-30 active fog puffs
    const targetCount = Math.max(15, Math.floor(h / 80));
    while (this.particles.length < targetCount) {
      this.particles.push(this.createParticle(false));
    }

    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.age++;

      // Drift physics
      p.x += p.vx;
      p.y += p.vy;
      p.radius += p.growth;

      // Randomize horizontal drift direction slightly
      if (Math.random() < 0.008) {
        p.vx += (Math.random() - 0.5) * 0.12;
        // Limit velocity
        p.vx = Math.max(-0.5, Math.min(0.5, p.vx));
      }

      // Fade in at start, fade out towards the end of lifetime or when drifting too high
      if (p.age < 150) {
        p.opacity = (p.age / 150) * p.maxOpacity;
      } else if (p.age > p.maxAge - 200) {
        const remaining = p.maxAge - p.age;
        p.opacity = (remaining / 200) * p.maxOpacity;
      } else {
        p.opacity = p.maxOpacity;
      }

      // Extra fade out if it gets near the top 30% of canvas
      if (p.y < h * 0.3) {
        const topFade = Math.max(0, p.y / (h * 0.3));
        p.opacity *= topFade;
      }

      // Remove out of bounds or dead particles
      if (p.age >= p.maxAge || p.y < -p.radius || p.opacity <= 0) {
        this.particles.splice(i, 1);
      }
    }
  }

  draw() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    for (const p of this.particles) {
      this.ctx.beginPath();
      const grad = this.ctx.createRadialGradient(p.x, p.y, p.radius * 0.1, p.x, p.y, p.radius);
      
      if (p.colorType === 'gold') {
        grad.addColorStop(0, `rgba(201, 162, 39, ${p.opacity})`);
        grad.addColorStop(0.5, `rgba(201, 162, 39, ${p.opacity * 0.4})`);
        grad.addColorStop(1, 'rgba(201, 162, 39, 0)');
      } else {
        grad.addColorStop(0, `rgba(255, 255, 255, ${p.opacity})`);
        grad.addColorStop(0.5, `rgba(255, 255, 255, ${p.opacity * 0.3})`);
        grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
      }
      
      this.ctx.fillStyle = grad;
      this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      this.ctx.fill();
    }
  }

  animate() {
    this.update();
    this.draw();
    this.animationFrameId = requestAnimationFrame(() => this.animate());
  }

  destroy() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  }
}
window.BubblesFog = BubblesFog;
