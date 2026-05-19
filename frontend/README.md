# FireFusion Frontend

This folder contains the frontend application for the FireFusion project.

FireFusion is an AI-driven bushfire forecasting and misinformation monitoring dashboard for Victoria. The frontend provides the user interface for viewing bushfire risk information, misinformation review workflows, alerts, reports, settings, emergency advice, and related system pages.

## Frontend Purpose

The frontend is designed to present complex bushfire forecasting and misinformation detection outputs in a clear and usable dashboard for emergency managers, local councils, and disaster response teams.

The main frontend focus is:

- Building a consistent dashboard interface
- Connecting all frontend pages through routing
- Maintaining a shared sidebar, topbar, footer, spacing, and page layout
- Preparing frontend pages for backend API integration
- Supporting future development by making setup and navigation clear
- Making the system easy for future team members to run, test, and continue

## Project Structure

```text
frontend/
└── client/
    ├── src/
    │   ├── components/
    │   │   ├── Sidebar.jsx
    │   │   └── shared components
    │   ├── pages/
    │   │   ├── AboutUs.jsx
    │   │   ├── Analytics.jsx
    │   │   ├── BushfireForecastDetails.jsx
    │   │   ├── Dashboard.jsx
    │   │   ├── DataSourcesMethod.jsx
    │   │   ├── EmergencyAdvice.jsx
    │   │   ├── Feedback.jsx
    │   │   ├── FireRiskMap.tsx
    │   │   ├── Login.jsx
    │   │   ├── MisinformationLanding.jsx
    │   │   ├── MisinformationReview.jsx
    │   │   ├── Settings.css
    │   │   ├── Settings.jsx
    │   │   ├── Signup.jsx
    │   │   └── UserProfile.jsx
    │   ├── App.css
    │   ├── App.jsx
    │   ├── index.css
    │   └── main.jsx
    ├── package.json
    ├── package-lock.json
    └── vite.config.js
```

## Technologies Used

The frontend uses:

- React
- Vite
- JavaScript
- TypeScript for selected pages
- CSS
- lucide-react icons
- Git and GitHub

The full project also uses backend services through Docker.

## Requirements Before Running the Project

Before running the project, make sure these are installed:

- VS Code
- Node.js
- npm
- Docker Desktop
- Git

Before running the backend, open Docker Desktop and wait until it is fully started.

## How to Run the Full Project Locally

To view the FireFusion frontend website properly, run the backend and frontend in two separate terminals.

Use:

- Terminal 1 for the backend
- Terminal 2 for the frontend

The backend provides API services and data support. The frontend displays the FireFusion website interface.

## Step 1: Run the Backend

Open the first terminal in VS Code.

From the main project folder, go to the backend folder:

```powershell
cd backend
```

Then run the backend using Docker:

```powershell
docker compose --profile default up -d --build
```

This command will build and start the backend services.

Keep Docker Desktop open while the backend is running.

To check whether the backend containers are running, use:

```powershell
docker compose ps
```

To stop the backend later, run this inside the `backend` folder:

```powershell
docker compose down
```

To restart the backend from the beginning:

```powershell
docker compose down
docker compose --profile default up -d --build
```

## Step 2: Run the Frontend

Open a second terminal in VS Code.

From the main project folder, go to the frontend client folder:

```powershell
cd frontend/client
```

Install frontend dependencies:

```powershell
npm install
```

Then start the frontend:

```powershell
npm run dev
```

The terminal should show something similar to:

```text
VITE v5.4.21 ready

Local: http://localhost:5173/
```

Open this link in the browser:

```text
http://localhost:5173/
```

This will show the FireFusion frontend website.

## Full Command Summary

### Backend Terminal

```powershell
cd backend
docker compose --profile default up -d --build
```

### Frontend Terminal

```powershell
cd frontend/client
npm install
npm run dev
```

## Recommended Running Order

Use this order when running the full project:

```text
1. Open Docker Desktop
2. Open VS Code
3. Open Terminal 1
4. Run the backend commands
5. Open Terminal 2
6. Run the frontend commands
7. Open http://localhost:5173/ in the browser
```

## When to Run Only the Frontend

If you only want to check the website design, page layout, sidebar, buttons, colours, spacing, or navigation, you can run only the frontend.

```powershell
cd frontend/client
npm run dev
```

Then open:

```text
http://localhost:5173/
```

Running only the frontend is useful for design review and UI testing.

## When to Run Backend and Frontend Together

Run both backend and frontend when testing pages that need backend data, API responses, model outputs, or database-related features.

Examples include:

- Dashboard data connected to APIs
- Fire risk data
- Bushfire forecast details
- Reports data
- Misinformation review data
- Any page that depends on backend services

## Current Frontend Pages

Current frontend pages include:

- Dashboard
- Login
- Signup
- Fire Risk Map
- Misinformation Review
- Misinformation Landing
- Bushfire Forecast Details
- Analytics
- Settings
- About Us
- Feedback
- Emergency Advice
- User Profile
- Data Sources and Method

Additional pages may be added as the project develops.

## Routing and Navigation Notes

The main frontend routing is handled in:

```text
src/App.jsx
```

The sidebar navigation is handled in:

```text
src/components/Sidebar.jsx
```

When adding a new page:

1. Create the page inside `src/pages/`
2. Import the page into `App.jsx`
3. Add the correct route or path condition
4. Add the page link in `Sidebar.jsx` if it should appear in the sidebar
5. Test the page locally before pushing changes

