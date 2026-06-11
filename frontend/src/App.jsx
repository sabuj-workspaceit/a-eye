import { useState, useEffect } from 'react';
import EyeVisualizer from './components/EyeVisualizer';
import FaceVisualizer from './components/FaceVisualizer';
import TongueVisualizer from './components/TongueVisualizer';
import { fetchZoneMaps, fetchZoneRegions, fetchRules, createRule, deleteRule } from './api';

function App() {
  const [scanType, setScanType] = useState('iris');
  const [zoneMaps, setZoneMaps] = useState([]);
  const [activeZoneMap, setActiveZoneMap] = useState(null);
  
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState(null);
  
  const [rules, setRules] = useState([]);
  
  const [form, setForm] = useState({
    metric: 'redness',
    operator: '>',
    value: '0.5',
    finding: '',
    description: '',
    severity: 'medium'
  });

  useEffect(() => {
    fetchZoneMaps().then(data => {
      setZoneMaps(data.data.items);
    });
  }, []);

  useEffect(() => {
    const map = zoneMaps.find(m => m.scan_type === scanType);
    setActiveZoneMap(map);
    if (map) {
      fetchZoneRegions(map.id).then(data => setRegions(data.data.items));
    } else {
      setRegions([]);
    }
    setSelectedRegion(null);
    loadRules();
  }, [scanType, zoneMaps]);

  const loadRules = () => {
    fetchRules(scanType).then(data => setRules(data.data.items));
  };

  const handleCreateRule = async (e) => {
    e.preventDefault();
    if (!selectedRegion) {
      alert("Please select a visual zone first!");
      return;
    }
    const condition = `${form.metric} ${form.operator} ${form.value}`;
    
    try {
      let regionId = selectedRegion.id;
      
      if (selectedRegion.isNew) {
        let mapId = activeZoneMap?.id;
        if (!mapId) {
          const mapRes = await import('./api').then(m => m.createZoneMap({ name: scanType + ' map', scan_type: scanType }));
          mapId = mapRes.data.id;
          setActiveZoneMap(mapRes.data);
        }
        const regRes = await import('./api').then(m => m.createZoneRegion({ zone_map_id: mapId, name: selectedRegion.name, coordinates: [] }));
        regionId = regRes.data.id;
        
        // Refresh regions array to avoid duplicates
        import('./api').then(m => m.fetchZoneRegions(mapId).then(data => setRegions(data.data.items)));
      }

      await createRule({
        zone_region_id: regionId,
        scan_type: scanType,
        condition,
        finding: form.finding,
        description: form.description,
        severity: form.severity
      });
      setForm({ ...form, finding: '', description: '' });
      loadRules();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteRule = async (id) => {
    await deleteRule(id);
    loadRules();
  };

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500 mb-2">
          A-EYE Rule Builder
        </h1>
        <p className="text-slate-400">Practitioner configuration for analytical thresholds.</p>
      </header>

      {/* Tabs */}
      <div className="flex justify-center gap-4 mb-8">
        {['iris', 'face', 'tongue'].map(type => (
          <button
            key={type}
            onClick={() => setScanType(type)}
            className={`px-6 py-2 rounded-full font-semibold transition-all ${
              scanType === type 
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' 
                : 'bg-white/5 text-slate-300 hover:bg-white/10'
            }`}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Col: Visualizer */}
        <div className="glass-panel p-6 flex flex-col items-center">
          <h2 className="text-xl font-semibold mb-6">Select Zone</h2>
          <div className="w-full flex-grow flex items-center justify-center min-h-[300px]">
            {scanType === 'iris' && <EyeVisualizer regions={regions} selectedRegion={selectedRegion} onRegionSelect={setSelectedRegion} ruleRegionIds={rules.map(r => r.zone_region_id)} />}
            {scanType === 'face' && <FaceVisualizer regions={regions} selectedRegion={selectedRegion} onRegionSelect={setSelectedRegion} ruleRegionIds={rules.map(r => r.zone_region_id)} />}
            {scanType === 'tongue' && <TongueVisualizer regions={regions} selectedRegion={selectedRegion} onRegionSelect={setSelectedRegion} ruleRegionIds={rules.map(r => r.zone_region_id)} />}
          </div>
          <div className="mt-4 text-center h-8">
            {selectedRegion ? (
              <span className="inline-block px-4 py-1 bg-blue-500/20 text-blue-300 border border-blue-500/30 rounded-full text-sm">
                Selected: <strong className="font-mono">{selectedRegion.name}</strong>
              </span>
            ) : (
              <span className="text-slate-500 text-sm">Click a region to select</span>
            )}
          </div>
        </div>

        {/* Right Col: Builder Form & Rules List */}
        <div className="space-y-8">
          <div className="glass-panel p-6">
            <h2 className="text-xl font-semibold mb-6">Define Rule</h2>
            <form onSubmit={handleCreateRule} className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Metric</label>
                  <select 
                    value={form.metric} 
                    onChange={e => setForm({...form, metric: e.target.value})}
                    className="glass-input w-full"
                  >
                    <option value="redness">Redness</option>
                    <option value="brightness">Brightness</option>
                    <option value="roughness">Roughness</option>
                    <option value="uniformity">Uniformity</option>
                    <option value="spots.has_spots">Spots Present</option>
                    <option value="cracks.density">Crack Density</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Operator</label>
                  <select 
                    value={form.operator} 
                    onChange={e => setForm({...form, operator: e.target.value})}
                    className="glass-input w-full"
                  >
                    <option value=">">&gt;</option>
                    <option value="<">&lt;</option>
                    <option value=">=">&gt;=</option>
                    <option value="<=">&lt;=</option>
                    <option value="==">==</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Value</label>
                  <input 
                    type="text" 
                    value={form.value} 
                    onChange={e => setForm({...form, value: e.target.value})}
                    className="glass-input w-full"
                    placeholder="0.5, true..."
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Finding Title</label>
                <input 
                  type="text" 
                  required
                  value={form.finding} 
                  onChange={e => setForm({...form, finding: e.target.value})}
                  className="glass-input w-full"
                  placeholder="e.g. Inflammation detected"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Recommendation / Description</label>
                <textarea 
                  required
                  value={form.description} 
                  onChange={e => setForm({...form, description: e.target.value})}
                  className="glass-input w-full h-20 resize-none"
                  placeholder="Practitioner notes..."
                />
              </div>

              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <label className="block text-xs text-slate-400 mb-1">Severity</label>
                  <select 
                    value={form.severity} 
                    onChange={e => setForm({...form, severity: e.target.value})}
                    className="glass-input w-full"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <button type="submit" className="btn-primary py-[0.6rem]">
                  Save Rule
                </button>
              </div>
            </form>
          </div>

          <div className="glass-panel p-6 h-64 flex flex-col">
            <h2 className="text-xl font-semibold mb-4 shrink-0">Existing Rules ({scanType})</h2>
            <div className="overflow-y-auto pr-2 space-y-3 flex-1 custom-scrollbar">
              {rules.map(rule => (
                <div key={rule.id} className={`p-3 border rounded-lg flex justify-between items-start group transition-colors ${
                  selectedRegion?.id === rule.zone_region_id 
                    ? 'bg-blue-500/10 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.2)]' 
                    : 'bg-white/5 border-white/10'
                }`}>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                        rule.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                        rule.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {rule.severity}
                      </span>
                      <span className="text-sm font-semibold">{rule.finding}</span>
                    </div>
                    <code className="text-xs text-blue-300 block mb-1">IF {rule.condition}</code>
                    <p className="text-xs text-slate-400">{rule.description}</p>
                  </div>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm('Are you sure you want to delete this rule?')) {
                        handleDeleteRule(rule.id);
                      }
                    }}
                    className="text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 px-2 py-1 rounded transition-colors text-xs font-semibold ml-2 shrink-0"
                    title="Delete Rule"
                  >
                    Delete
                  </button>
                </div>
              ))}
              {rules.length === 0 && (
                <p className="text-slate-500 text-sm italic text-center mt-8">No rules defined for this scan type.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
