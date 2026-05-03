function initLoginPage() {
    const loginForm = document.getElementById("loginForm");
    if (!loginForm) return;
   
    const errorBox = document.getElementById("loginError");
    const togglePassword = document.getElementById("togglePassword");
    const passwordInput = document.getElementById("password");
   
    if (togglePassword && passwordInput) {
      togglePassword.addEventListener("click", () => {
        const isHidden = passwordInput.type === "password";
        passwordInput.type = isHidden ? "text" : "password";
        if (togglePassword.classList.contains("ff-eye")) {
          togglePassword.setAttribute(
            "aria-label",
            isHidden ? "Hide password" : "Show password"
          );
        } else {
          togglePassword.textContent = isHidden ? "Hide" : "Show";
        }
      });
    }
   
    loginForm.addEventListener("submit", (event) => {
      event.preventDefault();
   
      const formData = new FormData(loginForm);
      const email = String(formData.get("email") || "").trim();
      const password = String(formData.get("password") || "");
   
      if (errorBox) errorBox.textContent = "";
   
      if (!email || !password) {
        if (errorBox) errorBox.textContent = "Please enter your email and password.";
        return;
      }
   
      if (password.length < 6) {
        if (errorBox) errorBox.textContent = "Password must be at least 6 characters long.";
        return;
      }
   
      window.location.href = "./alerts.html";
    });
  }
   
  function wirePasswordToggle(toggleButton, inputElement) {
    if (!toggleButton || !inputElement) return;
    toggleButton.addEventListener("click", () => {
      const isHidden = inputElement.type === "password";
      inputElement.type = isHidden ? "text" : "password";
      if (toggleButton.classList.contains("ff-eye")) {
        toggleButton.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
      } else {
        toggleButton.textContent = isHidden ? "Hide" : "Show";
      }
    });
  }
   
  function getPasswordScore(value) {
    let score = 0;
    if (value.length >= 8) score += 1;
    if (/[A-Z]/.test(value)) score += 1;
    if (/[a-z]/.test(value)) score += 1;
    if (/\d/.test(value)) score += 1;
    if (/[^A-Za-z0-9]/.test(value)) score += 1;
    return score;
  }
   
  function initSignupPage() {
    const signupForm = document.getElementById("signupForm");
    if (!signupForm) return;
   
    const fullName = document.getElementById("fullName");
    const signupEmail = document.getElementById("signupEmail");
    const signupPassword = document.getElementById("signupPassword");
    const confirmPassword = document.getElementById("confirmPassword");
    const signupError = document.getElementById("signupError");
    const strengthBar = document.getElementById("passwordStrengthBar");
    const strengthText = document.getElementById("passwordStrengthText");
   
    wirePasswordToggle(document.getElementById("toggleSignupPassword"), signupPassword);
    wirePasswordToggle(document.getElementById("toggleConfirmPassword"), confirmPassword);
   
    function updateStrengthMeter() {
      const password = String(signupPassword?.value || "");
      const score = getPasswordScore(password);
      const width = Math.min(score * 20, 100);
      let label = "Strength: Very Weak";
      let color = "#ef4444";
   
      if (score >= 4) {
        label = "Strength: Strong";
        color = "#16a34a";
      } else if (score >= 3) {
        label = "Strength: Medium";
        color = "#f59e0b";
      } else if (score >= 2) {
        label = "Strength: Weak";
        color = "#f97316";
      }
   
      if (!password.length) {
        label = "Strength: —";
        color = "#9e9e9e";
      }
   
      if (strengthBar) {
        strengthBar.style.width = `${password.length ? width : 0}%`;
        strengthBar.style.background = color;
      }
      if (strengthText) {
        strengthText.textContent = label;
      }
    }
   
    signupPassword?.addEventListener("input", updateStrengthMeter);
    updateStrengthMeter();
   
    signupForm.addEventListener("submit", (event) => {
      event.preventDefault();
      if (signupError) signupError.textContent = "";
   
      const nameValue = String(fullName?.value || "").trim();
      const emailValue = String(signupEmail?.value || "").trim();
      const passwordValue = String(signupPassword?.value || "");
      const confirmValue = String(confirmPassword?.value || "");
   
      if (!nameValue || !emailValue || !passwordValue || !confirmValue) {
        if (signupError) signupError.textContent = "Please complete all fields.";
        return;
      }
   
      if (nameValue.length < 3) {
        if (signupError) signupError.textContent = "Please enter a valid full name.";
        return;
      }
   
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(emailValue)) {
        if (signupError) signupError.textContent = "Please enter a valid email address.";
        return;
      }
   
      if (passwordValue.length < 8) {
        if (signupError) signupError.textContent = "Password must be at least 8 characters long.";
        return;
      }
   
      if (getPasswordScore(passwordValue) < 3) {
        if (signupError) signupError.textContent = "Please create a stronger password.";
        return;
      }
   
      if (passwordValue !== confirmValue) {
        if (signupError) signupError.textContent = "Passwords do not match.";
        return;
      }
   
      window.location.href = "./login.html";
    });
  }
   
  /** Alerts page: UI only — no API calls or external data. */
  function initAlertsPage() {
    const reviewModal = document.getElementById("reviewModal");
    if (!reviewModal || !document.body.classList.contains("fusion-page")) return;
   
    function openReview() {
      reviewModal.setAttribute("aria-hidden", "false");
      reviewModal.classList.add("modal-open");
      document.body.style.overflow = "hidden";
    }
   
    function closeReview() {
      reviewModal.setAttribute("aria-hidden", "true");
      reviewModal.classList.remove("modal-open");
      document.body.style.overflow = "";
    }
   
    document.querySelectorAll(".fusion-btn-review").forEach((btn) => {
      btn.addEventListener("click", openReview);
    });
   
    reviewModal.querySelectorAll('[data-close-modal="true"]').forEach((el) => {
      el.addEventListener("click", closeReview);
    });
   
    document.getElementById("reviewDoneBtn")?.addEventListener("click", closeReview);
   
    document.querySelectorAll(".fusion-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        document.querySelectorAll(".fusion-pill").forEach((p) => {
          p.classList.remove("fusion-pill-on");
          p.setAttribute("aria-selected", "false");
        });
        pill.classList.add("fusion-pill-on");
        pill.setAttribute("aria-selected", "true");
      });
    });
   
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && reviewModal.classList.contains("modal-open")) {
        closeReview();
      }
    });
  }
   
  document.addEventListener("DOMContentLoaded", () => {
    initLoginPage();
    initSignupPage();
    initAlertsPage();
  });