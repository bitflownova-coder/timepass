package com.bitflow.finance.ui.screens.invoice

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.InvoiceEntity
import com.bitflow.finance.data.repository.InvoiceRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.ZoneId
import javax.inject.Inject

import com.google.gson.Gson

@HiltViewModel
class InvoiceViewModel @Inject constructor(
    private val repository: InvoiceRepository
) : ViewModel() {

    private val _state = MutableStateFlow(InvoiceState())
    val state: StateFlow<InvoiceState> = _state.asStateFlow()

    fun saveInvoice(onSuccess: () -> Unit) {
        viewModelScope.launch {
            val currentState = _state.value
            val gson = Gson()
            val itemsJson = gson.toJson(currentState.items)
            
            val invoiceEntity = InvoiceEntity(
                userId = "", // Will be set by repository
                invoiceNumber = currentState.invoiceNumber,
                clientName = currentState.clientName,
                clientAddress = currentState.clientAddress,
                date = currentState.date.atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli(),
                dueDate = currentState.dueDate.atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli(),
                itemsJson = itemsJson,
                taxRate = currentState.taxRate,
                amount = currentState.grandTotal
            )
            repository.saveInvoice(invoiceEntity)
            onSuccess()
        }
    }

    fun updateInvoiceNumber(number: String) {
        _state.update { it.copy(invoiceNumber = number) }
    }

    fun updateDate(date: LocalDate) {
        _state.update { it.copy(date = date) }
    }

    fun updateDueDate(date: LocalDate) {
        _state.update { it.copy(dueDate = date) }
    }

    fun updateClientName(name: String) {
        _state.update { it.copy(clientName = name) }
    }

    fun updateClientAddress(address: String) {
        _state.update { it.copy(clientAddress = address) }
    }

    fun addItem() {
        _state.update {
            val newItems = it.items + InvoiceItem(description = "New Item", quantity = 1, rate = 0.0)
            it.copy(items = newItems)
        }
    }

    fun removeItem(item: InvoiceItem) {
        _state.update {
            val newItems = it.items.filter { it.id != item.id }
            it.copy(items = newItems)
        }
    }

    fun updateItem(item: InvoiceItem, description: String, subDescription: String, quantity: Int, rate: Double) {
        _state.update {
            val newItems = it.items.map { currentItem ->
                if (currentItem.id == item.id) {
                    currentItem.copy(
                        description = description,
                        subDescription = subDescription,
                        quantity = quantity,
                        rate = rate
                    )
                } else {
                    currentItem
                }
            }
            it.copy(items = newItems)
        }
    }

    fun updateTaxRate(rate: Double) {
        _state.update { it.copy(taxRate = rate) }
    }
}
