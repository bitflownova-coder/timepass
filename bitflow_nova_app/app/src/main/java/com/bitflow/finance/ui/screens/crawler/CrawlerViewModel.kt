package com.bitflow.finance.ui.screens.crawler

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.CrawlSessionEntity
import com.bitflow.finance.domain.repository.CrawlerRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@HiltViewModel
class CrawlerViewModel @Inject constructor(
    private val repository: CrawlerRepository
) : ViewModel() {

    val allSessions: StateFlow<List<CrawlSessionEntity>> = repository.getAllSessions()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    init {
        // Simple polling mechanism
        viewModelScope.launch {
            while (true) {
                try {
                    // Filter running sessions
                    val currentSessions = allSessions.value
                    if (currentSessions.isNotEmpty()) {
                        val activeSessions = currentSessions.filter { 
                            it.status == "RUNNING" || it.status == "PENDING" || it.status == "PAUSED"
                        }
                        
                        activeSessions.forEach { session ->
                            repository.checkStatus(session.id)
                        }
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
                kotlinx.coroutines.delay(3000) // Poll every 3 seconds
            }
        }
    }

    fun getSession(id: Long) = repository.getSessionFlow(id)

    fun startCrawl(url: String, depth: Int) {
        viewModelScope.launch {
             // Create Session which triggers API call
             repository.createSession(url, depth, "")
        }
    }
    
    fun pauseCrawl(id: Long) {
        viewModelScope.launch { repository.pauseCrawl(id) }
    }

    fun resumeCrawl(id: Long) {
        viewModelScope.launch { repository.resumeCrawl(id) }
    }

    fun stopCrawl(id: Long) {
        viewModelScope.launch { repository.stopCrawl(id) }
    }

    suspend fun getReport(id: Long) = repository.getReport(id)
}

data class SessionFiles(
    val content: List<File>,
    val images: List<File>,
    val documents: List<File>
)
