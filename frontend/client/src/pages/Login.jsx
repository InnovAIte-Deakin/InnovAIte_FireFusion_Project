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

            <svg className="ff-hero-trees"