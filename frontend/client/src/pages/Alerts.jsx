import { useEffect, useMemo, useState } from "react";
import Layout from "../components/Layout";
import "../styles.css";

const SEED_POSTS = [
  {
    id: 1,
    severity: "critical",
    location: "Northern Rivers, NSW",
    author: "Community Watch",
    platform: "facebook",
    status: "needs review",
    engagement: 2410,
    text: "Unverified evacuation route map is spreading rapidly.",
    sourceUrl: "https://www.facebook.com/nswrfs",
    image:
      "https://images.unsplash.com/photo-1486915309851-b0cc1f8a0084?auto=format&fit=crop&w=1000&q=80",
  },
  {
    id: 2,
    severity: "high",
    location: "Grampians, VIC",
    author: "Local Update Board",
    platform: "twitter",
    status: "needs review",
    engagement: 1488,
    text: "Outdated hazard perimeter screenshot being reposted.",
    sourceUrl: "https://x.com/CFA_Updates",
    image:
      "https://images.unsplash.com/photo-1574870111867-089730e5a72b?auto=format&fit=crop&w=1000&q=80",
  },
  {
    id: 3,
    severity: "medium",
    location: "Perth Hills, WA",
    author: "Scanner Feed",
    platform: "facebook",
    status: "resolved",
    engagement: 623,
    text: "Speculative fire direction claim without official source.",
    sourceUrl: "https://www.facebook.com/dfeswa",
    image:
      "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=1000&q=80",
  },
  {
    id: 4,
    severity: "high",
    location: "SEQ, QLD",
    author: "Public Group",
    platform: "twitter",
    status: "needs review",
    engagement: 1182,
    text: "Road closure rumor posted as confirmed information.",
    sourceUrl: "https://x.com/QFESmedia",
    image:
      "https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?auto=format&fit=crop&w=1000&q=80",
  },
  {
    id: 5,
    severity: "critical",
    location: "Adelaide Hills, SA",
    author: "Flash News",
    platform: "instagram",
    status: "needs review",
    engagement: 3012,
    text: "Fake emergency hotline number shared in comments.",
    sourceUrl: "https://www.instagram.com/cfsalerts/",
    image:
      "https://images.unsplash.com/photo-1601581875309-fafbf2d3ed3a?auto=format&fit=crop&w=1000&q=80",
  },
  {
    id: 6,
    severity: "medium",
    location: "Hobart Fringe, TAS",
    author: "Regional Eye",
    platform: "instagram",
    status: "needs review",
    engagement: 490,
    text: "Incorrect shelter timing copied from an old incident.",
    sourceUrl: "https://www.instagram.com/afacnews/",
    image:
      "https://images.unsplash.com/photo-1493244040629-496f6d136cc3?auto=format&fit=crop&w=1000&q=80",
  },
];

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?auto=format&fit=crop&w=1000&q=80";

const SUBSCRIBERS_STORAGE_KEY = "firefusion.alerts.smsSubscribers";
const EMAIL_SUBSCRIBERS_STORAGE_KEY = "firefusion.alerts.emailSubscribers";
const TEXTBELT_KEY_STORAGE = "firefusion.alerts.textbeltKey";
const TEXTBELT_DEFAULT_KEY = "textbelt"; // public free key: 1 SMS / day / IP
// Goes through Vite's dev proxy (configured in vite.config.js) → textbelt.com/text.
// In production, point this at your own /api/sms route or your backend equivalent.
const TEXTBELT_ENDPOINT = "/api/sms";

// FormSubmit: free, CORS-enabled, no API key required.
// Each new recipient confirms their address once via a FormSubmit email,
// after which all submissions are forwarded to that inbox.
const FORMSUBMIT_ENDPOINT = "https://formsubmit.co/ajax";

function sanitizeApiKey(value) {
  if (!value) return TEXTBELT_DEFAULT_KEY;
  const cleaned = value.replace(/\s+/g, "");
  return cleaned || TEXTBELT_DEFAULT_KEY;
}

function isValidEmail(value) {
  if (!value) return false;
  const trimmed = value.trim();
  if (trimmed.length > 254) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed);
}

function maskEmail(value) {
  if (!value || !value.includes("@")) return value;
  const [name, domain] = value.split("@");
  if (name.length <= 2) return `${name[0]}•@${domain}`;
  return `${name.slice(0, 2)}${"•".repeat(Math.max(name.length - 2, 1))}@${domain}`;
}

