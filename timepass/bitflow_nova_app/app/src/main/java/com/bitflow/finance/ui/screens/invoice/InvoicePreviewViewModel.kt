package com.bitflow.finance.ui.screens.invoice

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.repository.InvoiceRepository
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.ZoneId
import javax.inject.Inject

@HiltViewModel
class InvoicePreviewViewModel @Inject constructor(
    private val repository: InvoiceRepository
) : ViewModel() {

    private val _state = MutableStateFlow(InvoiceState())
    val state: StateFlow<InvoiceState> = _state.asStateFlow()

    fun loadInvoice(id: Long) {
        viewModelScope.launch {
            val invoice = repository.getInvoiceById(id)
            if (invoice != null) {
                val gson = Gson()
                val itemType = object : TypeToken<List<InvoiceItem>>() {}.type
                val items: List<InvoiceItem> = try {
                    gson.fromJson(invoice.itemsJson, itemType)
                } catch (e: Exception) {
                    emptyList()
                }

                _state.update {
                    it.copy(
                        invoiceNumber = invoice.invoiceNumber,
                        clientName = invoice.clientName,
                        clientAddress = invoice.clientAddress,
                        date = Instant.ofEpochMilli(invoice.date).atZone(ZoneId.systemDefault()).toLocalDate(),
                        dueDate = Instant.ofEpochMilli(invoice.dueDate).atZone(ZoneId.systemDefault()).toLocalDate(),
                        items = items,
                        taxRate = invoice.taxRate
                    )
                }
            }
        }
    }
}
