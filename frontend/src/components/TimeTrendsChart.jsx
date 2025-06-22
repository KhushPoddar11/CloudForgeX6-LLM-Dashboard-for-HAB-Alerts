import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function TimeTrendsChart({ data }) {
  if (!data || data.length === 0) return null;

  return (
    <div className="w-full h-96 border rounded p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="timestamp" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="chlorophyll_a" stroke="#10b981" name="Chl-a (µg/L)" />
          <Line type="monotone" dataKey="sea_surface_temperature" stroke="#3b82f6" name="SST (°C)" />
          <Line type="monotone" dataKey="bloom_probability" stroke="#ef4444" name="Bloom Prob." />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}