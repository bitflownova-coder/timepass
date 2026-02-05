package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "crawl_sessions")
data class CrawlSessionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val startUrl: String,
    val status: String, // RUNNING, COMPLETED, FAILED, CANCELLED
    val startTime: Long,
    val endTime: Long? = null,
    val pagesCrawled: Int = 0,
    val outputPath: String,
    val depth: Int,
    val remoteId: String? = null // UUID from Python backend
)
