import { useState } from "react";
import { Link } from "react-router-dom";
import "../components/auth/styles.css";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(email.trim())) {
      setError("Please enter a valid email address.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    alert("Login successful. Backend connection will be added later.");
  };

  return (
    <main className="ff-login-shell">
      <div className="ff-login-card">
        <header className="ff-login-hero">
          <div className="ff-login-hero-bg" aria-hidden="true">
            <svg className="ff-hero-waves" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120" preserveAspectRatio="none">
              <path fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" d="M0,60 Q100,20 200,60 T400,55" />
              <path fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" d="M0,80 Q120,45 240,75 T400,70" />
              <path fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1" d="M0,95 Q80,70 200,90 T400,88" />
            </svg>

            <svg className="ff-hero-trees" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80" aria-hidden="true">
              <path fill="rgba(20,60,100,0.45)" d="M120 80 L135 35 L150 80 Z M145 80 L165 25 L185 80 Z M165 80 L180 40 L195 80 Z" />
            </svg>
          </div>

          <div className="ff-login-brand">
            <div className="ff-login-emblem" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" className="ff-emblem-svg">
                <defs>
                  <linearGradient id="ffSky" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#1e5a8a" />
                    <stop offset="100%" stopColor="#0a3d6e" />
                  </linearGradient>
                  <linearGradient id="ffField" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#2d8a4e" />
                    <stop offset="100%" stopColor="#1a5c36" />
                  </linearGradient>
                </defs>

                <circle cx="32" cy="32" r="30" fill="url(#ffSky)" />
                <ellipse cx="32" cy="44" rx="26" ry="14" fill="url(#ffField)" />
                <path fill="#fbbf24" d="M32 18a6 6 0 1 1 0.01 0z" />
                <path fill="#fcd34d" opacity="0.9" d="M18 38 Q32 32 46 38 L44 42 Q32 36 20 42 Z" />
                <path fill="#f97316" d="M28 8 Q32 2 36 8 Q34 14 32 18 Q30 14 28 8Z" />
                <path fill="#fb923c" d="M24 12 Q28 6 32 10 Q30 16 28 20 Q26 16 24 12Z" />
                <path fill="#ea580c" d="M36 10 Q40 6 44 12 Q40 18 38 20 Q36 16 36 10Z" />
              </svg>
            </div>

            <span className="ff-login-name">FireFusion</span>
          </div>

          <h1 className="ff-login-heading">Login to FireFusion</h1>
          <p className="ff-login-tagline">
            Access your account to monitor bushfires and risk alerts.
          </p>
        </header>

        <form className="ff-login-form" onSubmit={handleSubmit} noValidate>
          <label className="ff-label" htmlFor="email">Email</label>

          <div className="ff-field">
            <svg className="ff-field-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
              <polyline points="22,6 12,13 2,6" />
            </svg>

            <input
              type="email"
              id="email"
              className="ff-input"
              autoComplete="username"
              placeholder="Enter your email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <label className="ff-label" htmlFor="password">Password</label>

          <div className="ff-field ff-field-password">
            <svg className="ff-field-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>

            <input
              type={showPassword ? "text" : "password"}
              id="password"
              className="ff-input"
              autoComplete="current-password"
              placeholder="Enter your password"
              minLength="6"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />

            <button
              type="button"
              className="ff-eye"
              aria-label={showPassword ? "Hide password" : "Show password"}
              onClick={() => setShowPassword(!showPassword)}
            >
              👁
            </button>
          </div>

          <p className="ff-error" role="alert" aria-live="polite">
            {error}
          </p>

          <button type="submit" className="ff-btn-login">
            Login
          </button>

          <a href="#" className="ff-forgot">
            Forgot password?
          </a>

          <p className="ff-signup-line">
            Don&apos;t have an account?{" "}
            <Link to="/signup" className="ff-signup-link">
              Sign Up
            </Link>
          </p>
        </form>
      </div>
    </main>
  );
}

export default Login;