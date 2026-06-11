import React from 'react';

const EyeVisualizer = ({ regions, selectedRegion, onRegionSelect, ruleRegionIds = [] }) => {
  // regions is an array of objects: { id, name, ... }
  // We expect names like ring_1_segment_1
  
  const renderSlices = () => {
    const paths = [];
    const slices = 12;
    const angleStep = 360 / slices;
    const cx = 150, cy = 150;
    
    // Ring radii
    const rings = [
      { id: 1, inner: 30, outer: 70 },
      { id: 2, inner: 70, outer: 110 },
      { id: 3, inner: 110, outer: 150 }
    ];

    const polarToCartesian = (centerX, centerY, radius, angleInDegrees) => {
      const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
      return {
        x: centerX + (radius * Math.cos(angleInRadians)),
        y: centerY + (radius * Math.sin(angleInRadians))
      };
    };

    rings.forEach(ring => {
      for (let i = 1; i <= slices; i++) {
        const startAngle = (i - 1) * angleStep;
        const endAngle = i * angleStep;
        
        const startOuter = polarToCartesian(cx, cy, ring.outer, startAngle);
        const endOuter = polarToCartesian(cx, cy, ring.outer, endAngle);
        const startInner = polarToCartesian(cx, cy, ring.inner, startAngle);
        const endInner = polarToCartesian(cx, cy, ring.inner, endAngle);
        
        const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
        
        const pathData = [
          "M", startOuter.x, startOuter.y, 
          "A", ring.outer, ring.outer, 0, largeArcFlag, 1, endOuter.x, endOuter.y,
          "L", endInner.x, endInner.y,
          "A", ring.inner, ring.inner, 0, largeArcFlag, 0, startInner.x, startInner.y,
          "Z"
        ].join(" ");
        
        const regionName = `ring_${ring.id}_segment_${i}`;
        const regionObj = regions?.find(r => r.name === regionName);
        const isSelected = selectedRegion && (selectedRegion.id === regionObj?.id || selectedRegion.name === regionName);
        const hasRule = regionObj && ruleRegionIds.includes(regionObj.id);

        let fillValue = "var(--color-glass-panel)";
        if (isSelected) {
          fillValue = "var(--color-accent)";
        } else if (hasRule) {
          fillValue = "rgba(139, 92, 246, 0.4)"; // Faint purple to indicate rule exists
        }

        paths.push(
          <path
            key={regionName}
            d={pathData}
            fill={fillValue}
            stroke="var(--color-glass-border)"
            strokeWidth="1"
            className="cursor-pointer hover:fill-blue-500/30 transition-colors"
            onClick={() => {
              onRegionSelect(regionObj || { id: `new_${regionName}`, name: regionName, isNew: true });
            }}
          >
            <title>{regionName}</title>
          </path>
        );
      }
    });

    return paths;
  };

  return (
    <svg width="300" height="300" viewBox="0 0 300 300" className="mx-auto block">
      <circle cx="150" cy="150" r="150" fill="#000" opacity="0.3" />
      <circle cx="150" cy="150" r="30" fill="#000" /> {/* Pupil */}
      {renderSlices()}
    </svg>
  );
};

export default EyeVisualizer;
