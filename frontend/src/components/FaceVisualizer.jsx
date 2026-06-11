import React from 'react';

const FaceVisualizer = ({ regions, selectedRegion, onRegionSelect, ruleRegionIds = [] }) => {
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
    <svg width="240" height="300" viewBox="0 0 240 300" className="mx-auto block">
      {/* Face Outline Base */}
      <ellipse cx="120" cy="150" rx="100" ry="130" fill="none" stroke="var(--color-glass-border)" strokeWidth="2" />
      
      {/* Forehead */}
      <path 
        d="M 40 80 Q 120 10 200 80 L 170 110 Q 120 80 70 110 Z" 
        fill={getFill('forehead')} stroke="rgba(255,255,255,0.2)" 
        className="cursor-pointer hover:fill-blue-500/30 transition-colors"
        onClick={() => handleSelect('forehead')}
      ><title>Forehead</title></path>
      
      {/* Nose */}
      <path 
        d="M 110 120 L 130 120 L 140 190 L 100 190 Z" 
        fill={getFill('nose')} stroke="rgba(255,255,255,0.2)" 
        className="cursor-pointer hover:fill-blue-500/30 transition-colors"
        onClick={() => handleSelect('nose')}
      ><title>Nose</title></path>

      {/* Left Cheek */}
      <path 
        d="M 30 130 Q 70 120 90 150 Q 80 200 50 200 Q 20 170 30 130 Z" 
        fill={getFill('left_cheek')} stroke="rgba(255,255,255,0.2)" 
        className="cursor-pointer hover:fill-blue-500/30 transition-colors"
        onClick={() => handleSelect('left_cheek')}
      ><title>Left Cheek</title></path>
      
      {/* Right Cheek */}
      <path 
        d="M 210 130 Q 170 120 150 150 Q 160 200 190 200 Q 220 170 210 130 Z" 
        fill={getFill('right_cheek')} stroke="rgba(255,255,255,0.2)" 
        className="cursor-pointer hover:fill-blue-500/30 transition-colors"
        onClick={() => handleSelect('right_cheek')}
      ><title>Right Cheek</title></path>

      {/* Chin */}
      <path 
        d="M 70 230 Q 120 280 170 230 Q 120 210 70 230 Z" 
        fill={getFill('chin')} stroke="rgba(255,255,255,0.2)" 
        className="cursor-pointer hover:fill-blue-500/30 transition-colors"
        onClick={() => handleSelect('chin')}
      ><title>Chin</title></path>
    </svg>
  );
};

export default FaceVisualizer;
