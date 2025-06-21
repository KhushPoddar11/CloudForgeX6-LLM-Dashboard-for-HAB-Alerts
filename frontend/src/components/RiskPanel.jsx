import React from 'react';

export default function RiskPanel({ data }) {
  if (!data || data.length === 0) return null;

  return (
    <div className="overflow-x-auto border rounded p-4">
      <h2 className="text-lg font-semibold mb-2">Risk Data Table</h2>
      <table className="min-w-full table-auto border">
        <thead>
          <tr className="bg-gray-100">
            <th className="px-3 py-2 border">Timestamp</th>
            <th className="px-3 py-2 border">Latitude</th>
            <th className="px-3 py-2 border">Longitude</th>
            <th className="px-3 py-2 border">Chl-a (µg/L)</th>
            <th className="px-3 py-2 border">SST (°C)</th>
            <th className="px-3 py-2 border">Turbidity (NTU)</th>
            <th className="px-3 py-2 border">Bloom Label</th>
            <th className="px-3 py-2 border">Bloom Probability</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={index} className="text-sm">
              <td className="px-3 py-1 border">{row.timestamp}</td>
              <td className="px-3 py-1 border">{row.latitude}</td>
              <td className="px-3 py-1 border">{row.longitude}</td>
              <td className="px-3 py-1 border">{row.chlorophyll_a}</td>
              <td className="px-3 py-1 border">{row.sea_surface_temperature}</td>
              <td className="px-3 py-1 border">{row.turbidity}</td>
              <td className="px-3 py-1 border">{row.bloom_label}</td>
              <td className="px-3 py-1 border">{row.bloom_probability}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