Example page import:

```jsx
import Reports from "./pages/Reports.jsx";
```

Example route condition:

```jsx
if (path === "/reports") {
  return <Reports />;
}
```

The path in `Sidebar.jsx` must match the path used in `App.jsx`.

Example:

```jsx
path: "/reports"
```

and:

```jsx
if (path === "/reports") {
  return <Reports />;
}
```

## Shared Layout Rules

All frontend pages should follow the same layout and visual style.

Use the same:

- Sidebar
- Topbar where applicable
- Footer where applicable
- Page spacing
- Cards
- Buttons
- Badges
- Tables
- Colours
- Typography
- Page width and alignment

Do not create a completely separate page style unless the frontend lead or team has approved it.

The goal is to make FireFusion feel like one complete system rather than separate pages built by different people.

## Frontend Design Review Checklist

Before pushing frontend changes, check:

- The page opens without errors
- The design matches the shared dashboard style
- Sidebar navigation works correctly
- Buttons and links go to the correct pages
- The page looks clean on different screen sizes
- No unused imports are left in the file
- No broken file paths are included
- No temporary testing text is left on the page
- No private files, API keys, or personal data are committed

## GitHub Workflow

Before starting new work, always pull the latest `main` branch:

```powershell
git checkout main
git pull origin main
```

Create a new branch for your work:

```powershell
git checkout -b feature/your-page-name
```

After making changes:

```powershell
git status
git add .
git commit -m "Update frontend page"
git push origin feature/your-page-name
```

Then create a Pull Request into `main`.

## Important GitHub Rules

- Do not push incomplete work directly to `main`
- Use a feature branch for each page or fix
- Keep commit messages clear and meaningful
- Pull the latest `main` before starting new work
- Test the frontend locally before opening a Pull Request
- Review page layout and routing before merging
- Avoid committing API keys, `.env` files, personal files, or temporary files

## Suggested Branch Names

Use clear branch names such as:

```text
feature/dashboard-update
feature/fire-risk-map
feature/reports-page
feature/settings-page
fix/sidebar-navigation
fix/login-routing
```

## Suggested Commit Messages

Use clear commit messages such as:

```text
Update dashboard layout
Add reports page routing
Fix sidebar navigation
Add frontend README documentation
Update settings page design
Connect sign out button to login page
```

## Pull Request Checklist

Before creating a Pull Request, make sure:

- The project runs locally
- `npm run dev` works
- The page opens in the browser
- The sidebar link works
- The design matches the shared layout
- No console errors appear in the browser
- No terminal errors appear in VS Code
- The branch is updated with the latest `main`
- Only relevant files are included in the commit

Useful commands:

```powershell
npm run dev
npm run build
git status
```

## Common Frontend Issues

### Frontend does not start

Run:

```powershell
cd frontend/client
npm install
npm run dev
```

### Page is blank

Check:

- The page is imported correctly in `App.jsx`
- The page file name is correct
- The component is exported correctly
- The path in `Sidebar.jsx` matches the path in `App.jsx`
- There are no terminal errors
- There are no browser console errors

### Sidebar link does not open the correct page

Check that the sidebar path and `App.jsx` path are exactly the same.

Example:

```jsx
path: "/settings"
```

and:

```jsx
if (path === "/settings") {
  return <Settings />;
}
```

### Port issue

The frontend normally runs on:

```text
http://localhost:5173/
```

If port `5173` is already used, Vite may start on another port. Use the local link shown in the terminal.

### Dependency issue

Try reinstalling dependencies:

```powershell
cd frontend/client
npm install
npm run dev
```

If the issue continues on Windows PowerShell, remove `node_modules` and reinstall:

```powershell
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
npm run dev
```

## Common Backend Issues

### Docker command does not work

Make sure Docker Desktop is open.

Then run again:

```powershell
cd backend
docker compose --profile default up -d --build
```

### Backend containers are not running

Check with:

```powershell
docker compose ps
```

### Stop and restart backend

```powershell
docker compose down
docker compose --profile default up -d --build
```

### Frontend cannot connect to backend

Check:

- Docker Desktop is running
- Backend containers are running
- Backend was started from the `backend` folder
- Frontend was started from `frontend/client`
- The API URL is correct
- Any required `.env` file is configured
- CORS is enabled in the backend if needed

## Environment and Security Notes

Do not commit:

- `.env` files
- API keys
- Passwords
- Personal files
- Local test files
- Temporary screenshots
- Unrelated folders

If environment variables are required, create a local `.env` file based on team instructions or backend documentation.

## Notes for Future Frontend Members

Please run the project locally before making changes.

For design-only work, running the frontend is enough.

For API-connected pages, run both backend and frontend.

Always check the existing Dashboard and Sidebar structure before adding new pages.

Reuse shared components where possible.

Keep page design consistent with the FireFusion dashboard style.

## Current Frontend Priority

The current frontend priority is:

1. Integrate all completed frontend pages
2. Keep one consistent shared layout
3. Connect pages through sidebar navigation
4. Review pages before merging
5. Prepare frontend pages for backend API data
6. Test the final website flow for demonstration
7. Keep documentation clear for future team members

## Quick Start

Use this when you already know the setup and just want to run the project.

### Backend

```powershell
cd backend
docker compose --profile default up -d --build
```

### Frontend

```powershell
cd frontend/client
npm install
npm run dev
```

Then open:

```text
http://localhost:5173/
```
