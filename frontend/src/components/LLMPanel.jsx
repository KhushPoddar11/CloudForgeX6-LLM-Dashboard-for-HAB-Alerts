import React from 'react';

export default function LLMPanel({ answer, loading }) {
  if (loading) {
    return <div className="mt-4 p-4 border rounded text-sm text-blue-500">Generating response...</div>;
  }

  if (!answer) return null;

  return (
    <div className="mt-4 p-4 border rounded text-sm whitespace-pre-wrap">
      <h2 className="text-lg font-semibold mb-2">LLM Analysis</h2>
      {answer}
    </div>
  );
}