/* Synchronous provider for the isolated ARC-09 prototype fixture only. */
(function () {
  window.arc09PrototypeProvider = Object.freeze({
    getData() {
      const data = window.arc09PrototypeData;
      if (!data || typeof data !== 'object') {
        throw new Error('Synthetic prototype fixture data is unavailable.');
      }
      return data;
    }
  });
}());
