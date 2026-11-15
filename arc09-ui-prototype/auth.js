/* Clerk sign-in controller; session tokens stay in memory and on request. */
(function () {
  const signInMount = document.getElementById('clerk-sign-in');
  const userButtonMount = document.getElementById('clerk-user-button');
  const headerStatus = document.getElementById('clerk-auth-status');
  const missionStatus = document.getElementById('mission-demo-auth-status');
  const state = {
    configured: false,
    signedIn: false,
    clerk: null,
    mountedSignedIn: null
  };

  function setStatus(message, failed = false) {
    [headerStatus, missionStatus].filter(Boolean).forEach((host) => {
      host.textContent = message;
      host.setAttribute('role', failed ? 'alert' : 'status');
      host.setAttribute('aria-live', failed ? 'assertive' : 'polite');
      if (failed) host.dataset.tone = 'error';
      else host.removeAttribute('data-tone');
    });
  }

  function publishState() {
    window.dispatchEvent(new CustomEvent('nasaq-auth:state', {
      detail: {
        signedIn: state.signedIn,
        configured: state.configured
      }
    }));
  }

  function loadScript(source, attributes = {}) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      const timeout = window.setTimeout(() => {
        script.remove();
        reject(new Error('Clerk script loading timed out.'));
      }, 10000);
      script.src = source;
      script.async = true;
      script.crossOrigin = 'anonymous';
      Object.entries(attributes).forEach(([name, value]) => {
        script.setAttribute(name, value);
      });
      script.onload = () => {
        window.clearTimeout(timeout);
        resolve();
      };
      script.onerror = () => {
        window.clearTimeout(timeout);
        reject(new Error('Clerk script could not be loaded.'));
      };
      document.head.appendChild(script);
    });
  }

  function renderClerkMounts(signedIn) {
    if (state.mountedSignedIn === signedIn) return;
    state.mountedSignedIn = signedIn;
    if (signInMount) {
      signInMount.replaceChildren();
      signInMount.hidden = signedIn || !state.configured;
    }
    if (userButtonMount) {
      userButtonMount.replaceChildren();
      userButtonMount.hidden = !signedIn;
    }
    if (signedIn) {
      state.clerk.mountUserButton(userButtonMount);
    } else if (state.configured) {
      state.clerk.mountSignIn(signInMount);
    }
  }

  function updateSignedInState() {
    state.signedIn = Boolean(state.clerk && state.clerk.isSignedIn);
    renderClerkMounts(state.signedIn);
    setStatus(
      state.signedIn
        ? 'Signed in. Synthetic mission operations are available.'
        : 'Sign in to access the synthetic mission demo.'
    );
    publishState();
  }

  async function initialize() {
    try {
      const response = await fetch('/api/v1/auth/config', {
        headers: { Accept: 'application/json' }
      });
      if (!response.ok) throw new Error('Authentication configuration unavailable.');
      const configuration = await response.json();
      if (!configuration || typeof configuration.enabled !== 'boolean') {
        throw new Error('Authentication configuration is invalid.');
      }
      if (!configuration.enabled) {
        setStatus('Clerk sign-in is not configured. Mission operations are disabled.');
        publishState();
        return;
      }
      if (
        typeof configuration.publishable_key !== 'string' ||
        typeof configuration.frontend_api_url !== 'string'
      ) {
        throw new Error('Authentication configuration is invalid.');
      }

      const frontendApiUrl = new URL(configuration.frontend_api_url);
      const localHttpHost = ['localhost', '127.0.0.1', '[::1]']
        .includes(frontendApiUrl.hostname);
      if (
        frontendApiUrl.protocol !== 'https:' &&
        !(frontendApiUrl.protocol === 'http:' && localHttpHost)
      ) {
        throw new Error('Clerk must be loaded from a secure Frontend API URL.');
      }
      state.configured = true;
      const frontendApiOrigin = frontendApiUrl.origin;
      await loadScript(`${frontendApiOrigin}/npm/@clerk/ui@1/dist/ui.browser.js`);
      await loadScript(
        `${frontendApiOrigin}/npm/@clerk/clerk-js@6/dist/clerk.browser.js`,
        { 'data-clerk-publishable-key': configuration.publishable_key }
      );
      if (!window.Clerk || typeof window.Clerk.load !== 'function') {
        throw new Error('ClerkJS did not initialize.');
      }
      state.clerk = window.Clerk;
      await state.clerk.load({
        ui: { ClerkUI: window.__internal_ClerkUICtor }
      });
      if (typeof state.clerk.addListener !== 'function') {
        throw new Error('Clerk session updates are unavailable.');
      }
      state.clerk.addListener(updateSignedInState);
      updateSignedInState();
    } catch (error) {
      state.signedIn = false;
      if (signInMount) signInMount.hidden = true;
      if (userButtonMount) userButtonMount.hidden = true;
      setStatus(
        state.configured
          ? 'Clerk sign-in could not be initialized. Mission operations are disabled.'
          : 'Sign-in configuration could not be loaded. Mission operations are disabled.',
        true
      );
      publishState();
    }
  }

  const ready = initialize();
  window.nasaqAuth = Object.freeze({
    ready,
    getToken: async function () {
      if (!state.signedIn || !state.clerk || !state.clerk.session) return null;
      const token = await state.clerk.session.getToken();
      return typeof token === 'string' && token ? token : null;
    },
    isSignedIn: function () {
      return Boolean(state.clerk && state.clerk.isSignedIn);
    }
  });
}());
