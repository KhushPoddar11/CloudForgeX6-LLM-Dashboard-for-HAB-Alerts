// import React, { useEffect, useState, useRef } from 'react';
// import axios from 'axios';
// import DatePicker from './components/DatePicker';
// import SiteSelector from './components/SiteSelector';
// import GeoMap from './components/GeoMap';
// import TimeTrendsChart from './components/TimeTrendsChart';
// import RiskPanel from './components/RiskPanel';
// import DownloadButtons from './components/DownloadButtons';

// export default function App() {
//   const [sites, setSites] = useState([]);
//   const [selectedSite, setSelectedSite] = useState('');
//   const [siteDateRange, setSiteDateRange] = useState({ min: '', max: '' });
//   const [startDate, setStartDate] = useState('');
//   const [endDate, setEndDate] = useState('');
//   const [siteData, setSiteData] = useState([]);
//   const [llmLoading, setLlmLoading] = useState(false);
//   const [userQuestion, setUserQuestion] = useState('');
//   const [chatHistory, setChatHistory] = useState([]);
//   const [showChat, setShowChat] = useState(false);
//   const chatRef = useRef(null);

//   useEffect(() => {
//     axios.get('/api/discovery/sites').then((res) => {
//       setSites(res.data);
//     });
//   }, []);

//   useEffect(() => {
//     const siteInfo = sites.find((s) => s.site === selectedSite);
//     if (siteInfo) {
//       setSiteDateRange({ min: siteInfo.start_date, max: siteInfo.end_date });
//       setStartDate(siteInfo.start_date);
//       setEndDate(siteInfo.end_date);
//     } else {
//       setSiteDateRange({ min: '', max: '' });
//       setStartDate('');
//       setEndDate('');
//     }
//   }, [selectedSite, sites]);

//   useEffect(() => {
//     if (selectedSite && startDate && endDate) {
//       fetchMeasurements();
//       setChatHistory([]);
//     }
//   }, [selectedSite, startDate, endDate]);

//   useEffect(() => {
//     if (chatRef.current) {
//       chatRef.current.scrollTop = chatRef.current.scrollHeight;
//     }
//   }, [chatHistory, llmLoading]);

//   const fetchMeasurements = async () => {
//     try {
//       const res = await axios.post('/api/measurements', {
//         site: selectedSite,
//         start_date: startDate,
//         end_date: endDate,
//       });
//       setSiteData(res.data);
//     } catch (err) {
//       console.error('Error fetching measurements:', err);
//     }
//   };

//   const askLLM = async () => {
//     const question = userQuestion.trim();
//     if (!question) return;

//     setLlmLoading(true);
//     const updatedHistory = [...chatHistory, { role: 'user', message: question }];
//     setChatHistory(updatedHistory);
//     setUserQuestion('');

//     try {
//       const res = await axios.post('/api/ask-llm', {
//         site: selectedSite,
//         start_date: startDate,
//         end_date: endDate,
//         user_question: question,
//         chat_history: updatedHistory,
//       });

//       setChatHistory((prev) => [
//         ...prev,
//         {
//           role: 'assistant',
//           message: res.data.answer || "Here's what I found for you!",
//         },
//       ]);
//     } catch (err) {
//       setChatHistory((prev) => [
//         ...prev,
//         { role: 'assistant', message: 'Oops! Something went wrong. Please try again.' },
//       ]);
//     } finally {
//       setLlmLoading(false);
//     }
//   };

//   return (
//     <div className="min-h-screen bg-gray-100 p-6 relative">
//       <h1 className="text-2xl font-bold mb-4">HAB Risk Analysis Dashboard</h1>

//       <div className="flex flex-wrap gap-4 mb-4">
//         <SiteSelector
//           sites={sites}
//           selectedSite={selectedSite}
//           onChange={(val) => {
//             setSelectedSite(val);
//             setStartDate('');
//             setEndDate('');
//             setSiteData([]);
//             setChatHistory([]);
//           }}
//         />
//         <DatePicker
//           label={`Start Date (min: ${siteDateRange.min})`}
//           date={startDate}
//           onChange={setStartDate}
//           minDate={siteDateRange.min}
//           maxDate={endDate || siteDateRange.max}
//         />
//         <DatePicker
//           label={`End Date (max: ${siteDateRange.max})`}
//           date={endDate}
//           onChange={setEndDate}
//           minDate={startDate || siteDateRange.min}
//           maxDate={siteDateRange.max}
//         />
//       </div>

