import React, { useState } from 'react';

export default function SiteSelector({ sites, selectedSite, onChange }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRegion, setFilterRegion] = useState('all');
  const [sortBy, setSortBy] = useState('name');


  const regions = [...new Set(sites.map(site => site.region).filter(Boolean))].sort();


  let filteredSites = sites.filter(site => {
    const matchesSearch = site.site.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         site.region?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRegion = filterRegion === 'all' || site.region === filterRegion;
    return matchesSearch && matchesRegion;
  });


  filteredSites.sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.site.localeCompare(b.site);
      case 'region':
        return (a.region || '').localeCompare(b.region || '');
      case 'records':
        return (b.total_records || 0) - (a.total_records || 0);
      case 'risk':
        const riskOrder = { critical: 4, high: 3, medium: 2, low: 1, unknown: 0 };
        return (riskOrder[b.dominant_risk_level] || 0) - (riskOrder[a.dominant_risk_level] || 0);
      case 'chlorophyll':
        return (b.avg_chlorophyll || 0) - (a.avg_chlorophyll || 0);
      default:
        return 0;
    }
  });

  const getRiskColor = (riskLevel) => {
    const colors = {
      low: 'text-green-600',
      medium: 'text-yellow-600', 
      high: 'text-red-600',
      critical: 'text-red-800',
      unknown: 'text-gray-500'
    };
    return colors[riskLevel?.toLowerCase()] || colors.unknown;
  };

  const getRegionIcon = (region) => {
    if (!region) return '📍';
    if (region.toLowerCase().includes('ireland')) return '🇮🇪';
    if (region.toLowerCase().includes('celtic')) return '🌊';
    if (region.toLowerCase().includes('sea')) return '🌊';
    return '📍';
  };

  return (
    <div className="flex flex-col space-y-3">
      <label className="text-sm font-medium">🏖️ Monitoring Location:</label>
      

      <div className="flex space-x-2">
        <input
          type="text"
          placeholder="Search sites..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 border rounded px-3 py-1 text-sm"
        />
        
        <select
          value={filterRegion}
          onChange={(e) => setFilterRegion(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value="all">All Regions</option>
          {regions.map(region => (
            <option key={region} value={region}>
              {region}
            </option>
          ))}
        </select>
        
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value="name">Sort by Name</option>
          <option value="region">Sort by Region</option>
          <option value="records">Sort by Data Volume</option>
          <option value="risk">Sort by Risk Level</option>
          <option value="chlorophyll">Sort by Chl-a</option>
        </select>
      </div>


      <select
        value={selectedSite}
        onChange={(e) => onChange(e.target.value)}
        className="border rounded px-3 py-2 text-sm"
        size={Math.min(filteredSites.length + 1, 8)}
      >
        <option value="">
          {filteredSites.length === 0 ? 'No sites found' : 'Select a monitoring site...'}
        </option>
        {filteredSites.map((site) => (
          <option key={site.site} value={site.site}>
            {getRegionIcon(site.region)} {site.site} 
            {site.region && ` (${site.region})`}
            {site.total_records && ` - ${site.total_records.toLocaleString()} records`}
          </option>
        ))}
      </select>


      {selectedSite && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
          {(() => {
            const siteInfo = sites.find(s => s.site === selectedSite);
            if (!siteInfo) return null;
            
            return (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-blue-900 flex items-center">
                    {getRegionIcon(siteInfo.region)}
                    <span className="ml-2">{siteInfo.site}</span>
                  </h3>
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                    siteInfo.dominant_risk_level === 'high' || siteInfo.dominant_risk_level === 'critical' 
                      ? 'bg-red-100 text-red-700' :
                    siteInfo.dominant_risk_level === 'medium' 
                      ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                  }`}>
                    {siteInfo.dominant_risk_level?.toUpperCase() || 'UNKNOWN'} RISK
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">📊 Total Records:</span>
                      <span className="font-medium text-blue-700">
                        {siteInfo.total_records?.toLocaleString() || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">🌱 Avg Chl-a:</span>
                      <span className="font-medium text-green-700">
                        {siteInfo.avg_chlorophyll?.toFixed(2) || 'N/A'} µg/L
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">⚠️ Bloom Risk:</span>
                      <span className="font-medium text-yellow-700">
                        {siteInfo.avg_bloom_probability 
                          ? `${(siteInfo.avg_bloom_probability * 100).toFixed(1)}%`
                          : 'N/A'
                        }
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">🗺️ Region:</span>
                      <span className="font-medium text-indigo-700">
                        {siteInfo.region || 'Unknown'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">📍 Location:</span>
                      <span className="font-medium text-gray-700 font-mono text-xs">
                        {siteInfo.center_lat?.toFixed(2)}, {siteInfo.center_lon?.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">📡 Data Source:</span>
                      <span className="font-medium text-purple-700 text-xs truncate" title={siteInfo.primary_data_source}>
                        {siteInfo.primary_data_source?.split('-')[0] || 'Mixed'}
                      </span>
                    </div>
                  </div>
                </div>
                

                <div className="mt-3 pt-3 border-t border-blue-200">
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span>📅 Data Range:</span>
                    <span className="font-mono">
                      {siteInfo.start_date} → {siteInfo.end_date}
                    </span>
                  </div>
                  <div className="mt-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full"
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      )}


      {filteredSites.length > 0 && (
        <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
          📈 Showing {filteredSites.length} of {sites.length} sites
          {searchTerm && ` matching "${searchTerm}"`}
          {filterRegion !== 'all' && ` in ${filterRegion}`}
          • Total: {sites.reduce((sum, site) => sum + (site.total_records || 0), 0).toLocaleString()} records
        </div>
      )}
    </div>
  );
}