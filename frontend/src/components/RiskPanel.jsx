import React, { useState } from 'react';

export default function RiskPanel({ data }) {
  const [showAllRows, setShowAllRows] = useState(false);
  const [sortColumn, setSortColumn] = useState('timestamp');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterRisk, setFilterRisk] = useState('all');
  
  if (!data || data.length === 0) return null;


  let processedData = [...data];
  

  if (filterRisk !== 'all') {
    processedData = processedData.filter(row => 
      row.risk_level?.toLowerCase() === filterRisk.toLowerCase()
    );
  }
  

  processedData.sort((a, b) => {
    let aVal = a[sortColumn];
    let bVal = b[sortColumn];
    

    if (sortColumn === 'timestamp') {
      aVal = new Date(aVal);
      bVal = new Date(bVal);
    } else if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }
    
    if (sortDirection === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  const displayedData = showAllRows ? processedData : processedData.slice(0, 25);
  const totalRows = processedData.length;

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };

  const getRiskBadge = (riskLevel) => {
    const risk = riskLevel?.toLowerCase() || 'unknown';
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800',
      critical: 'bg-red-200 text-red-900',
      unknown: 'bg-gray-100 text-gray-600'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[risk]}`}>
        {risk.toUpperCase()}
      </span>
    );
  };

  const SortButton = ({ column, children }) => (
    <button
      onClick={() => handleSort(column)}
      className="flex items-center space-x-1 hover:bg-gray-100 px-2 py-1 rounded"
    >
      <span>{children}</span>
      {sortColumn === column && (
        <span className={`text-xs ${sortDirection === 'asc' ? 'rotate-180' : ''}`}>
          ▼
        </span>
      )}
    </button>
  );


  const riskCounts = data.reduce((acc, row) => {
    const risk = row.risk_level?.toLowerCase() || 'unknown';
    acc[risk] = (acc[risk] || 0) + 1;
    return acc;
  }, {});

  const avgChlorophyll = data.reduce((sum, row) => sum + (row.chlorophyll_a || 0), 0) / data.length;
  const avgBloomProb = data.reduce((sum, row) => sum + (row.bloom_probability || 0), 0) / data.length;
  const bloomEvents = data.filter(row => row.bloom_label === 1).length;

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">📊 Enhanced Measurement Analysis</h2>
        

        <div className="flex space-x-4 text-sm">
          <div className="text-center p-2 bg-blue-50 rounded">
            <div className="font-bold text-blue-600">{avgChlorophyll.toFixed(2)}</div>
            <div className="text-gray-600">Avg Chl-a</div>
          </div>
          <div className="text-center p-2 bg-yellow-50 rounded">
            <div className="font-bold text-yellow-600">{(avgBloomProb * 100).toFixed(1)}%</div>
            <div className="text-gray-600">Bloom Risk</div>
          </div>
          <div className="text-center p-2 bg-red-50 rounded">
            <div className="font-bold text-red-600">{bloomEvents}</div>
            <div className="text-gray-600">Bloom Events</div>
          </div>
        </div>
      </div>


      <div className="mb-4 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium mb-2">🎯 Risk Level Distribution</h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(riskCounts).map(([risk, count]) => (
            <div key={risk} className="flex items-center space-x-2">
              {getRiskBadge(risk)}
              <span className="text-sm text-gray-600">({count})</span>
            </div>
          ))}
        </div>
      </div>


      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center space-x-4">
          <div>
            <label className="text-sm font-medium mr-2">Filter by Risk:</label>
            <select 
              value={filterRisk} 
              onChange={(e) => setFilterRisk(e.target.value)}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value="all">All Levels</option>
              <option value="low">Low Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="high">High Risk</option>
              <option value="critical">Critical Risk</option>
            </select>
          </div>
          
          <div className="text-sm text-gray-600">
            Showing {displayedData.length} of {totalRows} records
            {filterRisk !== 'all' && ` (filtered by ${filterRisk} risk)`}
          </div>
        </div>
      </div>


      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-100 text-left">
              <th className="px-3 py-2 border-b">
                <SortButton column="timestamp">📅 Timestamp</SortButton>
              </th>
              <th className="px-3 py-2 border-b">
                <SortButton column="latitude">📍 Lat</SortButton>
              </th>
              <th className="px-3 py-2 border-b">
                <SortButton column="longitude">📍 Lon</SortButton>
              </th>
              <th className="px-3 py-2 border-b">
                <SortButton column="chlorophyll_a">🌱 Chl-a (µg/L)</SortButton>
              </th>
              <th className="px-3 py-2 border-b">
                <SortButton column="sea_surface_temperature">🌡️ SST (°C)</SortButton>
              </th>
              <th className="px-3 py-2 border-b">
                <SortButton column="turbidity">🌫️ Turbidity</SortButton>
              </th>
              {/* Enhanced columns */}
              {displayedData[0]?.salinity !== undefined && (
                <th className="px-3 py-2 border-b">
                  <SortButton column="salinity">🧂 Salinity</SortButton>
                </th>
              )}
              {displayedData[0]?.wind_speed !== undefined && (
                <th className="px-3 py-2 border-b">
                  <SortButton column="wind_speed">💨 Wind (m/s)</SortButton>
                </th>
              )}
              {displayedData[0]?.wave_height !== undefined && (
                <th className="px-3 py-2 border-b">
                  <SortButton column="wave_height">🌊 Waves (m)</SortButton>
                </th>
              )}
              <th className="px-3 py-2 border-b">
                <SortButton column="bloom_probability">⚠️ Bloom Risk</SortButton>
              </th>
              <th className="px-3 py-2 border-b">
                <SortButton column="risk_level">🎯 Risk Level</SortButton>
              </th>
              {displayedData[0]?.dataset_source && (
                <th className="px-3 py-2 border-b">
                  <SortButton column="dataset_source">📊 Data Source</SortButton>
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {displayedData.map((row, idx) => (
              <tr
                key={idx}
                className={`${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-blue-50 transition-colors`}
              >
                <td className="px-3 py-2 border-b whitespace-nowrap font-mono text-xs">
                  {new Date(row.timestamp).toLocaleString()}
                </td>
                <td className="px-3 py-2 border-b">{row.latitude?.toFixed(4)}</td>
                <td className="px-3 py-2 border-b">{row.longitude?.toFixed(4)}</td>
                <td className="px-3 py-2 border-b">
                  <span className={`font-medium ${
                    row.chlorophyll_a > 10 ? 'text-red-600' : 
                    row.chlorophyll_a > 5 ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    {row.chlorophyll_a?.toFixed(3)}
                  </span>
                </td>
                <td className="px-3 py-2 border-b">{row.sea_surface_temperature?.toFixed(1)}</td>
                <td className="px-3 py-2 border-b">{row.turbidity?.toFixed(2)}</td>
                

                {row.salinity !== undefined && (
                  <td className="px-3 py-2 border-b">{row.salinity?.toFixed(1)}</td>
                )}
                {row.wind_speed !== undefined && (
                  <td className="px-3 py-2 border-b">
                    <span className={`${
                      row.wind_speed > 10 ? 'text-blue-600 font-medium' : ''
                    }`}>
                      {row.wind_speed?.toFixed(1)}
                    </span>
                  </td>
                )}
                {row.wave_height !== undefined && (
                  <td className="px-3 py-2 border-b">
                    <span className={`${
                      row.wave_height > 2 ? 'text-blue-600 font-medium' : ''
                    }`}>
                      {row.wave_height?.toFixed(1)}
                    </span>
                  </td>
                )}
                
                <td className="px-3 py-2 border-b">
                  <div className="flex items-center">
                    <div 
                      className="w-16 h-2 bg-gray-200 rounded-full mr-2"
                      title={`${(row.bloom_probability * 100).toFixed(1)}% probability`}
                    >
                      <div 
                        className={`h-full rounded-full ${
                          row.bloom_probability > 0.8 ? 'bg-red-500' :
                          row.bloom_probability > 0.6 ? 'bg-yellow-500' :
                          row.bloom_probability > 0.3 ? 'bg-blue-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${row.bloom_probability * 100}%` }}
                      />
                    </div>
                    <span className="text-xs">{(row.bloom_probability * 100).toFixed(1)}%</span>
                  </div>
                </td>
                
                <td className="px-3 py-2 border-b">
                  {getRiskBadge(row.risk_level)}
                </td>
                
                {row.dataset_source && (
                  <td className="px-3 py-2 border-b">
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded truncate" title={row.dataset_source}>
                      {row.dataset_source?.split('-')[0] || 'Unknown'}
                    </span>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>


      {totalRows > 25 && (
        <div className="mt-4 flex justify-between items-center">
          <button
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            onClick={() => setShowAllRows(!showAllRows)}
          >
            {showAllRows ? 
              `Show Less (displaying all ${totalRows} records)` : 
              `Show All Data (${totalRows} records)`
            }
          </button>
          
          <div className="text-sm text-gray-500">
            {filterRisk !== 'all' && (
              <button
                onClick={() => setFilterRisk('all')}
                className="text-blue-600 hover:text-blue-800 ml-4"
              >
                Clear Filter
              </button>
            )}
          </div>
        </div>
      )}


      <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm">
        <div className="flex items-start space-x-2">
          <span className="text-blue-600">💡</span>
          <div>
            <strong className="text-blue-800">Enhanced Dataset Features:</strong>
            <ul className="mt-1 text-blue-700 space-y-1">
              <li>• Wind speed and wave height data for environmental context</li>
              <li>• Multiple data sources including satellite and synthetic data</li>
              <li>• Enhanced risk categorization and bloom probability modeling</li>
              <li>• Regional classification for geographic analysis</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}