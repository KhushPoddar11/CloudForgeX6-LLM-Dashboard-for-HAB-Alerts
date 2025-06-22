import React from 'react';

export default function DownloadButtons({ data }) {
  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'hab_data.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadCSV = () => {
    if (!data || data.length === 0) return;
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];

    for (const row of data) {
      csvRows.push(headers.map(field => JSON.stringify(row[field] ?? '')).join(','));
    }

    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'hab_data.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex gap-4 mt-2">
      <button onClick={downloadJSON} className="bg-blue-600 text-white px-4 py-1 rounded">Download JSON</button>
      <button onClick={downloadCSV} className="bg-green-600 text-white px-4 py-1 rounded">Download CSV</button>
    </div>
  );
}
