package com.bitflow.finance.crawler

import java.io.File
import java.net.URI
import java.net.URL

object SpiderUtils {

    fun normalizeUrl(url: String): String {
        return try {
            val uri = URI(url)
            val normalized = uri.normalize()
            var result = normalized.toString()
            if (result.endsWith("/")) {
                result = result.substring(0, result.length - 1)
            }
            result
        } catch (e: Exception) {
            url
        }
    }

    fun getDomain(url: String): String {
        return try {
            val uri = URI(url)
            val domain = uri.host ?: ""
            if (domain.startsWith("www.")) domain.substring(4) else domain
        } catch (e: Exception) {
            ""
        }
    }

    fun getSafeFilename(url: String): String {
        return url.replace(Regex("[^a-zA-Z0-9.-]"), "_")
            .take(255) // Max filename length
    }
}
