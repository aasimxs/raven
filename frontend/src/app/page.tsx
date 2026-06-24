"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";

const GraphComponent = dynamic(() => import("./GraphComponent"), { ssr: false });

export default function Home() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [cases, setCases] = useState<any[]>([]);
  
  const [activeCase, setActiveCase] = useState<any>(null);
  const [targetType, setTargetType] = useState("username");
  const [targetValue, setTargetValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [viewMode, setViewMode] = useState<"list" | "graph">("list");
  
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [caseToDelete, setCaseToDelete] = useState<{id: number, name: string} | null>(null);

  // Themed Alert Modal State
  const [alertModalOpen, setAlertModalOpen] = useState(false);
  const [alertMessage, setAlertMessage] = useState("");

  const showAlert = (message: string) => {
    setAlertMessage(message);
    setAlertModalOpen(true);
  };

  // New Case State
  const [isCreating, setIsCreating] = useState(false);
  const [newCaseName, setNewCaseName] = useState("");

  const fetchCases = async () => {
    try {
      const res = await fetch("/cases/");
      const data = await res.json();
      setCases(data);
    } catch (e) {
      console.error("Failed to fetch cases", e);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleCreateCase = async () => {
    if (!newCaseName) return;
    try {
      const res = await fetch(`/cases/?name=${encodeURIComponent(newCaseName)}`, {
        method: "POST"
      });
      const data = await res.json();
      await fetchCases();
      selectCase(data.id);
      setIsCreating(false);
      setNewCaseName("");
    } catch (e) {
      console.error(e);
      showAlert("Failed to create case. Is the backend running?");
    }
  };

  const selectCase = async (id: number) => {
    setLoading(true);
    setEvidence([]);
    try {
      // Fetch case details (which includes targets)
      const cRes = await fetch(`/cases/${id}`);
      const cData = await cRes.json();
      setActiveCase(cData);

      // Fetch evidence
      const evRes = await fetch(`/cases/${id}/evidence`);
      const evData = await evRes.json();
      setEvidence(evData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const confirmDeleteCase = async () => {
    if (!caseToDelete) return;
    try {
      await fetch(`/cases/${caseToDelete.id}`, { method: 'DELETE' });
      if (activeCase?.id === caseToDelete.id) {
        setActiveCase(null);
        setEvidence([]);
      }
      await fetchCases();
    } catch (err) {
      console.error("Failed to delete case", err);
      showAlert("Failed to delete investigation.");
    } finally {
      setDeleteModalOpen(false);
      setCaseToDelete(null);
    }
  };

  const handleDeleteClick = (id: number, name: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setCaseToDelete({id, name});
    setDeleteModalOpen(true);
  };

  const handleSearch = async () => {
    if (!activeCase || !targetValue) return;
    setLoading(true);
    setEvidence([]);
    try {
      const res = await fetch(`/search/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: activeCase.id,
          target_type: targetType,
          target_value: targetValue
        })
      });
      if (!res.ok) throw new Error("API returned an error");
      // Refresh case data to show new target in history
      await fetchCases();
      await selectCase(activeCase.id);
      setTargetValue("");
    } catch (e) {
      console.error(e);
      showAlert("Search failed. Ensure the target is correct and the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const isDark = theme === "dark";

  return (
    <div className={`min-h-screen flex font-sans ${isDark ? "bg-[#0a0a0b] text-gray-200" : "bg-gray-50 text-gray-800"}`}>
      {/* Sidebar */}
      <div className={`w-80 shrink-0 border-r flex flex-col transition-colors ${isDark ? "bg-[#111113] border-gray-800/60" : "bg-white border-gray-200"}`}>
        <div className={`p-6 border-b flex items-center justify-between ${isDark ? "border-gray-800/60" : "border-gray-200"}`}>
          <div className="flex items-center gap-2">
            <img src="/icon.png" alt="Raven Logo" className="w-6 h-6 object-contain" />
            <h1 className="text-xl font-bold tracking-tight">Raven</h1>
          </div>
        </div>

        <div className="p-4">
          {!isCreating ? (
            <button 
              onClick={() => setIsCreating(true)}
              className="w-full bg-red-600 hover:bg-red-500 text-white font-medium px-4 py-3 rounded-xl transition-all shadow-[0_0_10px_rgba(239,68,68,0.2)] flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
              New Investigation
            </button>
          ) : (
            <div className="flex flex-col gap-2">
              <input 
                type="text" 
                placeholder="Case Designation..." 
                className={`w-full border rounded-xl px-4 py-2 focus:outline-none focus:ring-1 focus:ring-red-500/50 text-sm ${isDark ? "bg-[#1a1a1e] border-gray-800 text-gray-200" : "bg-gray-100 border-gray-300 text-gray-800"}`}
                value={newCaseName}
                onChange={e => setNewCaseName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleCreateCase()}
                autoFocus
              />
              <div className="flex gap-2">
                <button onClick={handleCreateCase} className="flex-1 bg-red-600 hover:bg-red-500 text-white text-xs font-bold py-2 rounded-lg">Create</button>
                <button onClick={() => setIsCreating(false)} className={`flex-1 text-xs font-bold py-2 rounded-lg ${isDark ? "bg-gray-800 hover:bg-gray-700 text-gray-300" : "bg-gray-200 hover:bg-gray-300 text-gray-700"}`}>Cancel</button>
              </div>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
          {cases.map(c => (
            <div 
              key={c.id} 
              onClick={() => selectCase(c.id)}
              className={`p-4 rounded-xl cursor-pointer border transition-all ${activeCase?.id === c.id ? (isDark ? "bg-[#1a1a1e] border-red-500/50" : "bg-red-50 border-red-400") : (isDark ? "bg-transparent border-gray-800/40 hover:border-gray-700" : "bg-transparent border-transparent hover:bg-gray-100")}`}
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className={`text-sm font-bold truncate pr-2 ${activeCase?.id === c.id ? (isDark ? "text-white" : "text-red-900") : (isDark ? "text-gray-300" : "text-gray-700")}`}>[{c.id}] {c.name}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-500 font-mono whitespace-nowrap">{c.targets?.length || 0} Targets</span>
                  <button 
                    onClick={(e) => handleDeleteClick(c.id, c.name, e)}
                    className={`p-1 rounded transition-colors ${isDark ? "hover:bg-red-900/30 text-gray-600 hover:text-red-400" : "hover:bg-red-100 text-gray-400 hover:text-red-600"}`}
                    title="Delete Investigation"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                  </button>
                </div>
              </div>
              {c.targets && c.targets.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {c.targets.slice(0, 3).map((t: any, i: number) => (
                    <span key={i} className={`text-[9px] px-1.5 py-0.5 rounded font-mono truncate max-w-full ${isDark ? "bg-[#222228] text-gray-400" : "bg-gray-200 text-gray-600"}`}>
                      {t.value}
                    </span>
                  ))}
                  {c.targets.length > 3 && (
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${isDark ? "bg-[#222228] text-gray-400" : "bg-gray-200 text-gray-600"}`}>+{c.targets.length - 3}</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className={`p-4 border-t flex items-center justify-between ${isDark ? "border-gray-800/60" : "border-gray-200"}`}>
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Theme</span>
          <button 
            onClick={() => setTheme(isDark ? "light" : "dark")}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${isDark ? "bg-red-600" : "bg-gray-300"}`}
          >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isDark ? "translate-x-6" : "translate-x-1"}`} />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        {!activeCase ? (
          <div className="flex items-center justify-center h-full">
            <div className={`text-center p-8 rounded-2xl border ${isDark ? "bg-[#111113] border-gray-800/60 shadow-2xl" : "bg-white border-gray-200 shadow-xl"} max-w-md`}>
              <div className="inline-flex items-center justify-center p-3 bg-red-500/10 rounded-full mb-4 border border-red-500/20">
                <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
              </div>
              <h2 className={`text-xl font-bold mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>Select an Investigation</h2>
              <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-600"}`}>Choose an existing case from the sidebar or create a new one to begin OSINT collection.</p>
            </div>
          </div>
        ) : (
          <div className="p-8 lg:p-12 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Control Panel */}
            <div className={`p-8 rounded-2xl border shadow-xl ${isDark ? "bg-[#111113] border-gray-800/60" : "bg-white border-gray-200"}`}>
              <div className={`flex items-center justify-between mb-8 pb-6 border-b ${isDark ? "border-gray-800/50" : "border-gray-100"}`}>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                  <h2 className="text-xl font-bold">
                    <span className={isDark ? "text-gray-400" : "text-gray-500"}>Operation: </span>
                    <span className={isDark ? "text-white" : "text-gray-900"}>{activeCase.name}</span>
                  </h2>
                </div>
                <a 
                  href={`http://localhost:8000/cases/${activeCase.id}/dossier`}
                  target="_blank"
                  className={`text-xs font-bold tracking-wider uppercase px-5 py-2.5 rounded-lg transition-all border flex items-center gap-2 ${isDark ? "bg-[#1a1a1e] hover:bg-[#222228] text-gray-300 border-gray-800 hover:border-gray-700" : "bg-gray-100 hover:bg-gray-200 text-gray-700 border-gray-300"}`}
                >
                  <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                  Export Dossier
                </a>
              </div>
              
              <div className="flex flex-col md:flex-row gap-4">
                <select 
                  className={`border rounded-xl px-5 py-4 focus:outline-none focus:ring-1 focus:ring-red-500/50 font-medium w-full md:w-48 appearance-none ${isDark ? "bg-[#1a1a1e] border-gray-800 text-gray-300" : "bg-gray-50 border-gray-300 text-gray-700"}`}
                  value={targetType}
                  onChange={e => setTargetType(e.target.value)}
                >
                  <option value="username">Username</option>
                  <option value="email">Email Address</option>
                  <option value="phone">Phone Number</option>
                </select>
                <div className="flex-1 relative">
                  <input 
                    type="text" 
                    placeholder="Enter target identifier..." 
                    className={`w-full border rounded-xl px-5 py-4 focus:outline-none focus:ring-1 focus:ring-red-500/50 transition-all ${isDark ? "bg-[#1a1a1e] border-gray-800 text-gray-200 placeholder-gray-600 shadow-inner" : "bg-white border-gray-300 text-gray-900 placeholder-gray-400 shadow-sm"}`}
                    value={targetValue}
                    onChange={e => setTargetValue(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSearch()}
                  />
                  <div className={`absolute right-4 top-4 text-xs font-mono ${isDark ? "text-gray-600" : "text-gray-400"}`}>TARGET_INPUT</div>
                </div>
                <button 
                  onClick={handleSearch}
                  disabled={loading}
                  className={`font-semibold px-8 py-4 rounded-xl transition-colors flex items-center justify-center gap-2 min-w-[160px] ${isDark ? "bg-white hover:bg-gray-200 text-black disabled:bg-gray-800 disabled:text-gray-500" : "bg-gray-900 hover:bg-gray-800 text-white disabled:bg-gray-300 disabled:text-gray-500"}`}
                >
                  {loading ? (
                    <>
                      <div className={`w-5 h-5 border-2 rounded-full animate-spin ${isDark ? "border-black/20 border-t-black disabled:border-t-gray-500" : "border-white/20 border-t-white disabled:border-t-gray-500"}`}></div>
                      Scanning
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                      Execute
                    </>
                  )}
                </button>
              </div>

              {/* Tabs */}
              <div className={`mt-8 flex gap-8 border-b ${isDark ? "border-gray-800/50" : "border-gray-200"}`}>
                <button 
                  className={`pb-4 text-sm font-bold tracking-wide transition-colors relative ${viewMode === 'list' ? 'text-red-500' : (isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-400 hover:text-gray-700')}`}
                  onClick={() => setViewMode('list')}
                >
                  INTELLIGENCE FEED
                  {viewMode === 'list' && <div className="absolute bottom-0 left-0 w-full h-[2px] bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]"></div>}
                </button>
                <button 
                  className={`pb-4 text-sm font-bold tracking-wide transition-colors relative ${viewMode === 'graph' ? 'text-red-500' : (isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-400 hover:text-gray-700')}`}
                  onClick={() => setViewMode('graph')}
                >
                  NODE GRAPH
                  {viewMode === 'graph' && <div className="absolute bottom-0 left-0 w-full h-[2px] bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]"></div>}
                </button>
              </div>
            </div>

            {viewMode === 'graph' ? (
              <div className={`border p-2 rounded-2xl shadow-xl overflow-hidden ${isDark ? "bg-[#111113] border-gray-800/60" : "bg-white border-gray-200"}`}>
                 <GraphComponent caseId={activeCase.id} theme={theme} />
              </div>
            ) : evidence.length > 0 && (() => {
              const grouped: Record<string, { found: any[], notFound: any[], errors: any[] }> = {};
              
              evidence.forEach(ev => {
                try {
                  const payload = JSON.parse(ev.raw_payload);
                  const targetName = payload.target || "Legacy Search (Unknown Target)";
                  
                  if (!grouped[targetName]) {
                    grouped[targetName] = { found: [], notFound: [], errors: [] };
                  }
                  
                  if (payload.exists) {
                    grouped[targetName].found.push({ev, payload});
                  } else if (payload.error) {
                    grouped[targetName].errors.push({ev, payload});
                  } else {
                    grouped[targetName].notFound.push({ev, payload});
                  }
                } catch(e) {}
              });

              return (
                <div className="space-y-16">
                  {Object.entries(grouped).map(([targetName, { found, notFound, errors }]) => (
                    <div key={targetName} className="space-y-6">
                      <div className={`pb-3 border-b ${isDark ? "border-gray-800" : "border-gray-200"}`}>
                        <h2 className={`text-xl font-bold flex items-center gap-3 ${isDark ? "text-red-400" : "text-red-600"}`}>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                          Target: {targetName}
                        </h2>
                      </div>
                      
                      <div className="flex flex-col gap-6">
                        {/* Active Hits */}
                        <div className="space-y-4">
                          <h3 className="text-xs font-bold tracking-widest text-red-500 uppercase mb-4 flex items-center gap-2">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            Verified Hits ({found.length})
                          </h3>
                          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                            {found.map(({ev, payload}, i) => (
                              <div key={i} className={`p-5 rounded-2xl flex flex-col sm:flex-row sm:items-center gap-5 border transition-colors group ${isDark ? "bg-[#111113] border-gray-800/60 hover:border-red-500/30" : "bg-white border-gray-200 hover:border-red-400/50 shadow-sm"}`}>
                                <div className={`border px-3 py-2 rounded-lg text-xs font-bold font-mono w-40 truncate shrink-0 transition-colors ${isDark ? "bg-[#1a1a1e] border-gray-800 text-gray-400 group-hover:text-red-400/80" : "bg-gray-50 border-gray-200 text-gray-600 group-hover:text-red-600"}`}>
                                  {ev.source}
                                </div>
                                <div className="flex-1 overflow-hidden">
                                  {payload.url ? (
                                    <a href={payload.url} target="_blank" rel="noreferrer" className={`text-sm truncate block transition-colors font-medium ${isDark ? "text-gray-200 hover:text-red-400" : "text-gray-800 hover:text-red-600"}`}>{payload.url}</a>
                                  ) : (
                                    <span className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>{payload.note || "Match verified."}</span>
                                  )}
                                  {payload.avatar_url && (
                                    <div className={`mt-4 flex items-start gap-4 p-4 rounded-xl border ${isDark ? "bg-[#1a1a1e] border-gray-800/80" : "bg-gray-50 border-gray-200"}`}>
                                      <img src={payload.avatar_url} alt="Profile" className={`w-14 h-14 rounded-full border object-cover shadow-md ${isDark ? "border-gray-700" : "border-gray-300"}`} />
                                      <div className="flex flex-col gap-1.5">
                                        <span className={`text-[10px] uppercase tracking-widest font-bold ${isDark ? "text-gray-500" : "text-gray-400"}`}>Image Extracted</span>
                                        <a 
                                          href={`https://tineye.com/search?url=${encodeURIComponent(payload.avatar_url)}`} 
                                          target="_blank" 
                                          rel="noreferrer"
                                          className={`text-xs flex items-center gap-1.5 w-max font-bold px-2.5 py-1 rounded border transition-colors ${isDark ? "text-blue-400 hover:text-blue-300 bg-blue-500/10 border-blue-500/20" : "text-blue-600 hover:text-blue-700 bg-blue-50 border-blue-200"}`}
                                        >
                                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                                          Reverse Search Pivot
                                        </a>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Null/Error Feed - Expandable */}
                        {(notFound.length > 0 || errors.length > 0) && (
                          <details className={`group border rounded-2xl transition-all ${isDark ? "border-gray-800/60 bg-[#111113]/50" : "border-gray-200 bg-gray-50/50"} [&_summary::-webkit-details-marker]:hidden`}>
                            <summary className="flex items-center gap-2 cursor-pointer select-none font-bold text-xs tracking-widest uppercase p-5 outline-none">
                              <span className={isDark ? "text-gray-400" : "text-gray-500"}>
                                Unsuccessful Scans ({notFound.length + errors.length})
                              </span>
                              <svg className={`w-4 h-4 transition-transform group-open:rotate-180 ${isDark ? "text-gray-500" : "text-gray-400"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                            </summary>
                            
                            <div className="px-5 pb-5 space-y-8">
                              {notFound.length > 0 && (
                                <div>
                                  <h3 className="text-xs font-bold tracking-widest text-gray-400 uppercase mb-4">Null Results ({notFound.length})</h3>
                                  <div className={`p-5 rounded-2xl flex flex-wrap gap-2 border ${isDark ? "bg-[#111113] border-gray-800/60" : "bg-white border-gray-200 shadow-sm"}`}>
                                    {notFound.map(({ev}, i) => (
                                      <span key={i} className={`border px-2.5 py-1 rounded-md text-[11px] font-mono font-medium ${isDark ? "bg-[#1a1a1e] border-gray-800 text-gray-500" : "bg-gray-50 border-gray-200 text-gray-500"}`}>
                                        {ev.source}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {errors.length > 0 && (
                                <div>
                                  <h3 className="text-xs font-bold tracking-widest text-red-500 uppercase mb-4">Failed Scans ({errors.length})</h3>
                                  <div className={`p-5 rounded-2xl flex flex-wrap gap-2 border ${isDark ? "bg-[#111113] border-red-900/20" : "bg-white border-red-200 shadow-sm"}`}>
                                    {errors.map(({ev, payload}, i) => (
                                      <span key={i} className={`border px-2.5 py-1 rounded-md text-[11px] font-mono font-medium ${isDark ? "bg-[#1a1a1e] border-red-900/30 text-red-400/60" : "bg-red-50 border-red-200 text-red-600/80"}`} title={payload.error}>
                                        {ev.source}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </details>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })()}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && caseToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className={`max-w-md w-full p-6 rounded-2xl shadow-2xl border ${isDark ? "bg-[#111113] border-red-900/30" : "bg-white border-red-200"} animate-in zoom-in-95 duration-200`}>
            <div className="flex items-center gap-4 mb-4">
              <div className={`p-3 rounded-full ${isDark ? "bg-red-500/10 text-red-500" : "bg-red-100 text-red-600"}`}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
              </div>
              <div>
                <h3 className={`text-lg font-bold ${isDark ? "text-white" : "text-gray-900"}`}>Delete Investigation</h3>
                <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>Case: {caseToDelete.name}</p>
              </div>
            </div>
            <p className={`text-sm mb-8 ${isDark ? "text-gray-300" : "text-gray-600"}`}>
              Are you sure you want to permanently delete this investigation? All associated targets, collected evidence, and node graphs will be destroyed. This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button 
                onClick={() => setDeleteModalOpen(false)} 
                className={`px-5 py-2.5 rounded-lg text-sm font-bold transition-colors ${isDark ? "bg-gray-800 hover:bg-gray-700 text-gray-300" : "bg-gray-200 hover:bg-gray-300 text-gray-700"}`}
              >
                Cancel
              </button>
              <button 
                onClick={confirmDeleteCase} 
                className={`px-5 py-2.5 rounded-lg text-sm font-bold transition-colors ${isDark ? "bg-red-600 hover:bg-red-500 text-white shadow-[0_0_10px_rgba(220,38,38,0.3)]" : "bg-red-600 hover:bg-red-700 text-white shadow-md"}`}
              >
                Destroy Investigation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generic Themed Alert Modal */}
      {alertModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className={`max-w-sm w-full p-6 rounded-2xl shadow-2xl border ${isDark ? "bg-[#111113] border-red-900/30" : "bg-white border-red-200"} animate-in zoom-in-95 duration-200`}>
            <div className="flex flex-col items-center text-center gap-4 mb-6">
              <div className={`p-4 rounded-full ${isDark ? "bg-red-500/10 text-red-500" : "bg-red-100 text-red-600"}`}>
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </div>
              <div>
                <h3 className={`text-lg font-bold mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>Notice</h3>
                <p className={`text-sm ${isDark ? "text-gray-300" : "text-gray-600"}`}>
                  {alertMessage}
                </p>
              </div>
            </div>
            <button 
              onClick={() => setAlertModalOpen(false)} 
              className={`w-full px-5 py-3 rounded-xl text-sm font-bold transition-colors shadow-sm ${isDark ? "bg-gray-800 hover:bg-gray-700 text-white border border-gray-700" : "bg-gray-100 hover:bg-gray-200 text-gray-900 border border-gray-200"}`}
            >
              Okay
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