//       <div className="flex gap-6 mt-4">
//         <div className="flex-1">
//           {siteData.length > 0 ? (
//             <>
//               <GeoMap siteData={siteData} />
//               <TimeTrendsChart data={siteData} />
//               <RiskPanel data={siteData} />
//               <DownloadButtons data={siteData} />
//             </>
//           ) : (
//             selectedSite && startDate && endDate && (
//               <div className="mt-4 bg-yellow-100 border border-yellow-300 p-4 rounded text-sm text-yellow-700">
//                 No measurement data available for the selected site and date range.
//               </div>
//             )
//           )}
//               </div>
//                     </div>

//       <button
//         onClick={() => setShowChat(true)}
//         className="fixed bottom-6 right-6 bg-indigo-600 text-white px-4 py-2 rounded-full shadow-lg z-40"
//       >
//         Open Chat
//       </button>

//       {showChat && (
//         <>
//           <div
//             className="fixed inset-0 bg-black bg-opacity-40 z-40"
//             onClick={() => setShowChat(false)}
//           />
//           <div
//             className="fixed bottom-6 right-6 w-96 max-w-full bg-white rounded-lg shadow-lg z-[9999] p-4 animate-slide-up"
//           >
//             <div className="flex justify-between items-center mb-2">
//               <h2 className="text-lg font-semibold">HAB Chat Assistant</h2>
//               <button onClick={() => setShowChat(false)} className="text-sm text-gray-500 hover:text-red-500">✕</button>
//             </div>
//             <div
//               ref={chatRef}
//               className="flex flex-col space-y-2 mb-2 max-h-80 overflow-y-auto"
//             >
//               {chatHistory.map((chat, idx) => (
//                 <div
//                   key={idx}
//                   className={`p-2 rounded-lg text-sm ${
//                     chat.role === 'user'
//                       ? 'bg-blue-100 self-end text-right'
//                       : 'bg-gray-200 self-start'
//                   }`}
//                 >
//                   {chat.message}
//                 </div>
//               ))}
//               {llmLoading && (
//                 <div className="text-sm italic text-gray-500 self-start">
//                   🤖 Assistant is thinking...
//                 </div>
//               )}
//             </div>

//             <textarea
//               value={userQuestion}
//               onChange={(e) => setUserQuestion(e.target.value)}
//               placeholder="Ask something like: Is the site at risk today?"
//               className="border rounded px-2 py-1 h-20 resize-none w-full"
//             />
//             <button
//               className="mt-2 bg-indigo-600 text-white px-4 py-2 rounded w-full"
//               onClick={askLLM}
//               disabled={!userQuestion || llmLoading}
//             >
//               Send
//             </button>
//           </div>
//         </>
//         )}

