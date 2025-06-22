import React, { useState } from 'react';

export default function RiskPanel({ data }) {
  const [showAllRows, setShowAllRows] = useState(false);
  const displayedData = showAllRows ? data : data.slice(0, 10);
  const totalRows = data.length;

  return (
    <div className="mt-6 bg-white p-6 rounded shadow">
      <h2 className="text-lg font-semibold mb-4">Measurement Table</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-200 text-left">
              <th className="px-4 py-2">Timestamp</th>
              <th className="px-4 py-2">Latitude</th>
              <th className="px-4 py-2">Longitude</th>
              <th className="px-4 py-2">Chlorophyll-a</th>
              <th className="px-4 py-2">SST (°C)</th>
              <th className="px-4 py-2">Turbidity</th>
              <th className="px-4 py-2">Bloom</th>
            </tr>
          </thead>
          <tbody>
            {displayedData.map((row, idx) => (
              <tr
                key={idx}
                className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
              >
                <td className="px-4 py-2 whitespace-nowrap">{row.timestamp}</td>
                <td className="px-4 py-2">{row.latitude.toFixed(6)}</td>
                <td className="px-4 py-2">{row.longitude.toFixed(6)}</td>
                <td className="px-4 py-2">{row.chlorophyll_a.toFixed(4)}</td>
                <td className="px-4 py-2">{row.sea_surface_temperature.toFixed(4)}</td>
                <td className="px-4 py-2">{row.turbidity.toFixed(4)}</td>
                <td className="px-4 py-2">{row.bloom_label === 1 ? 'Yes' : 'No'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalRows > 10 && (
        <button
          className="mt-3 text-indigo-600 hover:underline text-sm"
          onClick={() => setShowAllRows(!showAllRows)}
        >
          {showAllRows ? 'Show Less' : `Show All Data (${totalRows} rows)`}
        </button>
      )}
    </div>
  );
}
