import MisinformationReview from "./pages/MisinformationReview.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import FireRiskMap from "./pages/FireRiskMap.tsx";
import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";
import Alerts from "./pages/Alerts.jsx";

export default function App() {
  const path = window.location.pathname;

  if (path === "/fire-map") {
    return <FireRiskMap />;
  }

  if (path === "/misinfo-review") {
    return <MisinformationReview />;
  }

  if (path === "/alerts") {
    return <Alerts />;
  }

  if (path === "/login") {
    return <Login />;
  }

  if (path === "/signup") {
    return <Signup />;
  }

  return <Dashboard />;
}