//       {/* Animation keyframe */}
//       <style>{`
//         @keyframes slideUp {
//           from { transform: translateY(100%); opacity: 0; }
//           to { transform: translateY(0); opacity: 1; }
//         }
//         .animate-slide-up {
//           animation: slideUp 0.3s ease-out;
//         }
//       `}</style>
//     </div>
//   );
// }


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
  const [datasetSummary, setDatasetSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [llmLoading, setLlmLoading] = useState(false);
  const [userQuestion, setUserQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [showChat, setShowChat] = useState(false);
  const [selectedSiteStats, setSelectedSiteStats] = useState(null);
  const [dataLimit, setDataLimit] = useState(1000);
  const chatRef = useRef(null);

  // Load sites and dataset summary on component mount
  useEffect(() => {
    Promise.all([
      axios.get('/api/discovery/sites'),
      axios.get('/api/summary')
    ]).then(([sitesRes, summaryRes]) => {
      setSites(sitesRes.data);
      setDatasetSummary(summaryRes.data);
    }).catch(err => {
      console.error('Error loading initial data:', err);
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
      fetchSiteStats();
      setChatHistory([]);
    }
  }, [selectedSite, startDate, endDate, dataLimit]);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [chatHistory, llmLoading]);

  const fetchMeasurements = async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/measurements', {
        site: selectedSite,
        start_date: startDate,
        end_date: endDate,
        limit: dataLimit
      });
      
      setSiteData(res.data.measurements || res.data);
      
      // Show warning if data was limited
      if (res.data.metadata?.limited) {
        console.warn(`Large dataset limited to ${dataLimit} records. Consider narrowing date range.`);
      }
    } catch (err) {
      console.error('Error fetching measurements:', err);
      setSiteData([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchSiteStats = async () => {
    try {
      const res = await axios.get(`/api/sites/${selectedSite}/stats`, {
        params: {
          start_date: startDate,
          end_date: endDate
        }
      });
      setSelectedSiteStats(res.data);
    } catch (err) {
      console.error('Error fetching site stats:', err);
      setSelectedSiteStats(null);
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

  const getSelectedSiteInfo = () => {
    return sites.find(s => s.site === selectedSite);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6 relative">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">
            🌊 HAB Risk Analysis Dashboard
          </h1>
          
          {/* Dataset Summary Card */}
          {datasetSummary && (
            <div className="bg-blue-50 p-4 rounded-lg text-sm">
              <h3 className="font-semibold text-blue-800 mb-2">Enhanced Dataset</h3>
              <div className="grid grid-cols-2 gap-2 text-blue-700">
                <div>📊 {datasetSummary.total_records?.toLocaleString()} records</div>
                <div>📍 {datasetSummary.unique_sites} sites</div>
                <div>📅 {datasetSummary.date_range?.start} to {datasetSummary.date_range?.end}</div>
                <div>🗺️ {Object.keys(datasetSummary.regions || {}).length} regions</div>
              </div>
            </div>
          )}
        </div>

        {/* Site Selection Controls */}
        <div className="bg-white p-6 rounded-lg shadow-lg mb-6">
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
                setSelectedSiteStats(null);
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
            
            {/* Data Limit Control */}
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">Data Limit:</label>
              <select 
                value={dataLimit} 
                onChange={(e) => setDataLimit(Number(e.target.value))}
                className="border rounded px-2 py-1"
              >
                <option value={100}>100 records</option>
                <option value={500}>500 records</option>
                <option value={1000}>1,000 records</option>
                <option value={5000}>5,000 records</option>
                <option value={10000}>10,000 records</option>
              </select>
            </div>
          </div>

          {/* Selected Site Information */}
          {selectedSite && getSelectedSiteInfo() && (
            <div className="bg-gray-50 p-4 rounded border-l-4 border-blue-500">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium">Region:</span> {getSelectedSiteInfo().region}
                </div>
                <div>
                  <span className="font-medium">Records:</span> {getSelectedSiteInfo().total_records?.toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Avg Chl-a:</span> {getSelectedSiteInfo().avg_chlorophyll?.toFixed(2)} µg/L
                </div>
                <div>
                  <span className="font-medium">Risk Level:</span> 
                  <span className={`ml-1 px-2 py-1 rounded text-xs ${
                    getSelectedSiteInfo().dominant_risk_level === 'high' ? 'bg-red-100 text-red-700' :
                    getSelectedSiteInfo().dominant_risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {getSelectedSiteInfo().dominant_risk_level}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading enhanced dataset...</p>
          </div>
        )}

        {/* Main Content */}
        <div className="flex gap-6">
          <div className="flex-1">
            {siteData.length > 0 ? (
              <>
                {/* Site Statistics Panel */}
                {selectedSiteStats && (
                  <div className="bg-white p-6 rounded-lg shadow-lg mb-6">
                    <h2 className="text-xl font-semibold mb-4">📊 Site Analytics: {selectedSiteStats.site_name}</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-3 bg-blue-50 rounded">
                        <div className="text-2xl font-bold text-blue-600">
                          {selectedSiteStats.total_records?.toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-600">Total Records</div>
                      </div>
                      <div className="text-center p-3 bg-green-50 rounded">
                        <div className="text-2xl font-bold text-green-600">
                          {selectedSiteStats.chlorophyll_stats?.mean?.toFixed(2)}
                        </div>
                        <div className="text-sm text-gray-600">Avg Chl-a (µg/L)</div>
                      </div>
                      <div className="text-center p-3 bg-yellow-50 rounded">
                        <div className="text-2xl font-bold text-yellow-600">
                          {(selectedSiteStats.risk_analysis?.avg_bloom_probability * 100)?.toFixed(1)}%
                        </div>
                        <div className="text-sm text-gray-600">Bloom Probability</div>
                      </div>
                      <div className="text-center p-3 bg-red-50 rounded">
                        <div className="text-2xl font-bold text-red-600">
                          {selectedSiteStats.risk_analysis?.bloom_events || 0}
                        </div>
                        <div className="text-sm text-gray-600">Bloom Events</div>
                      </div>
                    </div>
                    
                    {/* Environmental Conditions */}
                    {selectedSiteStats.environmental_conditions && (
                      <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                        <div className="bg-gray-50 p-2 rounded text-center">
                          <div className="font-medium">🌡️ SST</div>
                          <div>{selectedSiteStats.environmental_conditions.avg_sst?.toFixed(1)}°C</div>
                        </div>
                        <div className="bg-gray-50 p-2 rounded text-center">
                          <div className="font-medium">🌫️ Turbidity</div>
                          <div>{selectedSiteStats.environmental_conditions.avg_turbidity?.toFixed(1)} NTU</div>
                        </div>
                        {selectedSiteStats.environmental_conditions.avg_salinity && (
                          <div className="bg-gray-50 p-2 rounded text-center">
                            <div className="font-medium">🧂 Salinity</div>
                            <div>{selectedSiteStats.environmental_conditions.avg_salinity?.toFixed(1)} PSU</div>
                          </div>
                        )}
                        {selectedSiteStats.environmental_conditions.avg_wind_speed && (
                          <div className="bg-gray-50 p-2 rounded text-center">
                            <div className="font-medium">💨 Wind</div>
                            <div>{selectedSiteStats.environmental_conditions.avg_wind_speed?.toFixed(1)} m/s</div>
                          </div>
                        )}
                        {selectedSiteStats.environmental_conditions.avg_wave_height && (
                          <div className="bg-gray-50 p-2 rounded text-center">
                            <div className="font-medium">🌊 Waves</div>
                            <div>{selectedSiteStats.environmental_conditions.avg_wave_height?.toFixed(1)} m</div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                <div className="bg-white p-6 rounded-lg shadow-lg mb-6">
                  <h2 className="text-xl font-semibold mb-4">🗺️ Geographic Distribution</h2>
                  <GeoMap siteData={siteData} />
                </div>

                <div className="bg-white p-6 rounded-lg shadow-lg mb-6">
                  <h2 className="text-xl font-semibold mb-4">📈 Time Series Analysis</h2>
                  <TimeTrendsChart data={siteData} />
                </div>

                <RiskPanel data={siteData} />
                
                <div className="mt-4">
                  <DownloadButtons data={siteData} />
                </div>
              </>
            ) : (
              selectedSite && startDate && endDate && !loading && (
                <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-lg text-center">
                  <div className="text-yellow-700 text-lg mb-2">📭 No Data Available</div>
                  <p className="text-yellow-600">
                    No measurement data found for <strong>{selectedSite}</strong> between {startDate} and {endDate}.
                  </p>
                  <p className="text-sm text-yellow-600 mt-2">
                    Try expanding your date range or selecting a different site.
                  </p>
                </div>
              )
            )}
          </div>
        </div>
      </div>

      {/* Enhanced Chat Interface */}
      <button
        onClick={() => setShowChat(true)}
        className="fixed bottom-6 right-6 bg-gradient-to-r from-blue-500 to-blue-600 text-white px-6 py-3 rounded-full shadow-lg z-40 hover:from-blue-600 hover:to-blue-700 transition-all duration-200"
      >
        💬 HAB Expert Chat
      </button>

      {showChat && (
        <>
          <div
            className="fixed inset-0 bg-black bg-opacity-40 z-40"
            onClick={() => setShowChat(false)}
          />
          <div className="fixed bottom-6 right-6 w-96 max-w-full bg-white rounded-lg shadow-2xl z-[9999] animate-slide-up">
            {/* Chat Header */}
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4 rounded-t-lg">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-semibold">🤖 HAB Assistant</h2>
                  {selectedSite && (
                    <p className="text-blue-100 text-sm">Site name: {selectedSite}</p>
                  )}
                </div>
                <button 
                  onClick={() => setShowChat(false)} 
                  className="text-blue-100 hover:text-white text-xl"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Chat Messages */}
            <div
              ref={chatRef}
              className="flex flex-col space-y-3 p-4 max-h-80 overflow-y-auto bg-gray-50"
            >
              {chatHistory.length === 0 && (
                <div className="text-gray-500 text-sm text-center py-4">
                  👋 Ask me about HAB risks, environmental conditions, or mitigation strategies!
                </div>
              )}
              
              {chatHistory.map((chat, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg text-sm max-w-[85%] ${
                    chat.role === 'user'
                      ? 'bg-blue-500 text-white self-end ml-auto'
                      : 'bg-white border self-start mr-auto'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{chat.message}</div>
                </div>
              ))}
              
              {llmLoading && (
                <div className="bg-white border p-3 rounded-lg text-sm self-start mr-auto">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                    <span className="text-gray-600">Assistant is thinking...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Chat Input */}
            <div className="p-4 border-t bg-white rounded-b-lg">
              <textarea
                value={userQuestion}
                onChange={(e) => setUserQuestion(e.target.value)}
                placeholder="Ask about bloom risks, environmental conditions, or get recommendations..."
                className="w-full border rounded-lg px-3 py-2 h-20 resize-none text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    askLLM();
                  }
                }}
              />
              <button
                className="mt-2 w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors duration-200 disabled:opacity-50"
                onClick={askLLM}
                disabled={!userQuestion.trim() || llmLoading || !selectedSite}
              >
                {llmLoading ? 'Thinking...' : 'Send Message'}
              </button>
              
              {!selectedSite && (
                <p className="text-xs text-gray-500 mt-1 text-center">
                  Select a site to start chatting
                </p>
              )}
            </div>
          </div>
        </>
      )}

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