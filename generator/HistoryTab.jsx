import React, { useState, useEffect } from 'react';
import { Download, FileText, Receipt, Clock, Search } from 'lucide-react';
import storage from '../../utils/localStorage';
import html2pdf from 'html2pdf.js';

const HistoryTab = () => {
  const [activeFilter, setActiveFilter] = useState('all'); // all, invoices, quotations
  const [invoices, setInvoices] = useState([]);
  const [quotations, setQuotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const [fetchedInvoices, fetchedQuotations] = await Promise.all([
        storage.getDocs('generator_invoices', 'createdAt', 'desc'),
        storage.getDocs('generator_quotations', 'createdAt', 'desc')
      ]);
      setInvoices(fetchedInvoices);
      setQuotations(fetchedQuotations);
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
    }
  };

  const regenerateAndDownloadPDF = (doc, type) => {
    const docContent = createDocumentHTML(doc, type);
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = docContent;
    
    const filename = type === 'invoice' 
      ? `Invoice_${doc.invoiceNumber || 'document'}.pdf`
      : `Quotation_${doc.quotationNumber || 'document'}.pdf`;

    html2pdf().set({
      filename: filename,
      html2canvas: { scale: 2 },
      jsPDF: { format: 'a4', orientation: 'portrait' }
    }).from(tempDiv).save();
  };

  const createDocumentHTML = (doc, type) => {
    const subtotal = doc.items?.reduce((sum, item) => sum + (item.quantity * item.rate), 0) || 0;
    const tax = subtotal * ((doc.taxRate || 18) / 100);
    const total = subtotal + tax;
    const formatCurrency = (amount) => new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(amount);

    return `
      <div style="max-width: 800px; margin: 0 auto; padding: 40px; font-family: system-ui, -apple-system, sans-serif; background: white;">
        <!-- Header -->
        <div style="border-bottom: 3px solid #2563eb; padding-bottom: 20px; margin-bottom: 30px;">
          <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
              <h1 style="font-size: 32px; font-weight: bold; color: #1e293b; margin: 0;">BitFlow Nova</h1>
              <p style="color: #64748b; margin: 5px 0 0 0;">Innovative Software Solutions</p>
            </div>
            <div style="text-align: right;">
              <h2 style="font-size: 24px; font-weight: bold; color: #2563eb; margin: 0;">${type === 'invoice' ? 'INVOICE' : 'QUOTATION'}</h2>
              <p style="color: #64748b; margin: 5px 0 0 0;">#${type === 'invoice' ? doc.invoiceNumber : doc.quotationNumber}</p>
            </div>
          </div>
        </div>

        <!-- From/To Section -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px;">
          <div>
            <h3 style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; margin: 0 0 10px 0;">From</h3>
            <p style="margin: 0; font-weight: 600; color: #1e293b;">BitFlow Nova</p>
            <p style="margin: 5px 0 0 0; color: #64748b; line-height: 1.6;">
              123 Business Street<br/>
              Mumbai, Maharashtra 400001<br/>
              India
            </p>
          </div>
          <div>
            <h3 style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; margin: 0 0 10px 0;">Bill To</h3>
            <p style="margin: 0; font-weight: 600; color: #1e293b;">${doc.clientName || ''}</p>
            <p style="margin: 5px 0 0 0; color: #64748b; line-height: 1.6;">
              ${doc.clientAddress ? doc.clientAddress.replace(/\n/g, '<br/>') : ''}<br/>
              ${doc.clientEmail || ''}<br/>
              ${doc.clientPhone || ''}<br/>
              ${doc.clientGSTIN ? `GSTIN: ${doc.clientGSTIN}` : ''}
            </p>
          </div>
        </div>

        <!-- Dates -->
        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 30px;">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
              <p style="margin: 0; font-size: 12px; color: #64748b; font-weight: 600;">DATE</p>
              <p style="margin: 5px 0 0 0; color: #1e293b; font-weight: 600;">${new Date(doc.date).toLocaleDateString()}</p>
            </div>
            <div>
              <p style="margin: 0; font-size: 12px; color: #64748b; font-weight: 600;">${type === 'invoice' ? 'DUE DATE' : 'VALID UNTIL'}</p>
              <p style="margin: 5px 0 0 0; color: #1e293b; font-weight: 600;">${new Date(doc.dueDate || doc.validUntil).toLocaleDateString()}</p>
            </div>
          </div>
        </div>

        <!-- Items Table -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
          <thead>
            <tr style="background: #f1f5f9; border-bottom: 2px solid #e2e8f0;">
              <th style="padding: 12px; text-align: left; font-size: 12px; font-weight: 600; color: #475569; text-transform: uppercase;">Item</th>
              <th style="padding: 12px; text-align: right; font-size: 12px; font-weight: 600; color: #475569; text-transform: uppercase;">Qty</th>
              <th style="padding: 12px; text-align: right; font-size: 12px; font-weight: 600; color: #475569; text-transform: uppercase;">Rate</th>
              <th style="padding: 12px; text-align: right; font-size: 12px; font-weight: 600; color: #475569; text-transform: uppercase;">Amount</th>
            </tr>
          </thead>
          <tbody>
            ${(doc.items || []).map(item => `
              <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 16px 12px;">
                  <p style="margin: 0; font-weight: 600; color: #1e293b;">${item.description || ''}</p>
                  ${item.details ? `<p style="margin: 4px 0 0 0; color: #64748b; font-size: 14px;">${item.details}</p>` : ''}
                </td>
                <td style="padding: 16px 12px; text-align: right; color: #1e293b;">${item.quantity || 0}</td>
                <td style="padding: 16px 12px; text-align: right; color: #1e293b;">${formatCurrency(item.rate || 0)}</td>
                <td style="padding: 16px 12px; text-align: right; font-weight: 600; color: #1e293b;">${formatCurrency((item.quantity || 0) * (item.rate || 0))}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <!-- Totals -->
        <div style="margin-left: auto; max-width: 350px;">
          <div style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between;">
            <span style="color: #64748b;">Subtotal</span>
            <span style="font-weight: 600; color: #1e293b;">${formatCurrency(subtotal)}</span>
          </div>
          <div style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between;">
            <span style="color: #64748b;">GST (${doc.taxRate || 18}%)</span>
            <span style="font-weight: 600; color: #1e293b;">${formatCurrency(tax)}</span>
          </div>
          <div style="padding: 16px 0; display: flex; justify-content: space-between; background: #f8fafc; padding-left: 12px; padding-right: 12px; border-radius: 8px; margin-top: 8px;">
            <span style="font-size: 18px; font-weight: 700; color: #1e293b;">Total</span>
            <span style="font-size: 20px; font-weight: 700; color: #2563eb;">${formatCurrency(total)}</span>
          </div>
        </div>

        ${doc.notes ? `
          <div style="margin-top: 30px; padding: 20px; background: #f8fafc; border-radius: 8px;">
            <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase;">Notes</p>
            <p style="margin: 0; color: #475569; line-height: 1.6;">${doc.notes}</p>
          </div>
        ` : ''}

        <!-- Footer -->
        <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e2e8f0; text-align: center;">
          <p style="margin: 0; color: #64748b; font-size: 14px;">Thank you for your business!</p>
        </div>
      </div>
    `;
  };

  const filteredData = () => {
    let combined = [];
    
    if (activeFilter === 'all' || activeFilter === 'invoices') {
      combined = [...combined, ...invoices.map(inv => ({ ...inv, type: 'invoice' }))];
    }
    
    if (activeFilter === 'all' || activeFilter === 'quotations') {
      combined = [...combined, ...quotations.map(quot => ({ ...quot, type: 'quotation' }))];
    }

    // Sort by date
    combined.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

    // Apply search filter
    if (searchTerm) {
      combined = combined.filter(doc => {
        const searchLower = searchTerm.toLowerCase();
        return (
          doc.clientName?.toLowerCase().includes(searchLower) ||
          doc.invoiceNumber?.toLowerCase().includes(searchLower) ||
          doc.quotationNumber?.toLowerCase().includes(searchLower)
        );
      });
    }

    return combined;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Clock className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading history...</p>
        </div>
      </div>
    );
  }

  const data = filteredData();

  return (
    <div className="space-y-6">
      {/* Filters and Search */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
        <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
          {/* Filter Tabs */}
          <div className="flex gap-2">
            <button
              onClick={() => setActiveFilter('all')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                activeFilter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              All ({invoices.length + quotations.length})
            </button>
            <button
              onClick={() => setActiveFilter('invoices')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                activeFilter === 'invoices'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Invoices ({invoices.length})
            </button>
            <button
              onClick={() => setActiveFilter('quotations')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                activeFilter === 'quotations'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Quotations ({quotations.length})
            </button>
          </div>

          {/* Search */}
          <div className="relative w-full md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>
      </div>

      {/* History List */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
        {data.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
              {activeFilter === 'invoices' ? (
                <Receipt className="w-8 h-8 text-slate-400" />
              ) : activeFilter === 'quotations' ? (
                <FileText className="w-8 h-8 text-slate-400" />
              ) : (
                <Clock className="w-8 h-8 text-slate-400" />
              )}
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">No records found</h3>
            <p className="text-slate-600">
              {searchTerm
                ? 'Try a different search term'
                : `No ${activeFilter === 'all' ? 'documents' : activeFilter} created yet`}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {data.map((doc) => {
              const subtotal = doc.items?.reduce((sum, item) => sum + (item.quantity * item.rate), 0) || 0;
              const tax = subtotal * ((doc.taxRate || 18) / 100);
              const total = subtotal + tax;

              return (
                <div
                  key={doc.id}
                  className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 p-4 border border-slate-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 transition"
                >
                  <div className="flex items-center gap-3 sm:gap-4 flex-1">
                    <div className={`p-2 sm:p-3 ${
                      doc.type === 'invoice' ? 'bg-green-100' : 'bg-purple-100'
                    } rounded-lg flex-shrink-0`}>
                      {doc.type === 'invoice' ? (
                        <Receipt className={`w-5 h-5 text-green-600`} />
                      ) : (
                        <FileText className={`w-5 h-5 text-purple-600`} />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-semibold text-slate-900">
                          {doc.type === 'invoice' ? doc.invoiceNumber : doc.quotationNumber}
                        </p>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                          doc.type === 'invoice' 
                            ? 'bg-green-100 text-green-700'
                            : 'bg-purple-100 text-purple-700'
                        }`}>
                          {doc.type === 'invoice' ? 'Invoice' : 'Quotation'}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600">{doc.clientName}</p>
                      <p className="text-xs text-slate-500 mt-1">
                        Created: {new Date(doc.createdAt).toLocaleString()}
                      </p>
                    </div>
                    <div className="text-left sm:text-right sm:ml-auto">
                      <p className="font-bold text-base sm:text-lg text-slate-900">{formatCurrency(total)}</p>
                      <p className="text-xs text-slate-500">
                        Due: {new Date(doc.dueDate || doc.validUntil).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => regenerateAndDownloadPDF(doc, doc.type)}
                    className="w-full sm:w-auto sm:ml-4 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                  >
                    <Download className="w-4 h-4" />
                    <span className="sm:inline">Download</span>
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryTab;
