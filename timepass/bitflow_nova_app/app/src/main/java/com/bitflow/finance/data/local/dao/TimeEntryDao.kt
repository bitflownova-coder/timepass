package com.bitflow.finance.data.local.dao

import androidx.room.*
import com.bitflow.finance.data.local.entity.TimeEntryEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface TimeEntryDao {
    
    @Query("SELECT * FROM time_entries WHERE userId = :userId ORDER BY startTime DESC")
    fun getAllEntries(userId: String): Flow<List<TimeEntryEntity>>
    
    @Query("SELECT * FROM time_entries WHERE userId = :userId AND endTime IS NULL LIMIT 1")
    fun getActiveTimer(userId: String): Flow<TimeEntryEntity?>
    
    @Query("SELECT * FROM time_entries WHERE userId = :userId AND startTime >= :startOfDay AND startTime < :endOfDay ORDER BY startTime DESC")
    fun getEntriesForDay(userId: String, startOfDay: Long, endOfDay: Long): Flow<List<TimeEntryEntity>>
    
    @Query("SELECT * FROM time_entries WHERE userId = :userId AND startTime >= :startTime ORDER BY startTime DESC")
    fun getEntriesAfter(userId: String, startTime: Long): Flow<List<TimeEntryEntity>>
    
    @Query("SELECT * FROM time_entries WHERE userId = :userId AND clientId = :clientId ORDER BY startTime DESC")
    fun getEntriesForClient(userId: String, clientId: Long): Flow<List<TimeEntryEntity>>
    
    @Query("SELECT * FROM time_entries WHERE userId = :userId AND projectName = :projectName ORDER BY startTime DESC")
    fun getEntriesForProject(userId: String, projectName: String): Flow<List<TimeEntryEntity>>
    
    @Query("SELECT DISTINCT projectName FROM time_entries WHERE userId = :userId ORDER BY projectName ASC")
    fun getAllProjectNames(userId: String): Flow<List<String>>
    
    @Query("SELECT SUM(durationMinutes) FROM time_entries WHERE userId = :userId AND startTime >= :startTime AND endTime IS NOT NULL")
    fun getTotalMinutesAfter(userId: String, startTime: Long): Flow<Int?>
    
    @Query("SELECT SUM(durationMinutes * hourlyRate / 60.0) FROM time_entries WHERE userId = :userId AND clientId = :clientId AND endTime IS NOT NULL")
    fun getTotalEarningsForClient(userId: String, clientId: Long): Flow<Double?>
    
    @Query("""
        SELECT projectName, SUM(durationMinutes) as totalMinutes 
        FROM time_entries 
        WHERE userId = :userId AND startTime >= :startTime AND endTime IS NOT NULL
        GROUP BY projectName 
        ORDER BY totalMinutes DESC
    """)
    fun getProjectSummary(userId: String, startTime: Long): Flow<List<ProjectTimeSummary>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEntry(entry: TimeEntryEntity): Long
    
    @Update
    suspend fun updateEntry(entry: TimeEntryEntity)
    
    @Delete
    suspend fun deleteEntry(entry: TimeEntryEntity)
    
    @Query("DELETE FROM time_entries WHERE id = :id")
    suspend fun deleteById(id: Long)
}

data class ProjectTimeSummary(
    val projectName: String,
    val totalMinutes: Int
)
