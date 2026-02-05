package com.bitflow.finance.ui.screens.clients

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.dao.ClientDao
import com.bitflow.finance.data.local.dao.InvoiceDao
import com.bitflow.finance.data.local.entity.ClientEntity
import com.bitflow.finance.data.local.entity.InvoiceEntity
import com.bitflow.finance.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject
import kotlinx.coroutines.flow.first

data class ClientWithBalance(
    val client: ClientEntity,
    val totalInvoiced: Double,
    val totalPaid: Double,
    val balance: Double, // Outstanding
    val invoiceCount: Int
)

@HiltViewModel
class ClientLedgerViewModel @Inject constructor(
    private val clientDao: ClientDao,
    private val invoiceDao: InvoiceDao,
    private val authRepository: AuthRepository
) : ViewModel() {

    @OptIn(ExperimentalCoroutinesApi::class)
    val clientsWithBalance: StateFlow<List<ClientWithBalance>> = authRepository.currentUserId
        .filterNotNull()
        .flatMapLatest { userId ->
            combine(
                clientDao.getAllClients(userId),
                invoiceDao.getAllInvoices(userId)
            ) { clients, invoices ->
                clients.map { client ->
                    val clientInvoices = invoices.filter { it.clientName == client.name }
                    val totalInvoiced = clientInvoices.sumOf { it.amount }
                    val totalPaid = clientInvoices.filter { it.isPaid }.sumOf { it.amount }
                    ClientWithBalance(
                        client = client,
                        totalInvoiced = totalInvoiced,
                        totalPaid = totalPaid,
                        balance = totalInvoiced - totalPaid,
                        invoiceCount = clientInvoices.size
                    )
                }
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun addClient(name: String, email: String, phone: String, gstin: String) {
        viewModelScope.launch {
            val userId = authRepository.currentUserId.first()
            clientDao.insertClient(
                ClientEntity(
                    userId = userId,
                    name = name,
                    email = email,
                    phone = phone,
                    gstin = gstin
                )
            )
        }
    }

    fun deleteClient(client: ClientEntity) {
        viewModelScope.launch {
            clientDao.deleteClient(client)
        }
    }
}
