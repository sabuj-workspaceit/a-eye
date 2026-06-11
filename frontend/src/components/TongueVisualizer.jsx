import React from 'react';

const TongueVisualizer = ({ regions, selectedRegion, onRegionSelect, ruleRegionIds = [] }) => {
  const getFill = (name) => {
    const regionObj = regions?.find(r => r.name === name);
    const isSelected = selectedRegion && (selectedRegion.id === regionObj?.id || selectedRegion.name === name);
    const hasRule = regionObj && ruleRegionIds.includes(regionObj.id);

    if (isSelected) {
      return "var(--color-accent)";
    } else if (hasRule) {
      return "rgba(139, 92, 246, 0.4)";
    }
    return "var(--color-glass-panel)";
  };

  const handleSelect = (name) => {
    const regionObj = regions?.find(r => r.name === name);
    onRegionSelect(regionObj || { id: `new_${name}`, name: name, isNew: true });
  };

  return (
    <svg width="200" height="300" viewBox="0 0 200 300" className="mx-auto block">
      {/* Tongue Outline Base */}
      <path d="M 50 50 Q 100 0 150 50 L 170 180 Q 180 280 100 280 Q 20 280 30 180 Z" fill="none" stroke="var(--color-glass-border)" strokeWidth="2" />
      
      {/* Rear */}
      <path 
        d="M 50 50 Q 100 0 150 50 L 155 100 L 45 100 Z" 
        fill={getFill('rear')} stroke="rgba(255,255,255,0.2)" 
        className="cursor-pointer hover:fill-blue-500/30 transition-colors"
        onClick={() => handleSelect('rear')}
      ><title>Rear</title></path>
      
      {/* Center */}
      <rect 
        x="75" y="100" width="50" height="100" 
        fill={getFill('center')} stroke="rgba(255,255,255,0.2)" 
        className="cursor-pointer hover:fill-blue-500/30 transition-colors"
        onClick={() => handleSelect('center')}
      ><title>Center</title></rect>

      {/* Left */}
      <path 
        d="M 45 100 L 75 100 L 75 200 L 32 200 Z" 
        fill={getFill('left')} stroke="rgba(255,255,255,0.2)" 
        className="cursor-pointer hover:fill-blue-500/30 transition-colors"
        onClick={() => handleSelect('left')}
      ><title>Left</title></path>
      
      {/* Right */}
      <path 
        d="M 125 100 L 155 100 L 168 200 L 125 200 Z" 
        fill={getFill('right')} stroke="rgba(255,255,255,0.2)" 
        className="cursor-pointer hover:fill-blue-500/30 transition-colors"
        onClick={() => handleSelect('right')}
      ><title>Right</title></path>

      {/* Tip */}
      <path 
        d="M 32 200 L 168 200 Q 180 280 100 280 Q 20 280 32 200 Z" 
        fill={getFill('tip')} stroke="rgba(255,255,255,0.2)" 
        className="cursor-pointer hover:fill-blue-500/30 transition-colors"
        onClick={() => handleSelect('tip')}
      ><title>Tip</title></path>
    </svg>
  );
};

export default TongueVisualizer;
