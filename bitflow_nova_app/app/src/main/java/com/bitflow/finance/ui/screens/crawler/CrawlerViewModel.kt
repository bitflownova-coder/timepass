package com.bitflow.finance.ui.screens.crawler

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.CrawlSessionEntity
import com.bitflow.finance.domain.crawler.AnalysisReport
import com.bitflow.finance.domain.repository.CrawlerRepository
import com.bitflow.finance.domain.repository.SessionFiles
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CrawlerViewModel @Inject constructor(
    private val repository: CrawlerRepository
) : ViewModel() {

    val allSessions: StateFlow<List<CrawlSessionEntity>> = repository.getAllSessions()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    // Analysis report for current session
    private val _analysisReport = MutableStateFlow<AnalysisReport?>(null)
    val analysisReport: StateFlow<AnalysisReport?> = _analysisReport.asStateFlow()

    // Loading state for analysis
    private val _isLoadingAnalysis = MutableStateFlow(false)
    val isLoadingAnalysis: StateFlow<Boolean> = _isLoadingAnalysis.asStateFlow()

    // Session files
    private val _sessionFiles = MutableStateFlow<SessionFiles?>(null)
    val sessionFiles: StateFlow<SessionFiles?> = _sessionFiles.asStateFlow()

    init {
        // Polling mechanism - every 2 seconds for more responsive progress
        viewModelScope.launch {
            while (true) {
                try {
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
                kotlinx.coroutines.delay(2000) // Poll every 2 seconds
            }
        }
    }

    fun getSession(id: Long) = repository.getSessionFlow(id)

    fun startCrawl(url: String, depth: Int, isMobileMode: Boolean, scanCategories: Set<String> = emptySet()) {
        viewModelScope.launch {
             repository.createSession(url, depth, "", isMobileMode, scanCategories)
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

    /**
     * Load the full analysis report for a session.
     */
    fun loadAnalysisReport(sessionId: Long) {
        viewModelScope.launch {
            _isLoadingAnalysis.value = true
            try {
                _analysisReport.value = repository.getAnalysisReport(sessionId)
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                _isLoadingAnalysis.value = false
            }
        }
    }

    /**
     * Load session files.
     */
    fun loadSessionFiles(sessionId: Long) {
        viewModelScope.launch {
            try {
                _sessionFiles.value = repository.getReport(sessionId)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    /**
     * Get content of a specific file.
     */
    suspend fun getFileContent(sessionId: Long, filename: String): String {
        return repository.getFileContent(sessionId, filename)
    }

    /**
     * Get HTML source of a specific page.
     */
    suspend fun getHtmlContent(sessionId: Long, filename: String): String {
        return repository.getHtmlContent(sessionId, filename)
    }

    fun generateSitemap(sessionId: Long, onResult: (String) -> Unit) {
        viewModelScope.launch {
            val result = repository.generateSitemap(sessionId)
            onResult(result)
        }
    }

    fun exportData(sessionId: Long, format: String, onResult: (String) -> Unit) {
        viewModelScope.launch {
            val result = repository.exportData(sessionId, format)
            onResult(result)
        }
    }
    
    fun generatePdf(sessionId: Long, onResult: (String) -> Unit) {
        viewModelScope.launch {
            val result = repository.generatePdf(sessionId)
            onResult(result)
        }
    }

    /**
     * Clear analysis data when leaving detail screen.
     */
    fun clearAnalysisData() {
        _analysisReport.value = null
        _sessionFiles.value = null
    }
}
