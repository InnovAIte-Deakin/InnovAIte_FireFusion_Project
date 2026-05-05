import MisinformationReview from "./pages/MisinformationReview.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import FireRiskMap from "./pages/FireRiskMap.tsx";

export default function App() {
  const path = window.location.pathname;

  if (path === "/fire-map") {
    return <FireRiskMap />;
  }

  if (path === '/misinfo-review') {
    return <MisinformationReview />;
  }

  return <Dashboard />;
}