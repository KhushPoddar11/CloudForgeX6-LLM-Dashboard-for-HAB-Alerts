import React, { useEffect, useState } from 'react';
import axios from 'axios';
import DatePicker from './components/DatePicker';
import SiteSelector from './components/SiteSelector';
import GeoMap from './components/GeoMap';
import TimeTrendsChart from './components/TimeTrendsChart';
import RiskPanel from './components/RiskPanel';
import DownloadButtons from './components/DownloadButtons';

export default function App() {
  const [sites, setSites] = useState([]);
  const [selectedSite, setSelectedSite] = useState('');
  const [siteDateRange, setSiteDateRange] = useState({ min: '', max: '' });
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [siteData, setSiteData] = useState([]);
  const [llmLoading, setLlmLoading] = useState(false);
  const [userQuestion, setUserQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);

  useEffect(() => {
    axios.get('/api/discovery/sites').then((res) => {
      setSites(res.data);
    });
  }, []);

  useEffect(() => {
    const siteInfo = sites.find((s) => s.name === selectedSite);
    if (siteInfo) {
      setSiteDateRange({ min: siteInfo.min_date, max: siteInfo.max_date });
      setStartDate(siteInfo.min_date);
      setEndDate(siteInfo.max_date);
    } else {
      setSiteDateRange({ min: '', max: '' });
      setStartDate('');
      setEndDate('');
    }
  }, [selectedSite, sites]);

  useEffect(() => {
    if (selectedSite && startDate && endDate) {
      fetchMeasurements();
    }
  }, [selectedSite, startDate, endDate]);

  const fetchMeasurements = async () => {
    try {
      const res = await axios.post('/api/measurements', {
        site: selectedSite,
        start_date: startDate,
        end_date: endDate,
      });
      setSiteData(res.data);
    } catch (err) {
      console.error('Error fetching measurements:', err);
    }
  };

  const askLLM = async () => {
    const question = userQuestion.trim();
    if (!question) return;

    setLlmLoading(true);
    setChatHistory((prev) => [...prev, { role: 'user', message: question }]);
    setUserQuestion('');

    try {
      const res = await axios.post('/api/ask-llm', {
        site: selectedSite,
        start_date: startDate,
        end_date: endDate,
        user_question: question,
      });

      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          message:
            res.data.answer || 'I reviewed the data and here is what I found...',
        },
      ]);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        { role: 'assistant', message: 'Oops! Something went wrong. Please try again.' },
      ]);
    } finally {
      setLlmLoading(false);
    }
  };

  const selectedSiteMeta = sites.find((s) => s.site === selectedSite);
  const minDate = selectedSiteMeta?.start_date || '';
  const maxDate = selectedSiteMeta?.end_date || '';

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-2xl font-bold mb-4">HAB Risk Analysis Dashboard</h1>

      <div className="flex flex-wrap gap-4 mb-4">
        <SiteSelector
          sites={sites}
          selectedSite={selectedSite}
          onChange={(val) => {
            setSelectedSite(val);
            setStartDate('');
            setEndDate('');
            setSiteData([]);
          }}
        />
        <DatePicker
          label="Start Date"
          date={startDate}
          onChange={setStartDate}
          minDate={minDate}
          maxDate={endDate || maxDate}
        />
        <DatePicker
          label="End Date"
          date={endDate}
          onChange={setEndDate}
          minDate={startDate || minDate}
          maxDate={maxDate}
        />
      </div>

      <div className="flex gap-6 mt-4">
        <div className="flex-1">
          {siteData.length > 0 && (
            <>
              <GeoMap siteData={siteData} />
              <TimeTrendsChart data={siteData} />
              <RiskPanel data={siteData} />
              <DownloadButtons data={siteData} />
            </>
          )}
        </div>

        {siteData.length > 0 && (
          <div className="w-full max-w-sm flex flex-col border border-gray-300 rounded-lg p-4 bg-white shadow-sm h-fit">
            <h2 className="text-lg font-semibold mb-2">HAB Chat Assistant</h2>
            <div className="flex flex-col space-y-2 mb-2 max-h-[400px] overflow-y-auto">
              {chatHistory.map((chat, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded-lg text-sm ${
                    chat.role === 'user'
                      ? 'bg-blue-100 self-end text-right'
                      : 'bg-gray-200 self-start'
                  }`}
                >
                  {chat.message}
                </div>
              ))}
              {llmLoading && (
                <div className="text-sm italic text-gray-500 self-start">
                  Assistant is thinking...
                </div>
              )}
            </div>

            <textarea
              value={userQuestion}
              onChange={(e) => setUserQuestion(e.target.value)}
              placeholder="Ask something like: What is the risk today?"
              className="border rounded px-2 py-1 h-24 resize-none"
            />
            <button
              className="mt-2 bg-indigo-600 text-white px-4 py-2 rounded"
              onClick={askLLM}
              disabled={!userQuestion || llmLoading}
            >
              Send
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
