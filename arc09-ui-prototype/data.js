/* Synthetic layout-review examples only. Not NASA or actual mission data. */
window.arc09PrototypeData = Object.freeze({
  overview: Object.freeze([
    Object.freeze({ label: 'Sample missions', value: '03', detail: 'Illustrative count', icon: '▦', tone: 'blue' }),
    Object.freeze({ label: 'Draft samples', value: '01', detail: 'Illustrative status', icon: '◷', tone: 'teal' }),
    Object.freeze({ label: 'Review samples', value: '02', detail: 'Illustrative status', icon: '✓', tone: 'amber' })
  ]),
  resources: Object.freeze([
    Object.freeze({ label: 'Sample allocation A', value: 68, unit: '%', detail: 'Synthetic share · no limit implied' }),
    Object.freeze({ label: 'Sample allocation B', value: 42, unit: '%', detail: 'Synthetic share · no limit implied' })
  ]),
  trend: Object.freeze([
    Object.freeze({ step: 1, value: 4 }),
    Object.freeze({ step: 2, value: 6 }),
    Object.freeze({ step: 3, value: 5 }),
    Object.freeze({ step: 4, value: 8 }),
    Object.freeze({ step: 5, value: 9 })
  ]),
  comparison: Object.freeze([
    Object.freeze({ category: 'A', seriesA: 5, seriesB: 7 }),
    Object.freeze({ category: 'B', seriesA: 8, seriesB: 6 }),
    Object.freeze({ category: 'C', seriesA: 6, seriesB: 9 })
  ]),
  scatter: Object.freeze([
    Object.freeze({ x: 1, y: 2 }),
    Object.freeze({ x: 2, y: 3 }),
    Object.freeze({ x: 3, y: 3 }),
    Object.freeze({ x: 4, y: 5 }),
    Object.freeze({ x: 5, y: 4 })
  ]),
  relationshipGraph: Object.freeze({
    label: 'Conceptual relationship example',
    nodes: Object.freeze([
      Object.freeze({ id: 'mission', label: 'Mission' }),
      Object.freeze({ id: 'spacecraft', label: 'Spacecraft' }),
      Object.freeze({ id: 'payload', label: 'Payload' }),
      Object.freeze({ id: 'resources', label: 'Resources' }),
      Object.freeze({ id: 'simulation', label: 'Simulation' })
    ]),
    edges: Object.freeze([
      Object.freeze({ from: 'mission', to: 'spacecraft', label: 'Illustrative association' }),
      Object.freeze({ from: 'spacecraft', to: 'payload', label: 'Illustrative association' }),
      Object.freeze({ from: 'mission', to: 'resources', label: 'Illustrative association' }),
      Object.freeze({ from: 'mission', to: 'simulation', label: 'Illustrative association' })
    ])
  }),
  activity: Object.freeze([
    Object.freeze({ title: 'Sample plan alpha', action: 'Draft layout opened', status: 'Planning', time: 'Sample entry 01' }),
    Object.freeze({ title: 'Sample plan beta', action: 'Review state shown', status: 'In progress', time: 'Sample entry 02' }),
    Object.freeze({ title: 'Sample plan gamma', action: 'Placeholder review completed', status: 'Reviewed', time: 'Sample entry 03' })
  ])
});
