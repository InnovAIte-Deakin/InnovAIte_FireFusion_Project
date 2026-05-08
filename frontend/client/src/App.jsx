import Dashboard from "./pages/Dashboard.jsx";
import FireRiskMap from "./pages/FireRiskMap.tsx";
import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";

export default function App() {
  const path = window.location.pathname;

  if (path === "/fire-map") {
    return <FireRiskMap />;
  }

  if (path === "/login") {
    return <Login />;
  }

  if (path === "/signup") {
    return <Signup />;
  }

  return <Dashboard />;
}