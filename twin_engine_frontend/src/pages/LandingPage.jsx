import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Utensils,
  Users,
  TrendingUp,
  Layers,
  Mail,
  Linkedin,
  Phone,
  Zap,
  LayoutDashboard,
  MapPin,
  Sparkles,
} from 'lucide-react';
import '../styles/landing.css';

/* ---- Theme constants ---- */
const COLORS = {
  pink1: '#FFAFCC',
  pink2: '#FFC7DD',
  pink3: '#FFE1ED',
  cyan1: '#A3F8F8',
  cyan2: '#A5E2E2',
  mauve1: '#DFBEBF',
  mauve2: '#E7A4A3',
  red1: '#FF9090',
  text: '#4A4A4A',
};

/* ---- Inline SVG animations ---- */

function WaiterAnimation() {
  return (
    <div style={{ width: 200, height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="lp-anim-bounce">
        <svg viewBox="0 0 200 200" style={{ width: 180, height: 180 }}>
          <ellipse cx="100" cy="180" rx="40" ry="10" fill={COLORS.text} opacity="0.1" />
          <path d="M60 140 Q80 150 100 140 T140 140" stroke={COLORS.text} strokeWidth="8" fill="none" strokeLinecap="round" />
          <rect x="40" y="125" width="120" height="10" rx="5" fill={COLORS.mauve2} />
          <path d="M60 125 A40 40 0 0 1 140 125" fill={COLORS.cyan1} stroke={COLORS.text} strokeWidth="4" />
          <circle cx="100" cy="85" r="8" fill={COLORS.red1} />
          <circle cx="80" cy="60" r="4" fill={COLORS.pink1} className="lp-anim-ping" />
          <circle cx="120" cy="50" r="3" fill={COLORS.cyan2} className="lp-anim-pulse" />
          <circle cx="100" cy="40" r="2" fill={COLORS.mauve1} className="lp-anim-bounce" />
        </svg>
      </div>
    </div>
  );
}

function ThinkingAnimation() {
  return (
    <div style={{ width: 80, height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%' }}>
        <circle cx="50" cy="50" r="30" fill="none" stroke={COLORS.cyan1} strokeWidth="4" strokeDasharray="10 5" className="lp-anim-spin" />
        <circle cx="50" cy="50" r="20" fill={COLORS.pink1} opacity="0.5" className="lp-anim-pulse" />
        <text x="50" y="65" textAnchor="middle" fontSize="40" fontWeight="bold" fill={COLORS.text} className="lp-anim-bounce">?</text>
      </svg>
    </div>
  );
}

/* ---- Status colours for the interactive demo ---- */
const STATUS_LIST = [
  { id: 'cyan',   name: 'Available',   bg: '#A3F8F8', text: 'Table is ready for new guests.' },
  { id: 'red',    name: 'Waiting',     bg: '#FF9090', text: 'Occupied, order placed, food pending.' },
  { id: 'green',  name: 'Served',      bg: '#A5E2E2', text: 'Guests enjoying their meal.' },
  { id: 'yellow', name: 'Alert',       bg: '#FFAFCC', text: 'Issue detected (Wrong order/Delay).' },
  { id: 'mauve',  name: 'Maintenance', bg: '#DFBEBF', text: 'Reserved or under maintenance.' },
];

const FEATURES = [
  {
    title: 'Real-Time 3D Orchestration',
    description: "A spatial digital twin of your floor plan. Monitor every table's heartbeat in real-time.",
    icon: <LayoutDashboard size={22} color="#4A4A4A" />,
    bg: COLORS.cyan1,
  },
  {
    title: 'AI Demand Forecasting',
    description: 'Predict busy hours and food demand before they happen using advanced ML models.',
    icon: <TrendingUp size={22} color="#4A4A4A" />,
    bg: COLORS.pink2,
  },
  {
    title: 'Staff Optimization',
    description: 'Dynamic scheduling logic that recommends the perfect number of chefs and waiters.',
    icon: <Users size={22} color="#4A4A4A" />,
    bg: COLORS.mauve1,
  },
  {
    title: 'Automated Insights',
    description: 'GPT-powered daily reports sent to your Cloudinary storage every night.',
    icon: <Zap size={22} color="#4A4A4A" />,
    bg: COLORS.cyan2,
  },
];

/* ==================================================================
   Landing Page
   ================================================================== */
export default function LandingPage() {
  const [isVisible, setIsVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('cyan');
  const [mobileMenu, setMobileMenu] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { setIsVisible(true); }, []);

  const activeBg = STATUS_LIST.find((s) => s.id === activeTab)?.bg || '#A3F8F8';

  return (
    <div className="lp">

      {/* ============ NAVIGATION ============ */}
      <nav className="lp-nav">
        <div className="lp-nav-inner">
          <div className="lp-brand">
            <div className="lp-brand-icon">
              <Layers size={18} color="#4A4A4A" />
            </div>
            <span className="lp-brand-text">
              TwinEngine <span>Hospitality</span>
            </span>
          </div>

          {/* Desktop */}
          <div className="lp-nav-links">
            <a href="#features">Solutions</a>
            <a href="#about">Our Team</a>
            <a href="#contact">Contact</a>
            <button className="lp-nav-login" onClick={() => navigate('/login')}>Login</button>
          </div>

          {/* Mobile */}
          <div className="lp-mob-ctrls">
            <button className="lp-mob-login" onClick={() => navigate('/login')}>Login</button>
            <button className="lp-hamburger" onClick={() => setMobileMenu(!mobileMenu)} aria-label="Menu">
              <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                {mobileMenu
                  ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
              </svg>
            </button>
          </div>
        </div>

        {mobileMenu && (
          <div className="lp-mob-menu">
            <a href="#features" onClick={() => setMobileMenu(false)}>Solutions</a>
            <a href="#about" onClick={() => setMobileMenu(false)}>Our Team</a>
            <a href="#contact" onClick={() => setMobileMenu(false)}>Contact</a>
          </div>
        )}
      </nav>

      {/* ============ HERO ============ */}
      <section className="lp-hero">
        <div className="lp-hero-glow1" />
        <div className="lp-hero-glow2" />

        <div className="lp-hero-content">
          <div className="lp-hero-badge" style={{ opacity: isVisible ? 1 : 0, transition: 'opacity 0.7s' }}>
            <Sparkles size={12} color="#E7A4A3" />
            <span>Enterprise Digital Twins</span>
          </div>

          <h1 style={{ opacity: isVisible ? 1 : 0, transform: isVisible ? 'none' : 'translateY(24px)', transition: 'all 0.7s 0.1s' }}>
            Modernizing <br />
            <span>Guest Experiences.</span>
          </h1>

          <p className="lp-hero-sub" style={{ opacity: isVisible ? 1 : 0, transform: isVisible ? 'none' : 'translateY(24px)', transition: 'all 0.7s 0.2s' }}>
            TwinEngine blends 3D visualization with predictive AI to help cafes and hotels master their floor health and operational flow.
          </p>

          <div className="lp-hero-anim" style={{ opacity: isVisible ? 1 : 0, transition: 'opacity 0.7s 0.3s' }}>
            <WaiterAnimation />
            <div className="lp-hero-tag">AI-Powered Service Orchestration</div>
          </div>
        </div>
      </section>

      {/* ============ STATUS ENGINE ============ */}
      <section className="lp-status">
        <div className="lp-wrap">
          <div className="lp-status-grid">
            {/* Floor grid */}
            <div className="lp-status-floor">
              <div className="lp-floor-wrap">
                <div className="lp-floor-glow" />
                <div className="lp-floor-card">
                  <div className="lp-floor-grid">
                    {[...Array(9)].map((_, i) => (
                      <div
                        key={i}
                        className={`lp-floor-unit ${i === 4 ? 'active' : ''}`}
                        style={i === 4 ? { background: activeBg } : undefined}
                      >
                        <Utensils size={20} color={i === 4 ? '#fff' : '#DFBEBF'} />
                        <span className="lp-floor-unit-label">Unit {i + 1}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="lp-legend">
              <h2>
                Visual <span>Status</span> Engine
              </h2>
              <p className="lp-legend-desc">
                Our 3D twin orchestration replaces confusing tables with a living map. Instantly spot delays, manage turnover, and ensure every guest feels seen.
              </p>

              <div className="lp-legend-list">
                {STATUS_LIST.map((s) => (
                  <button
                    key={s.id}
                    className={`lp-legend-btn ${activeTab === s.id ? 'active' : ''}`}
                    onClick={() => setActiveTab(s.id)}
                  >
                    <div className="lp-legend-dot" style={{ background: s.bg }} />
                    <div>
                      <span className="lp-legend-name">{s.name}</span>
                      <span className="lp-legend-text">{s.text}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============ FEATURES ============ */}
      <section id="features" className="lp-features">
        <div className="lp-wrap">
          <div className="lp-features-heading">
            <h2>Enterprise Capabilities</h2>
            <div className="lp-features-bar" />
          </div>

          <div className="lp-features-grid">
            {FEATURES.map((f, i) => (
              <div key={i} className="lp-feat-card" style={{ background: f.bg + '35' }}>
                <div className="lp-feat-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ TEAM ============ */}
      <section id="about" className="lp-team">
        <div className="lp-wrap-sm">
          <div className="lp-team-heading">
            <h2>Brains Behind TwinEngine</h2>
            <p>The Visionary Architects</p>
          </div>

          <div className="lp-team-grid">
            {/* Amrita */}
            <div className="lp-team-card pink">
              <div className="lp-team-photo">
                <img
                  src="https://media.licdn.com/dms/image/v2/D4D03AQH0YVGwtA99EQ/profile-displayphoto-crop_800_800/B4DZrJXRzEJ4AI-/0/1764314915321?e=1774483200&v=beta&t=DKCEtMyohjeSLAMGnGGOGoHzsCrVbyBrMpol56gCSHM"
                  alt="Amrita Singh"
                />
              </div>
              <h3>Amrita Singh</h3>
              <span className="lp-team-role">ML &amp; Strategy Lead</span>
              <p>
                Specializing in time-series forecasting and demand-driven logic to ensure your outlet never misses a beat.
              </p>
            </div>

            {/* Akshat */}
            <div className="lp-team-card cyan">
              <div className="lp-team-photo">
                <img
                  src="https://media.licdn.com/dms/image/v2/D4D03AQHXgSEqHtb_fw/profile-displayphoto-crop_800_800/B4DZrKqpNCHwAI-/0/1764336768583?e=1774483200&v=beta&t=FuRIz8aAb7l0on2Z-7aCVukM9X0M9l_wKUSsx4ZEp50"
                  alt="Akshat Gupta"
                />
              </div>
              <h3>Akshat Gupta</h3>
              <span className="lp-team-role">Systems &amp; Full-Stack Architect</span>
              <p>
                The engineer behind the 3D-graph architecture and real-time synchronization between the floor and the twin.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============ CONTACT ============ */}
      <section id="contact" className="lp-contact">
        <div className="lp-wrap-sm">
          <div className="lp-contact-card">
            <div className="lp-contact-glow" />
            <div className="lp-contact-inner">
              <h2>Let&apos;s Build Together</h2>
              <p className="lp-contact-desc">
                Whether you&apos;re a boutique cafe or a luxury hotel chain, TwinEngine is built to scale with you. Reach out directly.
              </p>

              <div className="lp-contact-grid">
                <div className="lp-contact-tile" style={{ background: '#F0FBFC' }}>
                  <Mail size={28} color="#A5E2E2" />
                  <span className="lp-contact-label">Email</span>
                  <span className="lp-contact-value">hello@twinengine.ai</span>
                </div>
                <div className="lp-contact-tile" style={{ background: '#FFE1ED' }}>
                  <Linkedin size={28} color="#E7A4A3" />
                  <span className="lp-contact-label">LinkedIn</span>
                  <span className="lp-contact-value">/in/twinengine-ai</span>
                </div>
                <div className="lp-contact-tile" style={{ background: '#FFF8F0' }}>
                  <Phone size={28} color="#FF9090" />
                  <span className="lp-contact-label">Contact</span>
                  <span className="lp-contact-value">+91 98765 43210</span>
                </div>
                <div className="lp-contact-tile" style={{ background: '#F5F5F5' }}>
                  <MapPin size={28} color="#4A4A4A" />
                  <span className="lp-contact-label">Location</span>
                  <span className="lp-contact-value">Tech District, IN</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============ FOOTER ============ */}
      <footer className="lp-footer">
        <div className="lp-footer-inner">
          <div className="lp-footer-icon">
            <Layers size={24} color="#A3F8F8" />
          </div>
          <p className="lp-footer-brand">TwinEngine</p>
          <div className="lp-footer-anim">
            <ThinkingAnimation />
            <p className="lp-footer-tag">
              Architecting Enterprise Intelligence for the Service Industry
            </p>
          </div>
          <div className="lp-footer-divider" />
          <p className="lp-footer-copy">Digitizing Hospitality Since 2024</p>
        </div>
      </footer>
    </div>
  );
}
