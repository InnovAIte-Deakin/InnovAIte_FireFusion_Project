import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

const Dashboard = lazy(() => import("./pages/Dashboard.jsx"));
const Analytics = lazy(() => import("./pages/Analytics.jsx"));
const FireRiskMap = lazy(() => import("./pages/FireRiskMap.jsx"));
const Alerts = lazy(() => import("./pages/Alerts.jsx"));
const MisinformationReview = lazy(() => import("./pages/MisinformationReview.jsx"));
const BushfireForecastDetails = lazy(() => import("./pages/BushfireForecastDetails.jsx"));
const DataSourcesMethod = lazy(() => import("./pages/DataSourcesMethod.jsx"));
const EmergencyAdvice = lazy(() => import("./pages/EmergencyAdvice.jsx"));
const Feedback = lazy(() => import("./pages/Feedback.jsx"));
const Login = lazy(() => import("./pages/Login.jsx"));
const Signup = lazy(() => import("./pages/Signup.jsx"));
const Settings = lazy(() => import("./pages/Settings.jsx"));
const UserProfile = lazy(() => import("./pages/UserProfile.jsx"));

function LoadingScreen() {
  return (
    <div style={{ padding: "40px", fontFamily: "Arial, sans-serif" }}>
      Loading FireFusion...
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingScreen />}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/fire-map" element={<FireRiskMap />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/misinformation-review" element={<MisinformationReview />} />
          <Route path="/forecast-details" element={<BushfireForecastDetails />} />
          <Route path="/data-sources" element={<DataSourcesMethod />} />
          <Route path="/emergency-advice" element={<EmergencyAdvice />} />
          <Route path="/feedback" element={<Feedback />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/profile" element={<UserProfile />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}