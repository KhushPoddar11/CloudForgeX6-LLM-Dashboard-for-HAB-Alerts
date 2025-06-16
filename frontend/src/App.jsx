import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [sites, setSites] = useState([]);
  const [site, setSite] = useState("");
  const [siteMinDate, setSiteMinDate] = useState("");
  const [siteMaxDate, setSiteMaxDate] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [llmLoading, setLlmLoading] = useState(false);
  const [measurements, setMeasurements] = useState([]);
  const [showTable, setShowTable] = useState(false);

  useEffect(() => {
    axios.get("/api/discovery/sites")
      .then(res => setSites(res.data))
      .catch(err => console.error("Error fetching sites", err));
  }, []);

  const handleSubmit = async () => {
    setLoading(true);
    setAnswer("");
    setShowTable(false);
    setLlmLoading(false);

    try {
      // First fetch measurements
      const measurementRes = await axios.post("/api/measurements", {
        site,
        start_date: startDate,
        end_date: endDate
      });
      setMeasurements(measurementRes.data);
      setShowTable(true);

      // Then call LLM
      setLlmLoading(true);
      const payload = {
        site,
        start_date: startDate,
        end_date: endDate,
        user_question: question
      };
      const res = await axios.post("/api/ask-llm", payload);
      setAnswer(res.data.answer);
      setLlmLoading(false);
    } catch (err) {
      console.error(err);
      setAnswer("Error: " + err.response?.data?.error);
      setLlmLoading(false);
    }

    setLoading(false);
  };

  const handleSiteChange = (e) => {
    const selectedValue = e.target.value;
    if (!selectedValue) {
      setSite("");
      setStartDate("");
      setEndDate("");
      setSiteMinDate("");
      setSiteMaxDate("");
      setMeasurements([]);
      setShowTable(false);
      return;
    }
    const selected = sites.find(s => s.site === selectedValue);
    setSite(selected.site);
    setSiteMinDate(selected.start_date);
    setSiteMaxDate(selected.end_date);
    setStartDate(selected.start_date);
    setEndDate(selected.end_date);
  };

  const handleStartDateChange = (e) => {
    const newStart = e.target.value;
    setStartDate(newStart);
    if (newStart > endDate) {
      setEndDate(newStart);
    }
  };

  const handleEndDateChange = (e) => {
    const newEnd = e.target.value;
    setEndDate(newEnd);
    if (newEnd < startDate) {
      setStartDate(newEnd);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-8">
      <div className="bg-white p-8 rounded shadow-lg w-full max-w-[90%]">
        <h1 className="text-2xl font-bold mb-6">HAB Risk Dashboard</h1>

        <div className="mb-4">
          <label className="block font-semibold">Site</label>
          <select className="w-full p-2 border rounded" value={site} onChange={handleSiteChange}>
            <option value="">Select a site</option>
            {sites.map(s => (
              <option key={s.site} value={s.site}>{s.site}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <label className="block font-semibold">Start Date</label>
            <input
              type="date"
              className="w-full p-2 border rounded"
              value={startDate}
              min={siteMinDate}
              max={endDate || siteMaxDate}
              onChange={handleStartDateChange}
            />
          </div>

          <div className="flex-1">
            <label className="block font-semibold">End Date</label>
            <input
              type="date"
              className="w-full p-2 border rounded"
              value={endDate}
              min={startDate || siteMinDate}
              max={siteMaxDate}
              onChange={handleEndDateChange}
            />
          </div>
        </div>

        <div className="mb-4">
          <label className="block font-semibold">User Question</label>
          <input
            type="text"
            className="w-full p-2 border rounded"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Is the site at risk today?"
          />
        </div>

        <button
          className="w-full bg-blue-500 text-white p-3 rounded font-semibold disabled:opacity-50"
          onClick={handleSubmit}
          disabled={!site || !question || loading}
        >
          {loading ? "Processing..." : "Ask LLM"}
        </button>

        {showTable && (
          <div className="mt-6 overflow-x-auto">
            <h2 className="font-semibold mb-2">Measurement Data:</h2>
            <table className="table-auto border-collapse border border-gray-300 w-full text-sm">
              <thead>
                <tr>
                  <th className="border px-2 py-1">Timestamp</th>
                  <th className="border px-2 py-1">Latitude</th>
                  <th className="border px-2 py-1">Longitude</th>
                  <th className="border px-2 py-1">Chl-a (µg/L)</th>
                  <th className="border px-2 py-1">SST (°C)</th>
                  <th className="border px-2 py-1">Turbidity (NTU)</th>
                  <th className="border px-2 py-1">Bloom Label</th>
                  <th className="border px-2 py-1">Bloom Probability</th>
                </tr>
              </thead>
              <tbody>
                {measurements.length === 0 ? (
                  <tr><td colSpan="8" className="text-center py-2">No data</td></tr>
                ) : (
                  measurements.map((m, index) => (
                    <tr key={index}>
                      <td className="border px-2 py-1">{m.timestamp}</td>
                      <td className="border px-2 py-1">{m.latitude}</td>
                      <td className="border px-2 py-1">{m.longitude}</td>
                      <td className="border px-2 py-1">{m.chlorophyll_a}</td>
                      <td className="border px-2 py-1">{m.sea_surface_temperature}</td>
                      <td className="border px-2 py-1">{m.turbidity}</td>
                      <td className="border px-2 py-1">{m.bloom_label}</td>
                      <td className="border px-2 py-1">{m.bloom_probability}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {llmLoading && (
          <div className="mt-6 bg-yellow-100 p-4 rounded text-center font-semibold">
            Generating LLM response...
          </div>
        )}

        {answer && !llmLoading && (
          <div className="mt-6 bg-gray-200 p-4 rounded">
            <h2 className="font-semibold mb-2">LLM Response:</h2>
            <pre className="whitespace-pre-wrap">{answer}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
