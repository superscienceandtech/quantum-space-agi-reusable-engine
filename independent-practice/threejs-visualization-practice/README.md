# Three.js Visualization Practice

An isolated beginner practice project for learning Three.js fundamentals. It is separate from the ARC-09 prototype, the chart practice project, and production application code. Day 8 builds on the Day 7 scene; it does not add production or API integration.

## What it demonstrates

- A Three.js scene, perspective camera, and WebGL renderer.
- A restrained procedural star field, simple planet, basic spacecraft, lighting, and orbital path.
- A small animation loop, responsive renderer resizing, and a restrained star field.
- A more detailed lightweight spacecraft with body, nose, solar panels, panel details, fins, and engine details.
- Mouse/touch camera controls plus start/stop animation and reset-view buttons.
- A text description for the scene, meaningful button names, visible keyboard focus, and reduced-motion support.
- Beginner comments in `main.js` explaining scene setup, controls, rendering, and resource cleanup.

All objects are illustrative practice geometry. They are not NASA data, a real spacecraft, or a scientifically scaled mission simulation.

## Dependency and environment

This environment did not have Node.js/npm available, so no package installation or local Three.js dependency was added. The HTML import map loads Three.js **0.180.0** and its `OrbitControls` add-on from jsDelivr. You need internet access when loading the page. The core library and add-on use the same pinned version and CDN.

The page uses JavaScript modules and should be served over HTTP rather than opened as a `file://` URL. VS Code Live Server is available in the inspected editor environment.

## Run in VS Code

1. Open this folder in VS Code.
2. In `index.html`, right-click and choose **Open with Live Server**.
3. The browser should open the local page. If it does not, open the local URL shown by Live Server.

Alternatively, if Python 3 is installed on your computer, open a terminal in this folder and run:

```powershell
python -m http.server 8000
```

Then visit `http://localhost:8000`. Python was not available in the environment used to create this project, so that command was not run here.

## Controls and keyboard use

- Drag inside the 3D scene to orbit the camera; scroll or pinch to zoom.
- Use **Start animation** / **Stop animation** to control planet rotation and spacecraft movement.
- Use **Reset view** to return the camera to its initial position.
- Tab to either button and press Enter or Space to activate it. The buttons have visible focus outlines and descriptive accessible names.
- If the operating system requests reduced motion, animation begins stopped. You can start it manually.

The playback and reset buttons are outside the renderer canvas, which receives camera pointer and touch gestures. This keeps button clicks separate from camera dragging.

## Performance decisions

- Reuses spacecraft geometries and materials for repeated parts; objects are created during initialization, never inside the frame loop.
- Caps renderer pixel ratio at 1.75 to avoid unnecessarily large drawing buffers on high-density screens.
- Requests frames continuously only while animation is running. When stopped, camera-control changes request frames as needed.
- Cancels scheduled frames while the document is hidden and resumes rendering when it becomes visible.
- Disposes scene geometries, materials, controls, and renderer on page exit.
- No benchmark was run, so these are implementation choices rather than measured performance improvements.

## Browser verification checklist

1. Confirm the scene shows the planet, star field, orbital ring, and spacecraft.
2. Drag in the scene to rotate the camera; scroll or pinch to zoom. Confirm the separate controls do not trigger camera dragging.
3. Select **Stop animation**, confirm the planet and spacecraft stop, then select **Start animation**.
4. Select **Reset view** and confirm the camera returns to its initial position.
5. Resize to desktop and narrow mobile widths; check the canvas and controls for clipping or horizontal overflow.
6. Use keyboard Tab to reach both buttons; check their visible focus indicator and activate them with Enter or Space.
7. Enable the operating system's reduced-motion preference and reload; confirm animation starts stopped, then test manual start.
8. Switch to another tab while animation runs, return, and confirm the scene resumes.
9. Check the browser console for module, CDN, and WebGL errors.

## Verification status

- Project structure, local file references, event wiring, and animation-loop patterns were source-checked.
- No Node.js/npm was available, so JavaScript syntax checks and package-based checks were not run.
- Browser rendering and interactive behavior were not verified in this environment.
- No performance benchmark was run.
- This remains an independent practice project. Day 9 API integration has not been started.
