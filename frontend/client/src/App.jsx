import MisinformationReview from "./pages/MisinformationReview.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import FireRiskMap from "./pages/FireRiskMap.tsx";
import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";
import Settings from "./pages/Settings.jsx";
import MisinfoLandingPage from "./pages/MisinformationLanding.jsx";
import FeedbackPage from "./FeedbackPage.jsx";

export default function App() {
  const path = window.location.pathname;

  if (path === "/fire-map") {
    return <FireRiskMap />;
  }

  if (path === "/misinfo-review") {
    return <MisinformationReview />;
  }

  if (path === "/misinfo") {
    return <MisinfoLandingPage />;
  }

  if (path === "/login") {
    return <Login />;
  }

  if (path === "/signup") {
    return <Signup />;
  }
  if (path === "/feedback") {
  return <FeedbackPage />;
}
  if (path === "/settings") return <Settings />;
  return <FeedbackPage />;
}
