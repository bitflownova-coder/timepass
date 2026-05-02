import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, LogOut, FileText, Receipt, History } from 'lucide-react';
import html2pdf from 'html2pdf.js';
import InvoiceTab from './InvoiceTab';
import QuotationTab from './QuotationTab';
import HistoryTab from './HistoryTab';

const InvoiceGenerator = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('invoice');

  const handleLogout = () => {
    sessionStorage.removeItem('generator_auth');
    sessionStorage.removeItem('generator_user');
    navigate('/generator/login');
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h1 className="text-lg sm:text-2xl font-bold text-slate-900">Invoice & Quotation Generator</h1>
              <p className="text-xs sm:text-sm text-slate-600 mt-1 hidden sm:block">Create professional documents instantly</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6">
        <div className="flex gap-2 mb-4 sm:mb-6 overflow-x-auto pb-2 scrollbar-hide">
          <button
            onClick={() => setActiveTab('invoice')}
            className={`flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition whitespace-nowrap ${
              activeTab === 'invoice'
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-white text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Receipt className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="text-sm sm:text-base">Invoice</span>
          </button>
          <button
            onClick={() => setActiveTab('quotation')}
            className={`flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition whitespace-nowrap ${
              activeTab === 'quotation'
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-white text-slate-600 hover:bg-slate-50'
            }`}
          >
            <FileText className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="text-sm sm:text-base">Quotation</span>
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition whitespace-nowrap ${
              activeTab === 'history'
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-white text-slate-600 hover:bg-slate-50'
            }`}
          >
            <History className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="text-sm sm:text-base">History</span>
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'invoice' && <InvoiceTab />}
        {activeTab === 'quotation' && <QuotationTab />}
        {activeTab === 'history' && <HistoryTab />}
      </div>
    </div>
  );
};

export default InvoiceGenerator;
