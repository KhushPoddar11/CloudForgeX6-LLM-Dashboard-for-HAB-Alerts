import React from 'react';

export default function SiteSelector({ sites, selectedSite, onChange }) {
  return (
    <div className="flex flex-col">
      <label className="text-sm font-medium mb-1">Location:</label>
      <select
        value={selectedSite}
        onChange={(e) => onChange(e.target.value)}
        className="border rounded px-2 py-1"
      >
        <option value="">Select a site</option>
        {sites.map((site) => (
          <option key={site.site} value={site.site}>{site.site}</option>
        ))}
      </select>
    </div>
  );
}