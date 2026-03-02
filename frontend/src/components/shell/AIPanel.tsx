"use client";

import React, { useState } from 'react';

const TabButton = ({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) => (
  <button
    onClick={onClick}
    className={`flex-1 py-3 text-sm font-medium border-b-2 transition-colors ${
      active ? 'border-blue-500 text-white' : 'border-transparent text-gray-400 hover:text-gray-200'
    }`}
  >
    {label}
  </button>
);

export default function AIPanel() {
  const [activeTab, setActiveTab] = useState<'chat' | 'tasks' | 'reports'>('chat');

  return (
    <div className="w-80 h-full flex flex-col stell-panel z-40">
      <div className="flex border-b border-gray-700 px-2">
        <TabButton active={activeTab === 'chat'} label="Chat" onClick={() => setActiveTab('chat')} />
        <TabButton active={activeTab === 'tasks'} label="Tasks" onClick={() => setActiveTab('tasks')} />
        <TabButton active={activeTab === 'reports'} label="Reports" onClick={() => setActiveTab('reports')} />
      </div>

      <div className="flex-1 p-4 overflow-y-auto">
        {activeTab === 'chat' && (
          <div className="space-y-4">
            <div className="bg-gray-800 p-3 rounded-lg text-sm text-gray-300">
              <p className="font-bold text-blue-400 mb-1">STELL-AI</p>
              System operational. Event spine active. How can I assist with your production today?
            </div>
          </div>
        )}
        
        {activeTab === 'tasks' && (
          <div className="space-y-2">
            <div className="p-3 bg-gray-900 rounded border border-gray-700">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-mono text-yellow-500">PENDING</span>
                <span className="text-xs text-gray-500">#102</span>
              </div>
              <p className="text-sm">DXF Layer Analysis</p>
            </div>
            <div className="p-3 bg-gray-900 rounded border border-gray-700 opacity-50">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-mono text-green-500">DONE</span>
                <span className="text-xs text-gray-500">#101</span>
              </div>
              <p className="text-sm">Backup Verification</p>
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="space-y-2">
             <div className="text-xs font-mono text-gray-400">
                Today, 08:00 AM<br/>
                Backup synced to Google Drive.<br/>
                Size: 340MB<br/>
                Status: VERIFIED
             </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-gray-700">
        <div className="relative">
          <input 
            type="text" 
            placeholder="Ask STELL-AI..." 
            className="w-full bg-black border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>
    </div>
  );
}
