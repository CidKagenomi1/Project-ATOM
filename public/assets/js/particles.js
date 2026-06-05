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
