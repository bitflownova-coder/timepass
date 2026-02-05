package com.bitflow.finance.crawler

import org.jsoup.Jsoup
import org.jsoup.nodes.Element
import org.jsoup.nodes.TextNode
import java.net.URI
import java.net.URL

object CrawlerUtils {

    fun normalizeUrl(url: String): String {
        return try {
            val uri = URI(url)
            val scheme = uri.scheme ?: "https"
            val host = uri.host ?: return url
            val path = uri.path ?: ""
            // Reconstruct without query or fragment
            "$scheme://$host$path".trimEnd('/')
        } catch (e: Exception) {
            url
        }
    }

    fun getDomain(url: String): String {
        return try {
            val host = URL(url).host
            // Simple domain extraction (not perfect TLD extraction but sufficient for recursion limits)
            host.removePrefix("www.")
        } catch (e: Exception) {
            ""
        }
    }

    fun getSafeFilename(url: String): String {
        return try {
            val path = URL(url).path.trim('/')
            if (path.isEmpty()) return "index"
            path.replace(Regex("[^a-zA-Z0-9]"), "_")
        } catch (e: Exception) {
            "index"
        }
    }

    fun htmlToMarkdown(html: String): String {
        val doc = Jsoup.parse(html)
        val sb = StringBuilder()
        
        // Remove unwanted elements
        doc.select("script, style, nav, footer, iframe, noscript").remove()
        
        // Traverse body
        traverse(doc.body(), sb)
        
        return sb.toString().trim()
    }

    private fun traverse(element: Element, sb: StringBuilder) {
        for (node in element.childNodes()) {
            if (node is TextNode) {
                val text = node.text().trim()
                if (text.isNotEmpty()) {
                    sb.append(text).append(" ")
                }
            } else if (node is Element) {
                when (node.tagName()) {
                    "h1" -> {
                        sb.append("\n\n# ")
                        traverse(node, sb)
                        sb.append("\n\n")
                    }
                    "h2" -> {
                        sb.append("\n\n## ")
                        traverse(node, sb)
                        sb.append("\n\n")
                    }
                    "h3" -> {
                        sb.append("\n\n### ")
                        traverse(node, sb)
                        sb.append("\n\n")
                    }
                    "p" -> {
                        sb.append("\n\n")
                        traverse(node, sb)
                        sb.append("\n\n")
                    }
                    "ul", "ol" -> {
                        sb.append("\n")
                        traverse(node, sb)
                        sb.append("\n")
                    }
                    "li" -> {
                        sb.append("\n- ")
                        traverse(node, sb)
                    }
                    "a" -> {
                        val href = node.attr("abs:href")
                        sb.append("[")
                        traverse(node, sb)
                        sb.append("]($href)")
                    }
                    "strong", "b" -> {
                        sb.append("**")
                        traverse(node, sb)
                        sb.append("**")
                    }
                    "em", "i" -> {
                        sb.append("*")
                        traverse(node, sb)
                        sb.append("*")
                    }
                    "br" -> sb.append("\n")
                    else -> traverse(node, sb)
                }
            }
        }
    }
}
