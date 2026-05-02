import React, { useState, useRef } from 'react';
import { Plus, Trash2, Download } from 'lucide-react';
import html2pdf from 'html2pdf.js';
import storage from '../../utils/localStorage';

const InvoiceTab = () => {
  const invoiceRef = useRef(null);
  
  const [formData, setFormData] = useState({
    invoiceNumber: `INV-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
    date: new Date().toISOString().split('T')[0],
    dueDate: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    clientName: '',
    clientEmail: '',
    clientPhone: '',
    clientAddress: '',
    clientGSTIN: '',
    items: [
      { description: '', details: '', quantity: 1, rate: 0 }
    ],
    taxRate: 18,
    notes: ''
  });

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, { description: '', details: '', quantity: 1, rate: 0 }]
    }));
  };

  const removeItem = (index) => {
    if (formData.items.length > 1) {
      setFormData(prev => ({
        ...prev,
        items: prev.items.filter((_, i) => i !== index)
      }));
    }
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    setFormData(prev => ({ ...prev, items: newItems }));
  };

  const calculateSubtotal = () => {
    return formData.items.reduce((sum, item) => sum + (item.quantity * item.rate), 0);
  };

  const calculateTax = () => {
    return calculateSubtotal() * (formData.taxRate / 100);
  };

  const calculateTotal = () => {
    return calculateSubtotal() + calculateTax();
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const downloadPDF = async () => {
    try {
      // Save to Firebase first
      const invoiceData = {
        ...formData,
        createdAt: new Date().toISOString(),
        totalAmount: formatCurrency(calculateTotal()),
        subtotal: calculateSubtotal(),
        taxAmount: calculateTax(),
        total: calculateTotal(),
        createdBy: sessionStorage.getItem('generator_user') || 'Generator'
      };

      await storage.addDoc('generator_invoices', invoiceData);
      
      // Then download PDF
      html2pdf().set({
        filename: `Invoice_${formData.invoiceNumber}.pdf`,
        html2canvas: { scale: 2 },
        jsPDF: { format: 'a4', orientation: 'portrait' }
      }).from(invoiceRef.current).save();

      alert('✓ Invoice saved and downloaded successfully!');
    } catch (error) {
      console.error('Error saving invoice:', error);
      alert('Failed to save invoice. PDF will still download.');
      
      // Download PDF anyway
      html2pdf().set({
        filename: `Invoice_${formData.invoiceNumber}.pdf`,
        html2canvas: { scale: 2 },
        jsPDF: { format: 'a4', orientation: 'portrait' }
      }).from(invoiceRef.current).save();
    }
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 lg:gap-8">
      {/* Left - Form */}
      <div className="space-y-4 lg:space-y-6">
        {/* Invoice Details */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h3 className="font-bold text-slate-900 mb-4">Invoice Details</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Invoice Number</label>
              <input
                type="text"
                value={formData.invoiceNumber}
                onChange={(e) => setFormData({ ...formData, invoiceNumber: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Date</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Due Date</label>
                <input
                  type="date"
                  value={formData.dueDate}
                  onChange={(e) => setFormData({ ...formData, dueDate: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Client Details */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h3 className="font-bold text-slate-900 mb-4">Client Details</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Client Name</label>
              <input
                type="text"
                value={formData.clientName}
                onChange={(e) => setFormData({ ...formData, clientName: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="Company Name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
              <input
                type="email"
                value={formData.clientEmail}
                onChange={(e) => setFormData({ ...formData, clientEmail: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="client@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Phone</label>
              <input
                type="tel"
                value={formData.clientPhone}
                onChange={(e) => setFormData({ ...formData, clientPhone: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="+91 9876543210"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Address</label>
              <textarea
                value={formData.clientAddress}
                onChange={(e) => setFormData({ ...formData, clientAddress: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                rows="3"
                placeholder="Client address"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">GSTIN</label>
              <input
                type="text"
                value={formData.clientGSTIN}
                onChange={(e) => setFormData({ ...formData, clientGSTIN: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="22AAAAA0000A1Z5"
              />
            </div>
          </div>
        </div>

        {/* Items */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900">Line Items</h3>
            <button
              onClick={addItem}
              className="flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              Add Item
            </button>
          </div>
          <div className="space-y-4">
            {formData.items.map((item, index) => (
              <div key={index} className="border border-slate-200 rounded-lg p-4 relative">
                {formData.items.length > 1 && (
                  <button
                    onClick={() => removeItem(index)}
                    className="absolute top-2 right-2 text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs text-slate-600 mb-1">Item Name</label>
                    <input
                      type="text"
                      value={item.description}
                      onChange={(e) => updateItem(index, 'description', e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      placeholder="E.g. Web Development Service"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-600 mb-1">Description</label>
                    <input
                      type="text"
                      value={item.details}
                      onChange={(e) => updateItem(index, 'details', e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                      placeholder="Additional details"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs text-slate-600 mb-1">Quantity</label>
                      <input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', parseFloat(e.target.value) || 0)}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                        min="0.01"
                        step="0.01"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-600 mb-1">Rate (₹)</label>
                      <input
                        type="number"
                        value={item.rate}
                        onChange={(e) => updateItem(index, 'rate', parseFloat(e.target.value) || 0)}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                        min="0.01"
                        step="0.01"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-600 mb-1">Amount</label>
                      <div className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-medium text-slate-900">
                        {formatCurrency(item.quantity * item.rate)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tax */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h3 className="font-bold text-slate-900 mb-4">Tax</h3>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">GST Rate (%)</label>
            <input
              type="number"
              value={formData.taxRate}
              onChange={(e) => setFormData({ ...formData, taxRate: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              min="0"
              max="100"
            />
          </div>
        </div>

        {/* Download Button */}
        <button
          onClick={downloadPDF}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition font-medium"
        >
          <Download className="w-5 h-5" />
          Download Invoice PDF
        </button>
      </div>

      {/* Right - Preview */}
      <div className="xl:sticky xl:top-24 h-fit">
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
          <div className="bg-blue-900 text-white px-6 py-3 text-sm font-medium">
            Invoice Preview
          </div>
          
          <div ref={invoiceRef} className="p-8 bg-white" style={{ fontFamily: 'Inter, sans-serif' }}>
            {/* Invoice Header */}
            <div className="border-b-4 border-slate-900 pb-6 mb-6">
              <div className="flex justify-between items-start">
                <div>
                  <div className="mb-3">
                    <span className="text-3xl font-black text-slate-900 tracking-tighter">BIT</span>
                    <span className="text-3xl font-black text-blue-600 tracking-tighter">FLOW</span>
                    <span className="text-3xl font-thin text-slate-400 ml-2 tracking-[0.2em]">NOVA</span>
                  </div>
                  <div className="text-sm text-slate-600 space-y-1">
                    <p>Pune, Maharashtra</p>
                    <p>bitflownova@gmail.com</p>
                    <p>+91 7558434111</p>
                    <p><span className="font-medium">GSTIN:</span> 27CMFPC6807E1ZA</p>
                  </div>
                </div>
                <div className="text-right">
                  <h2 className="text-4xl font-light text-slate-300 uppercase tracking-widest">Invoice</h2>
                  <div className="mt-4 space-y-1 text-sm">
                    <div><span className="text-slate-600">No:</span> <span className="font-semibold">{formData.invoiceNumber}</span></div>
                    <div><span className="text-slate-600">Date:</span> {formData.date}</div>
                    <div><span className="text-slate-600">Due:</span> {formData.dueDate}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Client Info */}
            <div className="bg-slate-50 p-4 rounded mb-6">
              <p className="text-xs font-bold text-slate-600 uppercase mb-2">Bill To</p>
              <p className="font-bold text-slate-900 text-lg">{formData.clientName || 'Client Name'}</p>
              {formData.clientGSTIN && <p className="text-xs text-slate-600">GSTIN: {formData.clientGSTIN}</p>}
              <p className="text-sm text-slate-600 whitespace-pre-line">{formData.clientAddress}</p>
              {formData.clientEmail && <p className="text-sm text-slate-600">{formData.clientEmail}</p>}
              {formData.clientPhone && <p className="text-sm text-slate-600">{formData.clientPhone}</p>}
            </div>

            {/* Items Table */}
            <table className="w-full mb-6">
              <thead>
                <tr className="border-b-2 border-slate-900">
                  <th className="text-left py-2 text-xs font-bold text-slate-900 uppercase">Description</th>
                  <th className="text-center py-2 text-xs font-bold text-slate-900 uppercase w-16">Qty</th>
                  <th className="text-right py-2 text-xs font-bold text-slate-900 uppercase w-24">Rate</th>
                  <th className="text-right py-2 text-xs font-bold text-slate-900 uppercase w-28">Amount</th>
                </tr>
              </thead>
              <tbody>
                {formData.items.map((item, index) => (
                  <tr key={index} className="border-b border-slate-200">
                    <td className="py-3">
                      <div className="font-medium text-slate-800">{item.description || 'Item'}</div>
                      {item.details && <div className="text-xs text-slate-500 mt-1">{item.details}</div>}
                    </td>
                    <td className="text-center text-slate-700">{item.quantity}</td>
                    <td className="text-right text-slate-700">{formatCurrency(item.rate)}</td>
                    <td className="text-right font-medium text-slate-900">{formatCurrency(item.quantity * item.rate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Totals */}
            <div className="flex justify-end mb-6">
              <div className="w-64">
                <div className="flex justify-between py-2 border-b border-slate-200">
                  <span className="text-sm text-slate-600">Subtotal</span>
                  <span className="font-medium">{formatCurrency(calculateSubtotal())}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-200">
                  <span className="text-sm text-slate-600">GST ({formData.taxRate}%)</span>
                  <span className="font-medium">{formatCurrency(calculateTax())}</span>
                </div>
                <div className="flex justify-between py-3 text-xl font-bold text-slate-900">
                  <span>Total</span>
                  <span>{formatCurrency(calculateTotal())}</span>
                </div>
              </div>
            </div>

            {/* Payment Info */}
            <div className="bg-slate-50 p-4 rounded text-xs">
              <h4 className="font-bold text-slate-900 uppercase mb-2">Payment Information</h4>
              <div className="space-y-1 text-slate-600">
                <div><span className="font-medium">Bank:</span> INDUSIND BANK</div>
                <div><span className="font-medium">Account:</span> BITFLOW NOVA</div>
                <div><span className="font-medium">Account No:</span> 257558434111</div>
                <div><span className="font-medium">IFSC:</span> INDB0000142</div>
              </div>
            </div>

            {/* Footer */}
            <div className="mt-6 pt-4 border-t border-slate-200 text-xs text-slate-500 text-center">
              Computer Generated Invoice - Bitflow Nova © {new Date().getFullYear()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvoiceTab;
