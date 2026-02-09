package com.bitflow.finance.domain.repository

import com.bitflow.finance.data.local.dao.CrawlSessionDao
import com.bitflow.finance.data.local.entity.CrawlSessionEntity
import com.bitflow.finance.domain.crawler.CrawlerBridge
import com.bitflow.finance.domain.crawler.AnalysisReport
import kotlinx.coroutines.flow.Flow
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CrawlerRepository @Inject constructor(
    private val crawlerDao: CrawlSessionDao,
    private val crawlerBridge: CrawlerBridge
) {
    fun getAllSessions(): Flow<List<CrawlSessionEntity>> = crawlerDao.getAllSessions()
    
    fun getSessionFlow(id: Long): Flow<CrawlSessionEntity?> = crawlerDao.getSessionFlow(id)

    /**
     * Create a new crawl session and start the embedded Python crawler.
     */
    suspend fun createSession(
        url: String, 
        depth: Int,
        outputPath: String,
        isMobileMode: Boolean = false,
        scanCategories: Set<String> = emptySet()
    ): Long {
        // 1. Create Local Session "PENDING"
        val sessionId = crawlerDao.insertSession(
            CrawlSessionEntity(
                startUrl = url,
                depth = depth,
                outputPath = outputPath,
                status = "PENDING",
                startTime = System.currentTimeMillis()
            )
        )

        // 2. Start embedded Python crawl
        try {
            // Select User-Agent based on mode
            val userAgent = if (isMobileMode) {
                // iPhone 14 Pro Max UA
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            } else {
                // Standard Desktop Chrome UA
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            }
            
            // Convert categories to comma-separated string for Python
            val categoriesStr = if (scanCategories.isEmpty()) "all" else scanCategories.joinToString(",")
            
            val crawlId = crawlerBridge.startCrawl(url, depth, userAgent, categoriesStr)
            
            // Update local session with remote ID (Python crawl_id)
            crawlerDao.updateRemoteId(sessionId, crawlId)
            crawlerDao.updateStatus(sessionId, "RUNNING", System.currentTimeMillis())
            
            // Update output path to the actual crawl directory
            val actualOutputPath = crawlerBridge.getCrawlOutputDir(crawlId).absolutePath
            crawlerDao.updateOutputPath(sessionId, actualOutputPath)
            
        } catch (e: Exception) {
            e.printStackTrace()
            crawlerDao.updateStatus(sessionId, "ERROR: ${e.message}", System.currentTimeMillis())
        }

        return sessionId
    }

    suspend fun updateStatus(sessionId: Long, status: String) {
        crawlerDao.updateStatus(sessionId, status)
    }

    /**
     * Check status of a crawl by querying the embedded Python engine.
     * Updates all progress fields including current URL.
     */
    suspend fun checkStatus(sessionId: Long) {
        val session = crawlerDao.getSessionById(sessionId) ?: return
        if (session.remoteId == null) return
        
        try {
            val status = crawlerBridge.getStatus(session.remoteId)
            
            val normalizedStatus = when {
                status.isRunning -> "RUNNING"
                status.isCompleted -> "COMPLETED"
                status.isFailed -> "FAILED"
                status.status == "stopped" -> "STOPPED"
                else -> status.status.uppercase()
            }
            
            if (normalizedStatus != session.status) {
                crawlerDao.updateStatus(sessionId, normalizedStatus, System.currentTimeMillis())
            }
            
            // Update full progress with all new fields
            crawlerDao.updateFullProgress(
                id = sessionId,
                crawled = status.pagesCrawled,
                total = status.pagesTotal,
                queued = status.pagesQueued,
                currentUrl = status.currentUrl
            )
            
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    /**
     * Pause crawl - Not supported in embedded model, will stop instead.
     */
    suspend fun pauseCrawl(sessionId: Long) {
        // Embedded Python doesn't support pause, just stop
        stopCrawl(sessionId)
    }

    /**
     * Resume crawl - Not supported in embedded model.
     */
    suspend fun resumeCrawl(sessionId: Long) {
        // Would need to restart the crawl from scratch
        val session = crawlerDao.getSessionById(sessionId) ?: return
        // For now, just mark as error - user should start new crawl
        crawlerDao.updateStatus(sessionId, "RESUME_NOT_SUPPORTED")
    }

    /**
     * Stop a running crawl.
     */
    suspend fun stopCrawl(sessionId: Long) {
        val session = crawlerDao.getSessionById(sessionId) ?: return
        if (session.remoteId != null) {
            try {
                crawlerBridge.stopCrawl(session.remoteId)
                crawlerDao.updateStatus(sessionId, "STOPPED", System.currentTimeMillis())
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    /**
     * Get files generated by a crawl.
     */
    suspend fun getReport(sessionId: Long): SessionFiles? {
        val session = crawlerDao.getSessionById(sessionId) ?: return null
        if (session.remoteId == null) return null

        try {
            val files = crawlerBridge.getFiles(session.remoteId)
            val outputDir = crawlerBridge.getCrawlOutputDir(session.remoteId)
            
            // Map filenames to actual File objects
            val content = files.content.map { File(outputDir, "content/$it") }
            val images = files.images.map { File(outputDir, "images/$it") }
            val documents = files.documents.map { File(outputDir, "documents/$it") }
            val html = files.html.map { File(outputDir, "html/$it") }
            val stylesheets = files.stylesheets.map { File(outputDir, "stylesheets/$it") }
            val scripts = files.scripts.map { File(outputDir, "scripts/$it") }
            
            return SessionFiles(
                content = content,
                images = images,
                documents = documents,
                html = html,
                stylesheets = stylesheets,
                scripts = scripts
            )
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return null
    }

    /**
     * Get the full analysis report including SEO, security, SSL info.
     */
    suspend fun getAnalysisReport(sessionId: Long): AnalysisReport? {
        val session = crawlerDao.getSessionById(sessionId) ?: return null
        if (session.remoteId == null) return null

        return try {
            crawlerBridge.getAnalysisReport(session.remoteId)
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * Get content of a specific file.
     */
    suspend fun getFileContent(sessionId: Long, filename: String): String {
        val session = crawlerDao.getSessionById(sessionId) ?: return "Error: Session not found"
        if (session.remoteId == null) return "Error: Remote ID missing"

        return try {
            crawlerBridge.readContentFile(session.remoteId, filename)
        } catch (e: Exception) {
            "Error loading file: ${e.message}"
        }
    }

    /**
     * Get HTML source of a specific page.
     */
    suspend fun getHtmlContent(sessionId: Long, filename: String): String {
        val session = crawlerDao.getSessionById(sessionId) ?: return "Error: Session not found"
        if (session.remoteId == null) return "Error: Remote ID missing"

        return try {
            crawlerBridge.readHtmlFile(session.remoteId, filename)
        } catch (e: Exception) {
            "Error loading file: ${e.message}"
        }
    }

    suspend fun generateSitemap(sessionId: Long): String {
        val session = crawlerDao.getSessionById(sessionId) ?: return "{\"error\": \"Session not found\"}"
        if (session.remoteId == null) return "{\"error\": \"Remote ID missing\"}"
        return crawlerBridge.generateSitemap(session.remoteId)
    }

    suspend fun exportData(sessionId: Long, format: String): String {
        val session = crawlerDao.getSessionById(sessionId) ?: return "{\"error\": \"Session not found\"}"
        if (session.remoteId == null) return "{\"error\": \"Remote ID missing\"}"
        return crawlerBridge.exportData(session.remoteId, format)
    }
    
    suspend fun generatePdf(sessionId: Long): String {
        val session = crawlerDao.getSessionById(sessionId) ?: return "{\"error\": \"Session not found\"}"
        if (session.remoteId == null) return "{\"error\": \"Remote ID missing\"}"
        return crawlerBridge.generatePdf(session.remoteId)
    }

    suspend fun updateProgress(sessionId: Long, count: Int) {
        crawlerDao.updateProgress(sessionId, count)
    }

    suspend fun completeSession(sessionId: Long, success: Boolean) {
        val status = if (success) "COMPLETED" else "FAILED"
        crawlerDao.updateStatus(sessionId, status, System.currentTimeMillis())
    }
}

/**
 * Data class for session files with all asset types.
 */
data class SessionFiles(
    val content: List<File> = emptyList(),
    val images: List<File> = emptyList(),
    val documents: List<File> = emptyList(),
    val html: List<File> = emptyList(),
    val stylesheets: List<File> = emptyList(),
    val scripts: List<File> = emptyList()
) {
    val totalFiles: Int
        get() = content.size + images.size + documents.size + html.size + stylesheets.size + scripts.size
}
