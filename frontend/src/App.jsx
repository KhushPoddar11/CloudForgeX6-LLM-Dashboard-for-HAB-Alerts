import React, { useEffect, useState, useRef } from 'react';
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
  const [showChat, setShowChat] = useState(false);
  const chatRef = useRef(null);

  useEffect(() => {
    axios.get('/api/discovery/sites').then((res) => {
      setSites(res.data);
    });
  }, []);

  useEffect(() => {
    const siteInfo = sites.find((s) => s.site === selectedSite);
    if (siteInfo) {
      setSiteDateRange({ min: siteInfo.start_date, max: siteInfo.end_date });
      setStartDate(siteInfo.start_date);
      setEndDate(siteInfo.end_date);
    } else {
      setSiteDateRange({ min: '', max: '' });
      setStartDate('');
      setEndDate('');
    }
  }, [selectedSite, sites]);

  useEffect(() => {
    if (selectedSite && startDate && endDate) {
      fetchMeasurements();
      setChatHistory([]);
    }
  }, [selectedSite, startDate, endDate]);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [chatHistory, llmLoading]);

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
    const updatedHistory = [...chatHistory, { role: 'user', message: question }];
    setChatHistory(updatedHistory);
    setUserQuestion('');

    try {
      const res = await axios.post('/api/ask-llm', {
        site: selectedSite,
        start_date: startDate,
        end_date: endDate,
        user_question: question,
        chat_history: updatedHistory,
      });

      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          message: res.data.answer || "Here's what I found for you!",
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

  return (
    <div className="min-h-screen bg-gray-100 p-6 relative">
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
            setChatHistory([]);
          }}
        />
        <DatePicker
          label={`Start Date (min: ${siteDateRange.min})`}
          date={startDate}
          onChange={setStartDate}
          minDate={siteDateRange.min}
          maxDate={endDate || siteDateRange.max}
        />
        <DatePicker
          label={`End Date (max: ${siteDateRange.max})`}
          date={endDate}
          onChange={setEndDate}
          minDate={startDate || siteDateRange.min}
          maxDate={siteDateRange.max}
        />
      </div>

      <div className="flex gap-6 mt-4">
        <div className="flex-1">
          {siteData.length > 0 ? (
            <>
              <GeoMap siteData={siteData} />
              <TimeTrendsChart data={siteData} />
              <RiskPanel data={siteData} />
              <DownloadButtons data={siteData} />
            </>
          ) : (
            selectedSite && startDate && endDate && (
              <div className="mt-4 bg-yellow-100 border border-yellow-300 p-4 rounded text-sm text-yellow-700">
                No measurement data available for the selected site and date range.
              </div>
            )
          )}
              </div>
                    </div>

      <button
        onClick={() => setShowChat(true)}
        className="fixed bottom-6 right-6 bg-indigo-600 text-white px-4 py-2 rounded-full shadow-lg z-40"
      >
        Open Chat
      </button>

      {showChat && (
        <>
          <div
            className="fixed inset-0 bg-black bg-opacity-40 z-40"
            onClick={() => setShowChat(false)}
          />
          <div
            className="fixed bottom-6 right-6 w-96 max-w-full bg-white rounded-lg shadow-lg z-[9999] p-4 animate-slide-up"
          >
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-lg font-semibold">HAB Chat Assistant</h2>
              <button onClick={() => setShowChat(false)} className="text-sm text-gray-500 hover:text-red-500">✕</button>
            </div>
            <div
              ref={chatRef}
              className="flex flex-col space-y-2 mb-2 max-h-80 overflow-y-auto"
            >
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
                  🤖 Assistant is thinking...
                </div>
              )}
            </div>

            <textarea
              value={userQuestion}
              onChange={(e) => setUserQuestion(e.target.value)}
              placeholder="Ask something like: Is the site at risk today?"
              className="border rounded px-2 py-1 h-20 resize-none w-full"
            />
            <button
              className="mt-2 bg-indigo-600 text-white px-4 py-2 rounded w-full"
              onClick={askLLM}
              disabled={!userQuestion || llmLoading}
            >
              Send
            </button>
          </div>
        </>
        )}

      {/* Animation keyframe */}
      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .animate-slide-up {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
