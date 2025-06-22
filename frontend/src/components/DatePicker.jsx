import React from 'react';

export default function DatePicker({ label, date, onChange, minDate, maxDate }) {
  return (
    <div className="flex flex-col">
      <label className="text-sm font-medium mb-1">{label}</label>
      <input
        type="date"
        value={date}
        onChange={(e) => onChange(e.target.value)}
        className="border rounded px-2 py-1"
        min={minDate}
        max={maxDate}
      />
    </div>
  );
}
