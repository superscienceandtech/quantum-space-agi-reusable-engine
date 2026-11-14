import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const host = document.querySelector('#scene-canvas');
const status = document.querySelector('#scene-status');
const animationButton = document.querySelector('#animation-button');
const resetButton = document.querySelector('#reset-button');
const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

function showSceneError(message) {
  if (status) {
    status.textContent = message;
    status.dataset.state = 'error';
  }
  if (animationButton) animationButton.disabled = true;
  if (resetButton) resetButton.disabled = true;
}

if (!host || !status || !animationButton || !resetButton) {
  console.error('The scene page is missing a required element.');
  showSceneError('The 3D scene is missing a required page element.');
} else {
  try {
    // A scene is the container for every 3D object, light, and background.
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#050b14');

    // The perspective camera gives nearby and distant objects a 3D depth effect.
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    const homePosition = new THREE.Vector3(8, 5, 11);
    camera.position.copy(homePosition);

    // The renderer draws the scene into a WebGL canvas inside the page.
    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    renderer.setSize(host.clientWidth, host.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.domElement.setAttribute('role', 'img');
    renderer.domElement.setAttribute('aria-label', 'Illustration of a planet, stars, an orbital path, and a spacecraft.');
    host.append(renderer.domElement);

    // Broad ambient light prevents dark surfaces from disappearing.
    scene.add(new THREE.AmbientLight(0x9db9df, 1.25));
    // A directional light creates a clear light side and shadow side on the planet.
    const sunLight = new THREE.DirectionalLight(0xffe0ad, 3.2);
    sunLight.position.set(-5, 7, 6);
    scene.add(sunLight);
    const fillLight = new THREE.PointLight(0x3d8dc7, 18, 24);
    fillLight.position.set(5, -3, -4);
    scene.add(fillLight);

    // A seeded pseudo-random generator keeps the decorative star field stable.
    let seed = 2409;
    function randomUnit() {
      seed = (seed * 16807) % 2147483647;
      return (seed - 1) / 2147483646;
    }

    // BufferGeometry stores all star points together to keep the scene lightweight.
    const starPositions = new Float32Array(360 * 3);
    for (let i = 0; i < 360; i += 1) {
      const radius = 18 + randomUnit() * 28;
      const theta = randomUnit() * Math.PI * 2;
      const vertical = (randomUnit() - 0.5) * 36;
      starPositions[i * 3] = Math.cos(theta) * radius;
      starPositions[i * 3 + 1] = vertical;
      starPositions[i * 3 + 2] = Math.sin(theta) * radius;
    }
    const starGeometry = new THREE.BufferGeometry();
    starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
    const starMaterial = new THREE.PointsMaterial({ color: 0xb9d6ff, size: 0.12, sizeAttenuation: true });
    scene.add(new THREE.Points(starGeometry, starMaterial));

    // A sphere geometry and standard material form the central illustrative planet.
    const planetGeometry = new THREE.SphereGeometry(2, 48, 32);
    const planetMaterial = new THREE.MeshStandardMaterial({
      color: 0x287db4,
      roughness: 0.7,
      metalness: 0.03,
    });
    const planet = new THREE.Mesh(planetGeometry, planetMaterial);
    scene.add(planet);

    // A translucent outer sphere gives the planet a soft edge without post-processing.
    const atmosphereGeometry = new THREE.SphereGeometry(2.08, 40, 28);
    const atmosphereMaterial = new THREE.MeshBasicMaterial({
      color: 0x61b9ee,
      transparent: true,
      opacity: 0.1,
      side: THREE.BackSide,
      depthWrite: false,
    });
    planet.add(new THREE.Mesh(atmosphereGeometry, atmosphereMaterial));

    // The orbital path is a line loop in the planet's XZ plane.
    const orbitRadius = 4.3;
    const orbitPoints = [];
    for (let i = 0; i < 128; i += 1) {
      const angle = (i / 128) * Math.PI * 2;
      orbitPoints.push(new THREE.Vector3(Math.cos(angle) * orbitRadius, 0, Math.sin(angle) * orbitRadius));
    }
    const orbitGeometry = new THREE.BufferGeometry().setFromPoints(orbitPoints);
    const orbitMaterial = new THREE.LineBasicMaterial({ color: 0x6685aa, transparent: true, opacity: 0.7 });
    scene.add(new THREE.LineLoop(orbitGeometry, orbitMaterial));

    // Reuse these materials and geometries for the spacecraft's repeated parts.
    const spacecraft = new THREE.Group();
    const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0xe1e8f0, metalness: 0.35, roughness: 0.42 });
    const panelMaterial = new THREE.MeshStandardMaterial({
      color: 0x28618e,
      metalness: 0.28,
      roughness: 0.38,
      emissive: 0x102b45,
    });
    const detailMaterial = new THREE.MeshStandardMaterial({ color: 0x526b83, metalness: 0.3, roughness: 0.5 });
    const engineMaterial = new THREE.MeshStandardMaterial({
      color: 0xffbd72,
      emissive: 0xff6d25,
      emissiveIntensity: 1.2,
      roughness: 0.35,
    });

    const bodyGeometry = new THREE.CylinderGeometry(0.16, 0.2, 0.9, 12);
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    body.rotation.x = Math.PI / 2;
    spacecraft.add(body);

    const noseGeometry = new THREE.ConeGeometry(0.17, 0.38, 12);
    const nose = new THREE.Mesh(noseGeometry, bodyMaterial);
    nose.rotation.x = -Math.PI / 2;
    nose.position.z = -0.61;
    spacecraft.add(nose);

    // The aft nozzle and bright engine center make the rear of the craft distinct.
    const nozzleGeometry = new THREE.CylinderGeometry(0.2, 0.12, 0.34, 12);
    const nozzle = new THREE.Mesh(nozzleGeometry, detailMaterial);
    nozzle.rotation.x = Math.PI / 2;
    nozzle.position.z = 0.57;
    spacecraft.add(nozzle);
    const engineGeometry = new THREE.SphereGeometry(0.105, 10, 8);
    const engine = new THREE.Mesh(engineGeometry, engineMaterial);
    engine.position.z = 0.75;
    spacecraft.add(engine);

    // Broad panel wings are joined to the body with small, reused support struts.
    const panelGeometry = new THREE.BoxGeometry(0.78, 0.045, 0.38);
    const leftPanel = new THREE.Mesh(panelGeometry, panelMaterial);
    leftPanel.position.x = -0.66;
    spacecraft.add(leftPanel);
    const rightPanel = new THREE.Mesh(panelGeometry, panelMaterial);
    rightPanel.position.x = 0.66;
    spacecraft.add(rightPanel);

    const panelCellGeometry = new THREE.BoxGeometry(0.018, 0.052, 0.38);
    const strutGeometry = new THREE.BoxGeometry(0.36, 0.04, 0.07);
    for (const side of [-1, 1]) {
      for (const offset of [-0.24, 0, 0.24]) {
        const cellDivider = new THREE.Mesh(panelCellGeometry, detailMaterial);
        cellDivider.position.set(side * (0.66 + offset), 0, 0);
        spacecraft.add(cellDivider);
      }
      const strut = new THREE.Mesh(strutGeometry, detailMaterial);
      strut.position.set(side * 0.34, 0, 0);
      spacecraft.add(strut);
    }

    // Small fins add a silhouette cue; both share the same geometry and material.
    const finGeometry = new THREE.BoxGeometry(0.24, 0.055, 0.34);
    const leftFin = new THREE.Mesh(finGeometry, detailMaterial);
    leftFin.position.set(-0.19, -0.15, 0.28);
    spacecraft.add(leftFin);
    const rightFin = new THREE.Mesh(finGeometry, detailMaterial);
    rightFin.position.set(0.19, -0.15, 0.28);
    spacecraft.add(rightFin);
    scene.add(spacecraft);

    // OrbitControls act only on the canvas; the buttons are outside its hit area.
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.07;
    controls.target.set(0, 0, 0);
    controls.minDistance = 6;
    controls.maxDistance = 24;

    let animationRunning = !reducedMotionQuery.matches;
    let orbitAngle = 0;
    let frameId = null;
    let lastFrameTime = 0;
    let disposed = false;

    function updateAnimationButton() {
      animationButton.textContent = animationRunning ? 'Stop animation' : 'Start animation';
      animationButton.setAttribute('aria-label', animationRunning ? 'Stop scene animation' : 'Start scene animation');
    }

    function scheduleFrame() {
      if (frameId === null && !document.hidden && !disposed) {
        frameId = window.requestAnimationFrame(renderFrame);
      }
    }

    function renderFrame(timestamp) {
      frameId = null;
      if (disposed || document.hidden) return;

      const deltaSeconds = lastFrameTime === 0 ? 0 : Math.min((timestamp - lastFrameTime) / 1000, 0.05);
      lastFrameTime = timestamp;
      if (animationRunning) {
        planet.rotation.y += deltaSeconds * 0.16;
        orbitAngle += deltaSeconds * 0.32;
        spacecraft.position.set(
          Math.cos(orbitAngle) * orbitRadius,
          0.16 * Math.sin(orbitAngle * 2),
          Math.sin(orbitAngle) * orbitRadius,
        );
        spacecraft.rotation.y = -orbitAngle;
      }

      controls.update();
      renderer.render(scene, camera);
      if (animationRunning) scheduleFrame();
    }

    function resizeRenderer() {
      const width = host.clientWidth;
      const height = host.clientHeight;
      if (width === 0 || height === 0) return;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
      scheduleFrame();
    }

    function handleVisibilityChange() {
      if (document.hidden) {
        if (frameId !== null) window.cancelAnimationFrame(frameId);
        frameId = null;
        lastFrameTime = 0;
      } else {
        lastFrameTime = 0;
        scheduleFrame();
      }
    }

    function handleMotionPreferenceChange(event) {
      if (event.matches && animationRunning) {
        animationRunning = false;
        updateAnimationButton();
        lastFrameTime = 0;
        scheduleFrame();
      }
    }

    animationButton.addEventListener('click', () => {
      animationRunning = !animationRunning;
      updateAnimationButton();
      lastFrameTime = 0;
      scheduleFrame();
    });

    resetButton.addEventListener('click', () => {
      camera.position.copy(homePosition);
      controls.target.set(0, 0, 0);
      controls.update();
      scheduleFrame();
    });

    // When playback is stopped, camera changes still request frames as needed.
    controls.addEventListener('change', scheduleFrame);
    window.addEventListener('resize', resizeRenderer);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    reducedMotionQuery.addEventListener('change', handleMotionPreferenceChange);
    window.addEventListener('pagehide', disposeScene, { once: true });

    function disposeScene() {
      if (disposed) return;
      disposed = true;
      if (frameId !== null) window.cancelAnimationFrame(frameId);
      controls.removeEventListener('change', scheduleFrame);
      controls.dispose();
      window.removeEventListener('resize', resizeRenderer);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      reducedMotionQuery.removeEventListener('change', handleMotionPreferenceChange);

      // Dispose each shared GPU resource once before releasing the renderer.
      const geometries = new Set();
      const materials = new Set();
      scene.traverse((object) => {
        if (object.geometry) geometries.add(object.geometry);
        if (object.material) {
          for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
            materials.add(material);
          }
        }
      });
      geometries.forEach((geometry) => geometry.dispose());
      materials.forEach((material) => material.dispose());
      renderer.dispose();
    }

    updateAnimationButton();
    status.textContent = 'Drag to orbit · Scroll or pinch to zoom';
    spacecraft.position.set(orbitRadius, 0, 0);
    resizeRenderer();
    scheduleFrame();
  } catch (error) {
    console.error('Unable to initialize the 3D scene.', error);
    showSceneError('The 3D scene could not start. Check WebGL support and your internet connection, then reload.');
  }
}
