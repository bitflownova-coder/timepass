package com.bitflow.finance.ui.screens.bitflow

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.InvoiceEntity
import com.bitflow.finance.data.repository.InvoiceRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

import kotlinx.coroutines.launch

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine

@HiltViewModel
class InvoiceRecordsViewModel @Inject constructor(
    private val repository: InvoiceRepository
) : ViewModel() {

    private val _searchQuery = MutableStateFlow("")
    val searchQuery = _searchQuery.asStateFlow()

    val invoices: StateFlow<List<InvoiceEntity>> = combine(
        repository.getAllInvoices(),
        _searchQuery
    ) { list, query ->
        if (query.isBlank()) {
            list
        } else {
            list.filter { 
                it.clientName.contains(query, ignoreCase = true) || 
                it.invoiceNumber.contains(query, ignoreCase = true) 
            }
        }
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = emptyList()
    )

    fun onSearchQueryChange(query: String) {
        _searchQuery.value = query
    }

    fun toggleStatus(invoice: InvoiceEntity) {
        viewModelScope.launch {
            repository.updateInvoice(invoice.copy(isPaid = !invoice.isPaid))
        }
    }

    fun deleteInvoice(invoice: InvoiceEntity) {
        viewModelScope.launch {
            repository.deleteInvoice(invoice.id)
        }
    }
}