async function sendEmailViaFormSubmit({ to, subject, message }) {
  let response;
  try {
    response = await fetch(`${FORMSUBMIT_ENDPOINT}/${encodeURIComponent(to)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        name: "FireFusion Alerts",
        _subject: subject,
        _template: "table",
        _captcha: "false",
        message,
      }),
    });
  } catch (networkError) {
    throw new Error(
      "Network error reaching email gateway. Check your internet connection."
    );
  }

  if (!response.ok) {
    throw new Error(`Email gateway returned HTTP ${response.status}`);
  }

  const data = await response.json();
  // FormSubmit responds with { success: "true" | "false", message: "..." }
  return {
    success: data.success === true || data.success === "true",
    message: data.message || "",
  };
}

function loadStoredList(storageKey) {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function loadStoredSubscribers() {
  return loadStoredList(SUBSCRIBERS_STORAGE_KEY);
}

function loadStoredEmailSubscribers() {
  return loadStoredList(EMAIL_SUBSCRIBERS_STORAGE_KEY);
}

function loadStoredApiKey() {
  if (typeof window === "undefined") return TEXTBELT_DEFAULT_KEY;
  try {
    return sanitizeApiKey(
      window.localStorage.getItem(TEXTBELT_KEY_STORAGE) || TEXTBELT_DEFAULT_KEY
    );
  } catch {
    return TEXTBELT_DEFAULT_KEY;
  }
}

async function sendSmsViaTextBelt({ phone, message, apiKey }) {
  let response;
  try {
    response = await fetch(TEXTBELT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        phone,
        message,
        key: sanitizeApiKey(apiKey),
      }).toString(),
    });
  } catch (networkError) {
    throw new Error(
      "Network error reaching SMS gateway. If you just edited vite.config.js, restart `npm run dev`."
    );
  }

  if (!response.ok) {
    throw new Error(`SMS gateway returned HTTP ${response.status}`);
  }

  return response.json();
}

function normalizePhoneNumber(value) {
  const trimmed = value.trim().replace(/[\s\-().]/g, "");
  if (!trimmed) return null;
  if (!/^\+?[0-9]{8,15}$/.test(trimmed)) return null;
  return trimmed.startsWith("+") ? trimmed : `+${trimmed}`;
}

function maskPhoneNumber(value) {
  if (!value || value.length < 4) return value;
  return `${value.slice(0, value.length - 4).replace(/[0-9]/g, "•")}${value.slice(-4)}`;
}

function Alerts() {
  const [posts, setPosts] = useState(
    SEED_POSTS.map((post) => ({ ...post, bookmarked: false }))
  );
  const [query, setQuery] = useState("");
  const [platform, setPlatform] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [view, setView] = useState("needs review");
  const [sortBy, setSortBy] = useState("severity");
  const [selected, setSelected] = useState(null);
  const [note, setNote] = useState("");
  const [toast, setToast] = useState("Live monitoring active");
  const [activity, setActivity] = useState(["Session started"]);
  const [now, setNow] = useState(new Date());
  const [phoneInput, setPhoneInput] = useState("");
  const [phoneError, setPhoneError] = useState("");
  const [subscribers, setSubscribers] = useState(() => loadStoredSubscribers());
  const [apiKey, setApiKey] = useState(() => loadStoredApiKey());
  const [showApiKey, setShowApiKey] = useState(false);
  const [smsStatus, setSmsStatus] = useState(null);
  const [sending, setSending] = useState(false);

  const [emailInput, setEmailInput] = useState("");
  const [emailError, setEmailError] = useState("");
  const [emailSubscribers, setEmailSubscribers] = useState(() =>
    loadStoredEmailSubscribers()
  );
  const [emailStatus, setEmailStatus] = useState(null);
  const [sendingEmail, setSendingEmail] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!toast) return;

    const timer = setTimeout(() => setToast(""), 2400);
    return () => clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(
        SUBSCRIBERS_STORAGE_KEY,
        JSON.stringify(subscribers)
      );
    } catch {
      // ignore (private mode / storage full)
    }
  }, [subscribers]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(TEXTBELT_KEY_STORAGE, apiKey);
    } catch {
      // ignore
    }
  }, [apiKey]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(
        EMAIL_SUBSCRIBERS_STORAGE_KEY,
        JSON.stringify(emailSubscribers)
      );
    } catch {
      // ignore (private mode / storage full)
    }
  }, [emailSubscribers]);

  const filteredPosts = useMemo(() => {
    const severityWeight = { critical: 3, high: 2, medium: 1 };

    return posts
      .filter((post) => (view === "all" ? true : post.status === "needs review"))
      .filter((post) => (platform === "all" ? true : post.platform === platform))
      .filter((post) => (severity === "all" ? true : post.severity === severity))
      .filter((post) =>
        `${post.location} ${post.author} ${post.text}`
          .toLowerCase()
          .includes(query.toLowerCase())
      )
      .sort((a, b) => {
        if (sortBy === "engagement") return b.engagement - a.engagement;
        if (sortBy === "latest") return b.id - a.id;
        return severityWeight[b.severity] - severityWeight[a.severity];
      });
  }, [posts, view, platform, severity, query, sortBy]);

  const kpi = useMemo(
    () => ({
      review: posts.filter((post) => post.status === "needs review").length,
      critical: posts.filter((post) => post.severity === "critical").length,
      high: posts.filter((post) => post.severity === "high").length,
      resolved: posts.filter((post) => post.status === "resolved").length,
    }),
    [posts]
  );

  function addActivity(text) {
    setActivity((previous) => [text, ...previous].slice(0, 8));
  }

  // Sends real SMS via TextBelt's public CORS-enabled endpoint.
  // The default key "textbelt" gives 1 free SMS per IP per day.
  // Paste a paid TextBelt key in the SMS card to send more.
  // For production / Twilio, route this through your own backend instead.
  async function notifySubscribers(message) {
    if (subscribers.length === 0) return { sent: 0, failed: 0 };

    setSending(true);
    addActivity(
      `Dispatching SMS to ${subscribers.length} number${
        subscribers.length === 1 ? "" : "s"
      }…`
    );

    let sent = 0;
    let failed = 0;
    let lastQuota = null;
    let lastError = null;

    for (const phone of subscribers) {
      try {
        const result = await sendSmsViaTextBelt({
          phone,
          message,
          apiKey,
        });
        if (typeof result.quotaRemaining === "number") {
          lastQuota = result.quotaRemaining;
        }
        if (result.success) {
          sent += 1;
          addActivity(
            `SMS sent to ${maskPhoneNumber(phone)} (id ${result.textId || "n/a"})`
          );
        } else {
          failed += 1;
          lastError = result.error || "unknown error";
          addActivity(
            `SMS failed for ${maskPhoneNumber(phone)}: ${lastError}`
          );
        }
      } catch (error) {
        failed += 1;
        lastError = error.message || String(error);
        addActivity(
          `SMS error for ${maskPhoneNumber(phone)}: ${lastError}`
        );
      }
    }

    setSending(false);

    if (sent > 0 && failed === 0) {
      setSmsStatus({
        type: "success",
        message: `Sent ${sent} SMS${sent === 1 ? "" : "s"}.${
          lastQuota !== null ? ` Quota left: ${lastQuota}.` : ""
        }`,
      });
      setToast(`SMS sent (${sent})`);
    } else if (sent > 0 && failed > 0) {
      setSmsStatus({
        type: "warn",
        message: `Sent ${sent}, failed ${failed}. Last error: ${lastError}.`,
      });
      setToast(`SMS partial: ${sent} sent, ${failed} failed`);
    } else {
      setSmsStatus({
        type: "error",
        message: `All ${failed} SMS failed. ${
          lastError ? `Reason: ${lastError}.` : ""
        }${
          lastQuota === 0
            ? " (Free daily quota used — paste a paid TextBelt key to send more.)"
            : ""
        }`,
      });
      setToast("SMS failed — see status below");
    }

    return { sent, failed };
  }

  async function sendTestSms() {
    if (subscribers.length === 0) {
      setSmsStatus({
        type: "error",
        message: "Add at least one phone number first.",
      });
      return;
    }
    await notifySubscribers(
      "FireFusion test alert — your phone is now subscribed to bushfire-misinformation alerts."
    );
  }

  async function notifyEmailSubscribers(subject, message) {
    if (emailSubscribers.length === 0) return { sent: 0, failed: 0 };

    setSendingEmail(true);
    addActivity(
      `Dispatching email to ${emailSubscribers.length} address${
        emailSubscribers.length === 1 ? "" : "es"
      }…`
    );

    let sent = 0;
    let failed = 0;
    let lastError = null;

    for (const email of emailSubscribers) {
      try {
        const result = await sendEmailViaFormSubmit({
          to: email,
          subject,
          message,
        });
        if (result.success) {
          sent += 1;
          addActivity(`Email sent to ${maskEmail(email)}`);
        } else {
          failed += 1;
          lastError = result.message || "unknown error";
          addActivity(`Email failed for ${maskEmail(email)}: ${lastError}`);
        }
      } catch (error) {
        failed += 1;
        lastError = error.message || String(error);
        addActivity(`Email error for ${maskEmail(email)}: ${lastError}`);
      }
    }

    setSendingEmail(false);

    if (sent > 0 && failed === 0) {
      setEmailStatus({
        type: "success",
        message: `Sent ${sent} email${sent === 1 ? "" : "s"}. New addresses must click "Activate" in the FormSubmit confirmation email before alerts arrive.`,
      });
      setToast(`Email queued (${sent})`);
    } else if (sent > 0 && failed > 0) {
      setEmailStatus({
        type: "warn",
        message: `Sent ${sent}, failed ${failed}. Last error: ${lastError}.`,
      });
      setToast(`Email partial: ${sent} sent, ${failed} failed`);
    } else {
      setEmailStatus({
        type: "error",
        message: `All ${failed} email${failed === 1 ? "" : "s"} failed. ${
          lastError ? `Reason: ${lastError}.` : ""
        }`,
      });
      setToast("Email failed — see status below");
    }

    return { sent, failed };
  }

  function subscribeEmail(event) {
    event.preventDefault();
    const trimmed = emailInput.trim().toLowerCase();
    if (!isValidEmail(trimmed)) {
      setEmailError("Enter a valid email address.");
      return;
    }
    if (emailSubscribers.includes(trimmed)) {
      setEmailError("This address is already subscribed.");
      return;
    }
    setEmailSubscribers((previous) => [...previous, trimmed]);
    setEmailInput("");
    setEmailError("");
    setToast(`${maskEmail(trimmed)} subscribed for email alerts`);
    addActivity(`Email subscriber added: ${maskEmail(trimmed)}`);
  }

  function removeEmailSubscriber(email) {
    setEmailSubscribers((previous) => previous.filter((e) => e !== email));
    setToast(`Removed ${maskEmail(email)} from email alerts`);
    addActivity(`Email subscriber removed: ${maskEmail(email)}`);
  }

  async function sendTestEmail() {
    if (emailSubscribers.length === 0) {
      setEmailStatus({
        type: "error",
        message: "Add at least one email address first.",
      });
      return;
    }
    await notifyEmailSubscribers(
      "FireFusion test alert",
      "This is a test message confirming your email is now subscribed to FireFusion bushfire-misinformation alerts.\n\nIf this is the first time this address has received a FormSubmit message, please click the Activate link in the separate confirmation email so future alerts can reach you."
    );
  }

  function resolvePost(postId) {
    const post = posts.find((p) => p.id === postId);
    setPosts((previous) =>
      previous.map((p) =>
        p.id === postId ? { ...p, status: "resolved" } : p
      )
    );

    setSelected(null);
    setNote("");
    setToast("Incident marked resolved");
    addActivity(`Resolved incident #${postId}`);
    if (post) {
      const summary = `FireFusion: Resolved incident at ${post.location} (${post.severity.toUpperCase()}).`;
      void notifySubscribers(summary);
      void notifyEmailSubscribers(
        `FireFusion: incident resolved (${post.severity.toUpperCase()})`,
        `${summary}\n\nIncident #${post.id}\nLocation: ${post.location}\nPlatform: ${formatPlatform(post.platform)}\nSummary: ${post.text}`
      );
    }
  }

  function toggleBookmark(postId) {
    setPosts((previous) =>
      previous.map((post) =>
        post.id === postId ? { ...post, bookmarked: !post.bookmarked } : post
      )
    );

    addActivity(`Updated bookmark for incident #${postId}`);
    setToast("Bookmark updated");
  }

  function refreshFeed() {
    setNow(new Date());
    setToast("Feed refreshed");
    addActivity("Feed refreshed");
    const criticalCount = posts.filter(
      (p) => p.severity === "critical" && p.status === "needs review"
    ).length;
    if (criticalCount > 0) {
      const summary = `FireFusion: ${criticalCount} critical bushfire-misinformation alert${
        criticalCount === 1 ? "" : "s"
      } need review.`;
      void notifySubscribers(summary);
      void notifyEmailSubscribers(
        `FireFusion: ${criticalCount} critical alert${
          criticalCount === 1 ? "" : "s"
        } need review`,
        summary
      );
    }
  }

  function subscribePhone(event) {
    event.preventDefault();
    const normalized = normalizePhoneNumber(phoneInput);
    if (!normalized) {
      setPhoneError(
        "Enter a valid number (8-15 digits, country code optional)."
      );
      return;
    }
    if (subscribers.includes(normalized)) {
      setPhoneError("This number is already subscribed.");
      return;
    }
    setSubscribers((previous) => [...previous, normalized]);
    setPhoneInput("");
    setPhoneError("");
    setToast(`Demo: ${maskPhoneNumber(normalized)} subscribed for SMS alerts`);
    addActivity(`SMS subscriber added: ${maskPhoneNumber(normalized)}`);
  }

  function removeSubscriber(number) {
    setSubscribers((previous) => previous.filter((n) => n !== number));
    setToast(`Removed ${maskPhoneNumber(number)} from SMS alerts`);
    addActivity(`SMS subscriber removed: ${maskPhoneNumber(number)}`);
  }

  function handleImageError(event) {
    if (event.currentTarget.src === FALLBACK_IMAGE) return;
    event.currentTarget.src = FALLBACK_IMAGE;
  }

  function formatPlatform(value) {
    if (value === "twitter") return "X / Twitter";
    return value.charAt(0).toUpperCase() + value.slice(1);
  }

  return (
    <>
      <Layout title="Alerts">
        <header className="fusion-top">
          <div>
            <h1 className="fusion-h1">
              Misinformation monitor{" "}
              <span className="fusion-live">
                <span className="fusion-live-dot"></span> LIVE
              </span>
            </h1>
            <p className="fusion-subtitle">
              Screen 1 / Landing Monitor for tracking bushfire misinformation alerts.
            </p>
          </div>

          <div className="fusion-search-bar">
            <input
              className="fusion-search-input"
              placeholder="Search incidents."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>

          <div className="fusion-top-right">
            <span className="fusion-updated">
              Updated {now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
            <button className="fusion-btn-review" type="button" onClick={refreshFeed}>
              Refresh
            </button>
          </div>
        </header>

        <section className="fusion-kpis">
            <article className="fusion-kpi">
              <span className="fusion-kpi-label">Needs review</span>
              <strong className="fusion-kpi-num">{kpi.review}</strong>
            </article>

            <article className="fusion-kpi">
              <span className="fusion-kpi-label">Critical</span>
              <strong className="fusion-kpi-num fusion-kpi-critical">{kpi.critical}</strong>
            </article>

            <article className="fusion-kpi">
              <span className="fusion-kpi-label">High</span>
              <strong className="fusion-kpi-num fusion-kpi-high">{kpi.high}</strong>
            </article>

            <article className="fusion-kpi">
              <span className="fusion-kpi-label">Resolved</span>
              <strong className="fusion-kpi-num fusion-kpi-ok">{kpi.resolved}</strong>
            </article>
          </section>

          <section className="fusion-ops-grid">
            <div className="fusion-block fusion-ops-card--wide">
              <div className="fusion-platform-row" role="group" aria-label="Filter by platform">
                <button
                  type="button"
                  className={`fusion-platform-chip fusion-platform-chip--all ${platform === "all" ? "fusion-platform-chip-on" : ""}`}
                  onClick={() => setPlatform("all")}
                >
                  All platforms
                </button>
                <button
                  type="button"
                  className={`fusion-platform-chip fusion-platform-chip--facebook ${platform === "facebook" ? "fusion-platform-chip-on" : ""}`}
                  onClick={() => setPlatform("facebook")}
                >
                  Facebook
                </button>
                <button
                  type="button"
                  className={`fusion-platform-chip fusion-platform-chip--twitter ${platform === "twitter" ? "fusion-platform-chip-on" : ""}`}
                  onClick={() => setPlatform("twitter")}
                >
                  X / Twitter
                </button>
                <button
                  type="button"
                  className={`fusion-platform-chip fusion-platform-chip--instagram ${platform === "instagram" ? "fusion-platform-chip-on" : ""}`}
                  onClick={() => setPlatform("instagram")}
                >
                  Instagram
                </button>
              </div>

              <div className="fusion-feed-toolbar">
                <button
                  className={`fusion-pill ${view === "needs review" ? "fusion-pill-on" : ""}`}
                  type="button"
                  onClick={() => setView("needs review")}
                >
                  Needs review
                </button>

                <button
                  className={`fusion-pill ${view === "all" ? "fusion-pill-on" : ""}`}
                  type="button"
                  onClick={() => setView("all")}
                >
                  All
                </button>

                <select
                  className="fusion-platform-select"
                  value={severity}
                  onChange={(event) => setSeverity(event.target.value)}
                  aria-label="Filter by severity"
                >
                  <option value="all">All severity</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                </select>

                <select
                  className="fusion-platform-select"
                  value={sortBy}
                  onChange={(event) => setSortBy(event.target.value)}
                  aria-label="Sort by"
                >
                  <option value="severity">Most severe first</option>
                  <option value="engagement">Highest engagement</option>
                  <option value="latest">Latest first</option>
                </select>
              </div>

              <div className="fusion-cards">
                {filteredPosts.length === 0 ? (
                  <div className="feed-empty-card">
                    <div className="feed-empty-icon">FF</div>
                    <h3>No matching incidents</h3>
                    <p className="muted">Try changing the search or filter settings.</p>
                  </div>
                ) : (
                  filteredPosts.map((post) => (
                    <article className="fusion-card-item" key={post.id}>
                      <img
                        className="fusion-card-image"
                        src={post.image}
                        alt={`${post.location} incident reference`}
                        loading="lazy"
                        onError={handleImageError}
                      />

                      <div className="fusion-card-top">
                        <span className={`fusion-pill-sev fusion-pill-sev-${post.severity}`}>
                          {post.severity}
                        </span>
                        <span className="fusion-card-loc">{post.location}</span>
                        <span className="fusion-card-time">
                          #{post.id.toString().padStart(3, "0")}
                        </span>
                      </div>

                      <div className="fusion-card-handle-row">
                        <span className="fusion-card-handle-author">
                          {post.author}
                        </span>
                        <a
                          className={`fusion-card-platform fusion-card-platform--${post.platform}`}
                          href={post.sourceUrl}
                          target="_blank"
                          rel="noreferrer noopener"
                          title={`Open this alert on ${formatPlatform(post.platform)}`}
                        >
                          {formatPlatform(post.platform)}
                        </a>
                      </div>

                      <blockquote className="fusion-card-quote">“{post.text}”</blockquote>

                      <div className="fusion-card-foot">
                        <span className="fusion-card-meta">
                          {post.engagement.toLocaleString()} engagements ·{" "}
                          <span
                            className={
                              post.engagement > 1400 ? "fusion-spread" : "fusion-growing"
                            }
                          >
                            {post.engagement > 1400 ? "fast spread" : "growing"}
                          </span>
                        </span>

                        <div className="fusion-card-actions">
                          <button
                            className="fusion-btn-review"
                            type="button"
                            onClick={() => {
                              setSelected(post);
                              setNote("");
                            }}
                          >
                            Review
                          </button>

                          <button
                            className="fusion-modal-btn-secondary"
                            type="button"
                            onClick={() => toggleBookmark(post.id)}
                          >
                            {post.bookmarked ? "Saved" : "Save"}
                          </button>
                        </div>
                      </div>
                    </article>
                  ))
                )}
              </div>
            </div>

            <aside className="fusion-ops-column">
              <div className="fusion-ops-card fusion-sms-card">
                <h2 className="fusion-ops-card__title">
                  Get alerts on your phone
                </h2>
                <p className="fusion-sms-lead">
                  Add your mobile number to receive a real text whenever a
                  critical bushfire-misinformation alert is issued.
                </p>

                <form className="fusion-sms-form" onSubmit={subscribePhone}>
                  <label className="fusion-sms-label" htmlFor="alerts-sms">
                    Mobile number
                  </label>
                  <div className="fusion-sms-input-row">
                    <input
                      id="alerts-sms"
                      type="tel"
                      inputMode="tel"
                      autoComplete="tel"
                      className="fusion-sms-input"
                      placeholder="+61 4XX XXX XXX"
                      value={phoneInput}
                      onChange={(event) => {
                        setPhoneInput(event.target.value);
                        if (phoneError) setPhoneError("");
                      }}
                    />
                    <button
                      type="submit"
                      className="fusion-btn-review fusion-sms-submit"
                    >
                      Subscribe
                    </button>
                  </div>
                  {phoneError ? (
                    <p className="fusion-sms-error" role="alert">
                      {phoneError}
                    </p>
                  ) : (
                    <p className="fusion-sms-hint">
                      Include the country code (e.g. <code>+61</code> for AU,
                      <code> +1</code> for US).
                    </p>
                  )}
                </form>

                <div className="fusion-sms-list-wrap">
                  <p className="fusion-sms-list-title">
                    Subscribed numbers ({subscribers.length})
                  </p>
                  {subscribers.length === 0 ? (
                    <p className="fusion-sms-empty">
                      No numbers yet. Add yours above to start receiving alerts.
                    </p>
                  ) : (
                    <ul className="fusion-sms-list">
                      {subscribers.map((number) => (
                        <li key={number} className="fusion-sms-row">
                          <span className="fusion-sms-number">
                            {maskPhoneNumber(number)}
                          </span>
                          <button
                            type="button"
                            className="fusion-sms-remove"
                            onClick={() => removeSubscriber(number)}
                            aria-label={`Unsubscribe ${maskPhoneNumber(number)}`}
                          >
                            Remove
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="fusion-sms-actions">
                  <button
                    type="button"
                    className="fusion-btn-review"
                    onClick={sendTestSms}
                    disabled={sending || subscribers.length === 0}
                  >
                    {sending ? "Sending…" : "Send test SMS now"}
                  </button>
                  <button
                    type="button"
                    className="fusion-modal-btn-secondary"
                    onClick={() => setShowApiKey((value) => !value)}
                  >
                    {showApiKey ? "Hide API key" : "API key"}
                  </button>
                </div>

                {showApiKey && (
                  <div className="fusion-sms-key-wrap">
                    <label
                      className="fusion-sms-label"
                      htmlFor="alerts-textbelt-key"
                    >
                      TextBelt API key
                    </label>
                    <input
                      id="alerts-textbelt-key"
                      type="text"
                      className="fusion-sms-input"
                      placeholder="textbelt"
                      value={apiKey}
                      onChange={(event) =>
                        setApiKey(sanitizeApiKey(event.target.value))
                      }
                      autoCapitalize="off"
                      autoCorrect="off"
                      spellCheck="false"
                    />
                    <p className="fusion-sms-hint">
                      Default key <code>textbelt</code> = 1 free SMS per IP per
                      day. Buy a paid key at{" "}
                      <a
                        href="https://textbelt.com/"
                        target="_blank"
                        rel="noreferrer noopener"
                      >
                        textbelt.com
                      </a>{" "}
                      for unlimited sends.
                    </p>
                  </div>
                )}

                {smsStatus && (
                  <div
                    className={`fusion-sms-status fusion-sms-status--${smsStatus.type}`}
                    role="status"
                  >
                    {smsStatus.message}
                  </div>
                )}

                <p className="fusion-sms-note">
                  SMS is delivered through{" "}
                  <a
                    href="https://textbelt.com/"
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    TextBelt
                  </a>
                  . The free public key allows 1 message per day per IP. For
                  production volume, route this through your own backend +
                  Twilio/MessageBird with a server-side API key.
                </p>
              </div>

              <div className="fusion-ops-card fusion-email-card">
                <h2 className="fusion-ops-card__title">
                  Get alerts by email
                </h2>
                <p className="fusion-sms-lead">
                  Add your email and we'll send a real message every time a
                  critical alert is issued. No setup or API key required.
                </p>

                <form className="fusion-sms-form" onSubmit={subscribeEmail}>
                  <label className="fusion-sms-label" htmlFor="alerts-email">
                    Email address
                  </label>
                  <div className="fusion-sms-input-row">
                    <input
                      id="alerts-email"
                      type="email"
                      inputMode="email"
                      autoComplete="email"
                      autoCapitalize="off"
                      autoCorrect="off"
                      spellCheck="false"
                      className="fusion-sms-input"
                      placeholder="you@example.com"
                      value={emailInput}
                      onChange={(event) => {
                        setEmailInput(event.target.value);
                        if (emailError) setEmailError("");
                      }}
                    />
                    <button
                      type="submit"
                      className="fusion-btn-review fusion-sms-submit"
                    >
                      Subscribe
                    </button>
                  </div>
                  {emailError ? (
                    <p className="fusion-sms-error" role="alert">
                      {emailError}
                    </p>
                  ) : (
                    <p className="fusion-sms-hint">
                      First-time addresses receive a one-click confirmation
                      email. Click <strong>Activate</strong> in it once and all
                      future alerts arrive automatically.
                    </p>
                  )}
                </form>

                <div className="fusion-sms-list-wrap">
                  <p className="fusion-sms-list-title">
                    Subscribed addresses ({emailSubscribers.length})
                  </p>
                  {emailSubscribers.length === 0 ? (
                    <p className="fusion-sms-empty">
                      No addresses yet. Add yours above to start receiving
                      alerts.
                    </p>
                  ) : (
                    <ul className="fusion-sms-list">
                      {emailSubscribers.map((email) => (
                        <li key={email} className="fusion-sms-row">
                          <span className="fusion-sms-number">
                            {maskEmail(email)}
                          </span>
                          <button
                            type="button"
                            className="fusion-sms-remove"
                            onClick={() => removeEmailSubscriber(email)}
                            aria-label={`Unsubscribe ${maskEmail(email)}`}
                          >
                            Remove
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="fusion-sms-actions">
                  <button
                    type="button"
                    className="fusion-btn-review"
                    onClick={sendTestEmail}
                    disabled={sendingEmail || emailSubscribers.length === 0}
                  >
                    {sendingEmail ? "Sending…" : "Send test email now"}
                  </button>
                </div>

                {emailStatus && (
                  <div
                    className={`fusion-sms-status fusion-sms-status--${emailStatus.type}`}
                    role="status"
                  >
                    {emailStatus.message}
                  </div>
                )}

                <p className="fusion-sms-note fusion-email-note">
                  Email delivery is handled by{" "}
                  <a
                    href="https://formsubmit.co/"
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    FormSubmit
                  </a>{" "}
                  — free, no signup or API keys, sender confirmation built in
                  to prevent abuse. Subscribed addresses are saved locally in
                  your browser.
                </p>
              </div>

              <div className="fusion-ops-card">
                <h2 className="fusion-ops-card__title">Operations activity</h2>
                <ul className="runbook">
                  {activity.map((item, index) => (
                    <li key={`${item}-${index}`}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="fusion-ops-card">
                <h2 className="fusion-ops-card__title">Analyst runbook</h2>
                <ol className="runbook">
                  <li>Check the post against official emergency sources.</li>
                  <li>Confirm whether the claim is current, outdated, or false.</li>
                  <li>Send high-risk posts to the Review & Debunk screen.</li>
                  <li>Mark resolved once the review is complete.</li>
                </ol>
              </div>
            </aside>
        </section>
      </Layout>

      <div
        className={`modal fusion-modal ${selected ? "modal-open" : ""}`}
        aria-hidden={selected ? "false" : "true"}
      >
        <div
          className="modal-overlay fusion-modal-bg"
          onClick={() => setSelected(null)}
        ></div>

        <div className="modal-panel fusion-modal-box">
          <div className="fusion-modal-top">
            <h2 className="fusion-modal-h2">Review Incident</h2>
            <button
              type="button"
              className="fusion-modal-x"
              onClick={() => setSelected(null)}
            >
              ×
            </button>
          </div>

          <div className="fusion-modal-body">
            {selected ? (
              <>
                <p className="fusion-modal-lead">
                  {selected.location} · {selected.severity.toUpperCase()}
                </p>

                <ul className="fusion-modal-list">
                  <li>{selected.text}</li>
                  <li>Author: {selected.author}</li>
                  <li>Platform: {formatPlatform(selected.platform)}</li>
                  <li>Engagement: {selected.engagement.toLocaleString()}</li>
                  <li>Status: {selected.status}</li>
                </ul>

                <textarea
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                  placeholder="Add review notes."
                  style={{
                    width: "100%",
                    marginTop: "10px",
                    minHeight: "90px",
                    borderRadius: "8px",
                    border: "1px solid #e5e7eb",
                    padding: "8px",
                    fontFamily: "Inter, sans-serif",
                  }}
                />
              </>
            ) : null}
          </div>

          <div className="fusion-modal-actions">
            <button
              type="button"
              className="fusion-modal-btn-secondary"
              onClick={() => setSelected(null)}
            >
              Close
            </button>

            <button
              type="button"
              className="fusion-modal-btn-primary"
              onClick={() => {
                if (!selected) return;
                addActivity(`Reviewed incident #${selected.id}${note ? " with notes" : ""}`);
                resolvePost(selected.id);
              }}
            >
              Mark reviewed
            </button>
          </div>
        </div>
      </div>

      <div className={`toast fusion-toast ${toast ? "toast-show" : ""}`}>
        {toast}
      </div>
    </>
  );
}

export default Alerts;