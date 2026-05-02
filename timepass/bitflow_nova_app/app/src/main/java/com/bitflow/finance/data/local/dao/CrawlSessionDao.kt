package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.bitflow.finance.data.local.entity.CrawlSessionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface CrawlSessionDao {
    @Query("SELECT * FROM crawl_sessions ORDER BY startTime DESC")
    fun getAllSessions(): Flow<List<CrawlSessionEntity>>

    @Query("SELECT * FROM crawl_sessions WHERE id = :id")
    suspend fun getSessionById(id: Long): CrawlSessionEntity?

    @Query("SELECT * FROM crawl_sessions WHERE id = :id")
    fun getSessionFlow(id: Long): Flow<CrawlSessionEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSession(session: CrawlSessionEntity): Long

    @Query("UPDATE crawl_sessions SET status = :status, endTime = :endTime WHERE id = :id")
    suspend fun updateStatus(id: Long, status: String, endTime: Long? = null)

    @Query("UPDATE crawl_sessions SET pagesCrawled = :count WHERE id = :id")
    suspend fun updateProgress(id: Long, count: Int)

    @Query("UPDATE crawl_sessions SET pagesCrawled = :crawled, pagesTotal = :total, pagesQueued = :queued, currentUrl = :currentUrl WHERE id = :id")
    suspend fun updateFullProgress(id: Long, crawled: Int, total: Int, queued: Int, currentUrl: String)

    @Query("UPDATE crawl_sessions SET remoteId = :remoteId WHERE id = :id")
    suspend fun updateRemoteId(id: Long, remoteId: String)

    @Query("UPDATE crawl_sessions SET outputPath = :outputPath WHERE id = :id")
    suspend fun updateOutputPath(id: Long, outputPath: String)

    @Query("DELETE FROM crawl_sessions")
    suspend fun clearAll()
}
