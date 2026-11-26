// Runs before every test file.
import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Remove anything a test put on the page so tests cannot affect each other.
afterEach(() => {
  cleanup()
})

// jsdom has no real layout, so every element reports a size of 0 x 0.
// Leaflet cannot draw on a map with no size, so we pretend the map is 800 x 600.
Object.defineProperty(HTMLElement.prototype, 'clientWidth', { configurable: true, value: 800 })
Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, value: 600 })

// Leaflet only draws polygons if the browser says it supports SVG (it checks for createSVGRect).
// jsdom does not, so we add a stand-in. Without this, Leaflet draws nothing in tests.
;(SVGSVGElement.prototype as unknown as { createSVGRect: () => object }).createSVGRect = () => ({})
