/* Pure shape checks for the isolated ARC-09 prototype fixture. */
(function () {
  function isRecord(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }

  function hasRecords(collection, stringFields = [], numericFields = []) {
    return Array.isArray(collection) && Array.from(collection).every((record) => isRecord(record) &&
      stringFields.every((field) => typeof record[field] === 'string') &&
      numericFields.every((field) => typeof record[field] === 'number' && Number.isFinite(record[field])));
  }

  function hasValidPrototypeData(data) {
    return isRecord(data) &&
      hasRecords(data.overview, ['label', 'value', 'detail', 'icon', 'tone']) &&
      hasRecords(data.resources, ['label', 'unit', 'detail'], ['value']) &&
      hasRecords(data.trend, [], ['step', 'value']) &&
      hasRecords(data.comparison, ['category'], ['seriesA', 'seriesB']) &&
      hasRecords(data.scatter, [], ['x', 'y']) &&
      isRecord(data.relationshipGraph) &&
      hasRecords(data.relationshipGraph.nodes, ['id', 'label']) &&
      hasRecords(data.relationshipGraph.edges, ['from', 'to', 'label']) &&
      hasRecords(data.activity, ['title', 'action', 'status', 'time']);
  }

  window.arc09PrototypeValidation = Object.freeze({ hasValidPrototypeData });
}());
