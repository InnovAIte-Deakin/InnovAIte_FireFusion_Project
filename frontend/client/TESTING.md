# Frontend testing

## How to run
From the frontend/client folder: `npm install`, then `npm test`.
It runs every test once and prints a pass/fail list. It needs no backend, no internet and no browser.

## Tools
- Vitest: runs the tests (already used by Vite)
- jsdom: a pretend browser so React pages can run inside tests
- React Testing Library: renders a page and looks at it the way a user would
- user-event: clicks buttons in tests

Setup lives in `vite.config.js` (the `test` block) and `src/test/setup.ts`.

## What is covered
- `src/utils/forecastStatus.test.ts` (19 tests): the rules that decide Live / Stale / Sample / Unverified / Unavailable.
- `src/components/MapPage/ForecastStatusBadge.test.tsx` (17 tests): each badge shows the right words and age text, and the Try again button appears only when unavailable.
- `src/pages/FireRiskMap.test.tsx` (20 tests): the whole Fire Risk Map page with a fake forecast server.

### Fire Risk Map page tests
- Successful forecast: one polygon per forecast area; colours match risk (1 = most severe); badge says Live with the age; old data says Stale; Live turns into Stale as time passes; a live WebSocket update replaces the polygons.
- Sample / unproven data: sample is never shown as Live; no freshness information shows Unverified; an unknown source such as "mock" shows Unverified; a WebSocket update labelled sample replaces a Live label.
- Loading: the badge says Loading until the forecast arrives.
- Unavailable: 503 (with an error body, and with a valid-looking body), network failure, bare null, a body that is not a forecast, and an empty forecast all show Unavailable and draw nothing. Try again recovers once the backend is back.

## What is NOT covered yet
- Nothing here talks to the real backend, so it cannot catch a mismatch between the backend and the frontend. A manual check with the backend running is still needed.
- The search box, legend and sidebar have no tests.
- Map tiles (the OpenStreetMap background) and real-browser behaviour are not tested.
- Backend freshness fields (`metadata`) are still a proposal. The tests use that proposed shape.

## Test-environment notes
jsdom is not a real browser, so `src/test/setup.ts` gives map elements a size of 800 x 600 and says SVG drawing is supported. Without both, Leaflet draws no polygons in tests.

## Results (27 Nov 2026)
Test Files: 3 passed (3). Tests: 56 passed (56). Run four times with the same result.
Each rule was also checked by breaking the code on purpose: treating sample data as live, ignoring an HTTP 503, and ignoring WebSocket updates each made tests fail, then the code was restored.
