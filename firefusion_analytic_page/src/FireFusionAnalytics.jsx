import React, { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  Polyline,
} from "react-leaflet";

const SidebarItem = ({ children, active = false, icon }) => {
  return (
    <div
      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] transition ${
        active
          ? "bg-orange-500 font-semibold text-white shadow-md shadow-orange-500/30"
          : "text-slate-400 hover:bg-white/5 hover:text-white"
      }`}
    >
      <span className="w-4 text-center text-[13px]">{icon}</span>
      <span>{children}</span>
    </div>
  );
};

const Sidebar = () => {
  return (
    <aside className="flex h-screen w-[240px] flex-shrink-0 flex-col bg-[#151824] text-white">
      <div className="flex items-center gap-3 border-b border-white/10 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-orange-500 text-xs font-bold shadow-lg shadow-orange-500/30">
          FF
        </div>

        <div>
          <div className="text-[15px] font-bold leading-tight text-white">
            FireFusion
          </div>
          <div className="text-[10px] text-slate-500">Emergency Ops</div>
        </div>
      </div>

      <div className="px-3 py-4">
        <div className="mb-3 px-2 text-[9px] font-bold uppercase tracking-[0.18em] text-slate-600">
          Main Menu
        </div>

        <div className="space-y-1">
          <SidebarItem icon="⌘">Dashboard</SidebarItem>
          <SidebarItem icon="♧">Fire Map</SidebarItem>
          <SidebarItem icon="△">Alerts</SidebarItem>
          <SidebarItem icon="⌕">Misinformation</SidebarItem>
          <SidebarItem icon="□">Reports</SidebarItem>
          <SidebarItem icon="⌁" active>
            Analytics
          </SidebarItem>
        </div>
      </div>

      <div className="flex-1" />

      <div className="border-t border-white/10 px-3 py-4">
        <div className="mb-3 px-2 text-[9px] font-bold uppercase tracking-[0.18em] text-slate-600">
          System
        </div>

        <div className="space-y-1">
          <SidebarItem icon="♧">Notifications</SidebarItem>
          <SidebarItem icon="☼">Settings</SidebarItem>
        </div>

        <div className="mt-6 flex items-center gap-3 px-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500 text-[11px] font-bold text-white">
            VA
          </div>

          <div>
            <div className="text-[12px] font-bold text-white">
              Vardhan Akula
            </div>
            <div className="text-[10px] text-slate-500">Emergency Mgr</div>
          </div>
        </div>
      </div>
    </aside>
  );
};

const Topbar = () => {
  return (
    <header className="flex h-[56px] items-center gap-2 border-b border-slate-200 bg-white px-5">
      <h1 className="mr-2 text-[17px] font-bold text-slate-900">Analytics</h1>

      <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-[12px] text-slate-500">
        ◉ Region: <strong className="text-slate-900">Australia</strong>
      </div>

      <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-[12px] font-semibold text-slate-900">
        ◷ 18 Mar 2026 14:00–20:00
      </div>

      <div className="rounded-md border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-[12px] font-bold text-emerald-600">
        ● Updated 2 min ago
      </div>

      <button className="ml-auto rounded-md border-2 border-red-500 px-4 py-1.5 text-[11px] font-bold uppercase tracking-wider text-red-500 shadow-sm">
        Extreme Risk
      </button>

      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500 text-[11px] font-bold text-white">
        VA
      </div>
    </header>
  );
};

const Sparkline = ({ color, points }) => {
  return (
    <svg viewBox="0 0 100 25" className="mt-4 h-7 w-full">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

const KpiCard = ({ title, value, color, points }) => {
  return (
    <div className="relative overflow-hidden rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div
        className="absolute left-0 right-0 top-0 h-[3px]"
        style={{ backgroundColor: color }}
      />

      <div className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">
        {title}
      </div>

      <div
        className="mt-1 text-[24px] font-bold leading-none"
        style={{ color }}
      >
        {value}
      </div>

      <Sparkline color={color} points={points} />
    </div>
  );
};

const KPISection = () => {
  const data = [
    {
      title: "Overall Risk",
      value: "Extreme",
      color: "#ef4444",
      points: "0,22 20,20 40,17 60,13 80,10 100,6",
    },
    {
      title: "Active Zones",
      value: "7",
      color: "#ff6124",
      points: "0,22 20,19 40,17 60,14 80,11 100,8",
    },
    {
      title: "Misinformation",
      value: "14",
      color: "#d97706",
      points: "0,20 20,18 40,19 60,14 80,17 100,11",
    },
    {
      title: "Communities",
      value: "23",
      color: "#2563eb",
      points: "0,21 20,21 40,19 60,17 80,15 100,12",
    },
    {
      title: "Alerts Issued",
      value: "31",
      color: "#059669",
      points: "0,22 20,21 40,19 60,16 80,12 100,8",
    },
  ];

  return (
    <section className="grid grid-cols-5 gap-3">
      {data.map((item) => (
        <KpiCard key={item.title} {...item} />
      ))}
    </section>
  );
};

const WeatherTimeline = () => {
  const [weather, setWeather] = useState([]);
  const [loading, setLoading] = useState(true);

  // East Gippsland / Mallacoota coordinates
  const latitude = -37.558;
  const longitude = 149.754;

  const getWeatherIcon = (code) => {
    if (code === 0) return "☀️";
    if ([1, 2, 3].includes(code)) return "🌤️";
    if ([45, 48].includes(code)) return "🌫️";
    if ([51, 53, 55, 56, 57].includes(code)) return "🌦️";
    if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return "🌧️";
    if ([95, 96, 99].includes(code)) return "⛈️";
    return "☀️";
  };

  const getWindDirection = (degrees) => {
    const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
    const index = Math.round(degrees / 45) % 8;
    return directions[index];
  };

  useEffect(() => {
    const fetchWeather = async () => {
      try {
        setLoading(true);

        const response = await fetch(
          `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&hourly=temperature_2m,weather_code,wind_speed_10m,wind_direction_10m&timezone=Australia%2FSydney&forecast_days=1`
        );

        if (!response.ok) {
          throw new Error("Weather request failed");
        }

        const data = await response.json();
        const currentHour = new Date().getHours();

        const formattedWeather = data.hourly.time
          .map((time, index) => {
            const hour = new Date(time).getHours();

            return {
              time: hour === currentHour ? "NOW" : time.slice(11, 16),
              icon: getWeatherIcon(data.hourly.weather_code[index]),
              temp: `${Math.round(data.hourly.temperature_2m[index])}°C`,
              wind: `${getWindDirection(
                data.hourly.wind_direction_10m[index]
              )} ${Math.round(data.hourly.wind_speed_10m[index])}`,
              now: hour === currentHour,
              amber: data.hourly.temperature_2m[index] < 38,
            };
          })
          .filter((item, index) => {
            const hour = new Date(data.hourly.time[index]).getHours();
            return hour >= currentHour && hour <= currentHour + 5;
          })
          .slice(0, 6);

        setWeather(formattedWeather);
      } catch (error) {
        console.error("Weather API error:", error);

        setWeather([
          { time: "14:00", icon: "☀️", temp: "39°C", wind: "NW 38" },
          { time: "15:00", icon: "☀️", temp: "41°C", wind: "NW 42" },
          { time: "NOW", icon: "☀️", temp: "41°C", wind: "NW 45", now: true },
          { time: "17:00", icon: "☀️", temp: "43°C", wind: "NW 50" },
          {
            time: "18:00",
            icon: "🌤️",
            temp: "40°C",
            wind: "W 38",
            amber: true,
          },
          {
            time: "20:00",
            icon: "🌙",
            temp: "35°C",
            wind: "W 25",
            amber: true,
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchWeather();

    const interval = setInterval(fetchWeather, 30 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <section className="grid grid-cols-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        {Array.from({ length: 6 }).map((_, index) => (
          <div
            key={index}
            className="border-r border-slate-200 px-4 py-3 last:border-r-0"
          >
            <div className="font-mono text-[10px] text-slate-400">
              Loading
            </div>

            <div className="mt-1 text-lg">⏳</div>

            <div className="text-[19px] font-bold leading-tight text-slate-400">
              --°C
            </div>

            <div className="mt-1 text-[10px] text-slate-400">-- --</div>
          </div>
        ))}
      </section>
    );
  }

  return (
    <section className="grid grid-cols-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      {weather.map((item) => (
        <div
          key={item.time}
          className={`border-r border-slate-200 px-4 py-3 last:border-r-0 ${
            item.now ? "border-t-2 border-t-orange-500 bg-orange-50" : ""
          }`}
        >
          <div
            className={`font-mono text-[10px] ${
              item.now ? "font-bold text-orange-500" : "text-slate-400"
            }`}
          >
            {item.time}
          </div>

          <div className="mt-1 text-lg">{item.icon}</div>

          <div
            className={`text-[19px] font-bold leading-tight ${
              item.amber ? "text-amber-600" : "text-red-500"
            }`}
          >
            {item.temp}
          </div>

          <div className="mt-1 text-[10px] text-slate-400">{item.wind}</div>
        </div>
      ))}
    </section>
  );
};

const IncidentMap = () => {
  const fireZones = [
    {
      name: "Mallacoota Active Fire",
      position: [-37.558, 149.754],
      radius: 12000,
      color: "#ef4444",
      fillColor: "#ef4444",
    },
    {
      name: "Orbost Fire Zone",
      position: [-37.706, 148.457],
      radius: 9000,
      color: "#f97316",
      fillColor: "#f97316",
    },
    {
      name: "Genoa Road Closure Area",
      position: [-37.475, 149.594],
      radius: 5000,
      color: "#dc2626",
      fillColor: "#dc2626",
    },
  ];

  const evacuationRoute = [
    [-37.706, 148.457],
    [-37.645, 148.87],
    [-37.56, 149.15],
    [-37.558, 149.754],
  ];

  const closedRoad = [
    [-37.475, 149.594],
    [-37.52, 149.66],
    [-37.558, 149.754],
  ];

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex h-10 items-center gap-2 border-b border-slate-200 px-4">
        <span className="text-slate-400">♡</span>

        <h2 className="flex-1 text-[14px] font-bold text-slate-900">
          Incident Map — East Gippsland, VIC
        </h2>

        <button className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] text-slate-500">
          Live map
        </button>

        <button className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] text-slate-500">
          OpenStreetMap
        </button>

        <button className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] text-slate-500">
          Expand ↗
        </button>
      </div>

      <div className="h-[260px] w-full">
        <MapContainer
          center={[-37.65, 149.1]}
          zoom={8}
          scrollWheelZoom={true}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {fireZones.map((zone) => (
            <Circle
              key={zone.name}
              center={zone.position}
              radius={zone.radius}
              pathOptions={{
                color: zone.color,
                fillColor: zone.fillColor,
                fillOpacity: 0.25,
                weight: 2,
              }}
            >
              <Popup>
                <strong>{zone.name}</strong>
                <br />
                Status: Active monitoring
              </Popup>
            </Circle>
          ))}

          <Marker position={[-37.558, 149.754]}>
            <Popup>
              <strong>Mallacoota</strong>
              <br />
              Extreme fire risk area.
            </Popup>
          </Marker>

          <Marker position={[-37.706, 148.457]}>
            <Popup>
              <strong>Orbost</strong>
              <br />
              Watch and Act zone.
            </Popup>
          </Marker>

          <Marker position={[-37.881, 147.982]}>
            <Popup>
              <strong>Lakes Entrance</strong>
              <br />
              Advice zone.
            </Popup>
          </Marker>

          <Marker position={[-37.496, 148.172]}>
            <Popup>
              <strong>Buchan Valley</strong>
              <br />
              Currently marked clear.
            </Popup>
          </Marker>

          <Polyline
            positions={evacuationRoute}
            pathOptions={{
              color: "#16a34a",
              weight: 4,
              dashArray: "8 6",
            }}
          />

          <Polyline
            positions={closedRoad}
            pathOptions={{
              color: "#dc2626",
              weight: 4,
              dashArray: "6 6",
            }}
          />
        </MapContainer>
      </div>

      <div className="flex border-t border-slate-200 bg-slate-50 text-[11px] text-slate-600">
        <div className="border-r border-slate-200 px-4 py-2">
          Area burnt: <strong className="text-red-500">14,320 ha</strong>
        </div>

        <div className="border-r border-slate-200 px-4 py-2">
          Perimeter: <strong className="text-orange-500">284 km</strong>
        </div>

        <div className="border-r border-slate-200 px-4 py-2">
          Contained: <strong className="text-emerald-600">12%</strong>
        </div>

        <div className="px-4 py-2">
          Open routes: <strong className="text-blue-600">2 of 5</strong>
        </div>
      </div>
    </section>
  );
};

const RiskTag = ({ children, type }) => {
  const styles = {
    extreme: "bg-red-50 text-red-600",
    high: "bg-orange-50 text-orange-600",
    mod: "bg-yellow-50 text-yellow-600",
    safe: "bg-green-50 text-green-600",
  };

  return (
    <span
      className={`rounded px-2 py-1 text-[9px] font-bold uppercase ${styles[type]}`}
    >
      {children}
    </span>
  );
};

const CommunityRisk = () => {
  const data = [
    ["Mallacoota", "Pop. 1,100 · Evac", "EXTREME", "extreme"],
    ["Orbost", "Pop. 2,400 · Watch", "HIGH", "high"],
    ["Lakes Entrance", "Pop. 6,200 · Advice", "MOD", "mod"],
    ["Cann River", "Pop. 210 · Watch", "HIGH", "high"],
    ["Genoa", "Pop. 95 · Evac", "EXTREME", "extreme"],
    ["Buchan Valley", "Pop. 840 · Clear", "SAFE", "safe"],
  ];

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex h-10 items-center border-b border-slate-200 px-4">
        <h2 className="flex-1 text-[14px] font-bold text-slate-900">
          Community Risk Scorecard
        </h2>

        <button className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] text-slate-500">
          Full report
        </button>
      </div>

      <div className="grid grid-cols-2 gap-x-6 px-4 py-3">
        {data.map(([name, desc, risk, type]) => (
          <div
            key={name}
            className="flex items-center justify-between border-b border-slate-100 py-2 last:border-b-0"
          >
            <div>
              <div className="text-[12px] font-bold text-slate-900">{name}</div>
              <div className="mt-1 text-[10px] text-slate-400">{desc}</div>
            </div>

            <RiskTag type={type}>{risk}</RiskTag>
          </div>
        ))}
      </div>
    </section>
  );
};

const CommunicationsLog = () => {
  const data = [
    [
      "13:42",
      "EMERG",
      "Emergency warning — Mallacoota. Leave immediately via Princes Hwy east.",
      "bg-red-500",
    ],
    [
      "13:15",
      "WATCH",
      "Watch & Act for Orbost — prepare to leave if threatened.",
      "bg-orange-500",
    ],
    [
      "17:02",
      "ADVICE",
      "Advice — Lakes Entrance. Wind change at 20:00 may increase risk.",
      "bg-blue-500",
    ],
    [
      "15:30",
      "MEDIA",
      "Joint press conference — DELWP, CFA and Victoria Police. Next update 18:00.",
      "bg-slate-500",
    ],
  ];

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex h-10 items-center border-b border-slate-200 px-4">
        <h2 className="flex-1 text-[14px] font-bold text-slate-900">
          Official Communications Log
        </h2>

        <button className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] text-slate-500">
          New bulletin
        </button>
      </div>

      <div>
        {data.map(([time, label, text, color]) => (
          <div
            key={`${time}-${label}`}
            className="flex items-start gap-3 border-b border-slate-100 px-4 py-2 last:border-b-0"
          >
            <span className="w-10 font-mono text-[11px] text-slate-400">
              {time}
            </span>

            <span
              className={`rounded px-2 py-0.5 text-[9px] font-bold text-white ${color}`}
            >
              {label}
            </span>

            <span className="text-[12px] leading-relaxed text-slate-600">
              {text}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
};

const Misinformation = () => {
  const data = [
    [
      "Facebook groups",
      88,
      6,
      "High",
      "bg-red-500",
      "bg-orange-50 text-orange-600",
    ],
    [
      "Twitter / X",
      55,
      4,
      "Med",
      "bg-orange-500",
      "bg-yellow-50 text-yellow-600",
    ],
    [
      "WhatsApp chains",
      38,
      3,
      "Med",
      "bg-orange-500",
      "bg-yellow-50 text-yellow-600",
    ],
    [
      "News comments",
      14,
      1,
      "Low",
      "bg-red-500",
      "bg-green-50 text-green-600",
    ],
  ];

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex h-10 items-center border-b border-slate-200 px-4">
        <h2 className="flex-1 text-[14px] font-bold text-slate-900">
          Misinformation Sources
        </h2>

        <button className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] text-slate-500">
          Review queue (6 pending)
        </button>
      </div>

      <div>
        {data.map(([name, width, count, tag, bar, tagStyle]) => (
          <div
            key={name}
            className="flex items-center gap-4 border-b border-slate-100 px-4 py-2.5 last:border-b-0"
          >
            <div className="w-[130px] text-[12px] text-slate-600">{name}</div>

            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${bar}`}
                style={{ width: `${width}%` }}
              />
            </div>

            <div className="w-5 text-right text-[12px] font-bold text-slate-900">
              {count}
            </div>

            <div
              className={`w-10 rounded px-2 py-1 text-center text-[9px] font-bold ${tagStyle}`}
            >
              {tag}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default function FireFusionAnalytics() {
  return (
    <div className="flex h-screen overflow-hidden bg-[#eef0f4]">
      <Sidebar />

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <Topbar />

        <div className="flex-1 overflow-y-auto px-5 py-4">
          <div className="space-y-3">
            <KPISection />
            <WeatherTimeline />
            <IncidentMap />

            <div className="grid grid-cols-2 gap-3">
              <CommunityRisk />
              <CommunicationsLog />
            </div>

            <Misinformation />
          </div>
        </div>
      </main>
    </div>
  );
}