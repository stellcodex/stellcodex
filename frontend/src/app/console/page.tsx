import React from 'react';

export default function ConsolePage() {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-6">
        <h1 className="text-4xl font-bold tracking-tight text-white">
          STELL<span className="text-blue-500">CONSOLE</span>
        </h1>
        <p className="text-gray-400 text-lg">
          Select a file from the sidebar or drag & drop here to begin.
          <br />
          Supported formats: STEP, STL, DXF, PDF.
        </p>
        
        <div className="grid grid-cols-2 gap-4 mt-8">
          <button className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 transition-all group cursor-pointer">
            <div className="text-blue-400 mb-2 group-hover:scale-110 transition-transform flex justify-center">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
            </div>
            <div className="font-medium">Upload File</div>
            <div className="text-xs text-gray-500 mt-1">Local or Cloud</div>
          </button>
          
          <button className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 transition-all group cursor-pointer">
             <div className="text-green-400 mb-2 group-hover:scale-110 transition-transform flex justify-center">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
            </div>
            <div className="font-medium">Library</div>
            <div className="text-xs text-gray-500 mt-1">Browse Standard Parts</div>
          </button>
        </div>
      </div>
    </div>
  );
}
