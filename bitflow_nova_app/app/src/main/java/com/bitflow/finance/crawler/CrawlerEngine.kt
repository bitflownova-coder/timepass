package com.bitflow.finance.crawler

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.jsoup.Jsoup
import java.io.File
import java.io.FileOutputStream
import java.security.MessageDigest
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit

class CrawlerEngine(private val context: Context) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()
        
    private val visited = ConcurrentHashMap.newKeySet<String>()
    @Volatile private var isStopped = false
    @Volatile private var isPaused = false
    @Volatile private var pagesCrawled = 0

    suspend fun start(sessionId: Long, startUrl: String, maxDepth: Int, onLog: (String) -> Unit, onProgress: (Int) -> Unit) {
        isStopped = false
        isPaused = false
        pagesCrawled = 0
        visited.clear()

        try {
            val normalizedStartUrl = CrawlerUtils.normalizeUrl(startUrl)
            val domain = CrawlerUtils.getDomain(normalizedStartUrl)
            
            // Use session-specific folder: .../crawler_output/<sessionId>/
            val baseDir = File(context.getExternalFilesDir(null), "crawler_output/$sessionId")
            val contentDir = File(baseDir, "content").apply { mkdirs() }
            val imagesDir = File(baseDir, "images").apply { mkdirs() }
            val docsDir = File(baseDir, "documents").apply { mkdirs() }

            onLog("Output Directory: ${baseDir.absolutePath}")
            
            crawlRecursive(normalizedStartUrl, 0, maxDepth, domain, contentDir, imagesDir, docsDir, onLog, onProgress)
            
            if (isStopped) {
                onLog("Crawl stopped.")
            } else {
                onLog("Crawl complete. Total pages: $pagesCrawled")
            }
        } catch (e: Exception) {
            onLog("Crawl interrupted by error: ${e.message}")
            Log.e("CrawlerEngine", "Crawl failed", e)
            if (pagesCrawled > 0) {
                 onLog("Partial crawl results saved ($pagesCrawled pages).")
            } else {
                throw e
            }
        }
    }

    fun pause() {
        isPaused = true
    }

    fun resume() {
        isPaused = false
    }

    fun stop() {
        isStopped = true
    }

    private suspend fun crawlRecursive(
        url: String, 
        depth: Int, 
        maxDepth: Int, 
        domain: String, 
        contentDir: File,
        imagesDir: File,
        docsDir: File,
        onLog: (String) -> Unit,
        onProgress: (Int) -> Unit
    ) {
        if (isStopped) return
        while (isPaused) {
            if (isStopped) return
            kotlinx.coroutines.delay(500)
        }
        
        if (depth > maxDepth) return
        
        if (visited.contains(url)) return
        visited.add(url)
        
        pagesCrawled++
        onProgress(pagesCrawled)

        onLog("Visiting [$depth]: $url")

        try {
            val html = withContext(Dispatchers.IO) {
                fetchHtml(url)
            }

            if (html.isEmpty()) return

            val doc = Jsoup.parse(html, url) // Pass base URL for absolute resolution
            val title = doc.title()
            val description = doc.select("meta[name=description]").attr("content")
            
            // 1. Convert to Markdown
            val markdownBody = CrawlerUtils.htmlToMarkdown(doc.body().html())
            val fullContent = "# $title\n\n**Description:** $description\n\n**URL:** $url\n\n---\n\n$markdownBody"

            // Save Content - Use Hash for safe filename
            val safeName = getSafeFilename(url)
            val file = File(contentDir, "$safeName.md")
            withContext(Dispatchers.IO) {
                file.writeText(fullContent)
            }

            // 2. Extract and Download Assets
            val images = doc.select("img[src]")
            for (img in images) {
                if (isStopped) break
                val src = img.attr("abs:src")
                if (src.isNotEmpty()) {
                    downloadAsset(src, imagesDir, "img")
                }
            }

            val docExtensions = listOf(".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".zip", ".csv")
            val links = doc.select("a[href]")
            
            for (link in links) {
                if (isStopped) break
                val absUrl = link.attr("abs:href")
                if (absUrl.isEmpty()) continue

                // Check if it is a document
                val isDoc = docExtensions.any { absUrl.lowercase().endsWith(it) }
                if (isDoc) {
                    downloadAsset(absUrl, docsDir, "doc")
                } 
                // Else recurse if valid link
                else if (depth < maxDepth) {
                    val normalizedLink = CrawlerUtils.normalizeUrl(absUrl)
                    if (CrawlerUtils.getDomain(normalizedLink) == domain) {
                        crawlRecursive(normalizedLink, depth + 1, maxDepth, domain, contentDir, imagesDir, docsDir, onLog, onProgress)
                    }
                }
            }

        } catch (e: Exception) {
            onLog("Error visiting $url: ${e.message}")
            Log.e("Crawler", "Error visiting $url", e)
        }
    }

    private suspend fun downloadAsset(url: String, dir: File, type: String) {
        val extension = url.substringAfterLast('.', "")
            .takeIf { it.length in 2..4 } ?: if (type == "img") "jpg" else "dat"
            
        val safeName = getSafeFilename(url)
        val filename = "$safeName.$extension"
        val file = File(dir, filename)
        
        if (file.exists()) return

        try {
            withContext(Dispatchers.IO) {
                val request = Request.Builder().url(url).build()
                client.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        response.body?.byteStream()?.use { input ->
                            FileOutputStream(file).use { output ->
                                input.copyTo(output)
                            }
                        }
                    }
                }
            }
        } catch (e: Exception) {
            // Ignore download failures
        }
    }

    private fun fetchHtml(url: String): String {
        return try {
            val request = Request.Builder().url(url)
                .header("User-Agent", "BitflowCrawler/1.0")
                .build()
            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    response.body?.string() ?: ""
                } else {
                    ""
                }
            }
        } catch (e: Exception) {
            ""
        }
    }
    
    private fun getSafeFilename(url: String): String {
        return try {
            val digest = MessageDigest.getInstance("MD5")
            digest.update(url.toByteArray())
            val messageDigest = digest.digest()
            val hexString = StringBuilder()
            for (message in messageDigest) {
                var h = Integer.toHexString(0xFF and message.toInt())
                while (h.length < 2) h = "0$h"
                hexString.append(h)
            }
            hexString.toString() + "_" + System.currentTimeMillis() % 1000
        } catch (e: Exception) {
            "file_${System.currentTimeMillis()}"
        }
    }
}
