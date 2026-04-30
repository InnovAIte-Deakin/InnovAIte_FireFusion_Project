import Dashboard from "./pages/Dashboard.jsx";
import FireRiskMap from "./pages/FireRiskMap.tsx";

export default function App() {
  const path = window.location.pathname;

  if (path === "/fire-map") {
    return <FireRiskMap />;
  }

  return <Dashboard />;
}