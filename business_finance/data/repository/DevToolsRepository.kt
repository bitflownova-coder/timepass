package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.TimeEntryDao
import com.bitflow.finance.data.local.dao.QuickNoteDao
import com.bitflow.finance.data.local.dao.PasswordHistoryDao
import com.bitflow.finance.data.local.dao.ProjectTimeSummary
import com.bitflow.finance.data.local.entity.TimeEntryEntity
import com.bitflow.finance.data.local.entity.QuickNoteEntity
import com.bitflow.finance.data.local.entity.PasswordHistoryEntity
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DevToolsRepository @Inject constructor(
    private val timeEntryDao: TimeEntryDao,
    private val quickNoteDao: QuickNoteDao,
    private val passwordHistoryDao: PasswordHistoryDao
) {
    // ================== TIME TRACKER ==================
    
    fun getAllTimeEntries(userId: String): Flow<List<TimeEntryEntity>> = 
        timeEntryDao.getAllEntries(userId)
    
    fun getActiveTimer(userId: String): Flow<TimeEntryEntity?> = 
        timeEntryDao.getActiveTimer(userId)
    
    fun getEntriesForDay(userId: String, startOfDay: Long, endOfDay: Long): Flow<List<TimeEntryEntity>> = 
        timeEntryDao.getEntriesForDay(userId, startOfDay, endOfDay)
    
    fun getEntriesAfter(userId: String, startTime: Long): Flow<List<TimeEntryEntity>> = 
        timeEntryDao.getEntriesAfter(userId, startTime)
    
    fun getEntriesForClient(userId: String, clientId: Long): Flow<List<TimeEntryEntity>> = 
        timeEntryDao.getEntriesForClient(userId, clientId)
    
    fun getEntriesForProject(userId: String, projectName: String): Flow<List<TimeEntryEntity>> = 
        timeEntryDao.getEntriesForProject(userId, projectName)
    
    fun getAllProjectNames(userId: String): Flow<List<String>> = 
        timeEntryDao.getAllProjectNames(userId)
    
    fun getTotalMinutesAfter(userId: String, startTime: Long): Flow<Int?> = 
        timeEntryDao.getTotalMinutesAfter(userId, startTime)
    
    fun getTotalEarningsForClient(userId: String, clientId: Long): Flow<Double?> = 
        timeEntryDao.getTotalEarningsForClient(userId, clientId)
    
    fun getProjectSummary(userId: String, startTime: Long): Flow<List<ProjectTimeSummary>> = 
        timeEntryDao.getProjectSummary(userId, startTime)
    
    suspend fun insertTimeEntry(entry: TimeEntryEntity): Long = 
        timeEntryDao.insertEntry(entry)
    
    suspend fun updateTimeEntry(entry: TimeEntryEntity) = 
        timeEntryDao.updateEntry(entry)
    
    suspend fun deleteTimeEntry(entry: TimeEntryEntity) = 
        timeEntryDao.deleteEntry(entry)
    
    suspend fun deleteTimeEntryById(id: Long) = 
        timeEntryDao.deleteById(id)
    
    // ================== QUICK NOTES ==================
    
    fun getAllNotes(userId: String): Flow<List<QuickNoteEntity>> = 
        quickNoteDao.getAllNotes(userId)
    
    fun getPinnedNotes(userId: String): Flow<List<QuickNoteEntity>> = 
        quickNoteDao.getPinnedNotes(userId)
    
    fun getNotesByFolder(userId: String, folder: String): Flow<List<QuickNoteEntity>> = 
        quickNoteDao.getNotesByFolder(userId, folder)
    
    fun searchNotes(userId: String, query: String): Flow<List<QuickNoteEntity>> = 
        quickNoteDao.searchNotes(userId, query)
    
    fun getAllFolders(userId: String): Flow<List<String>> = 
        quickNoteDao.getAllFolders(userId)
    
    suspend fun getNoteById(id: Long): QuickNoteEntity? = 
        quickNoteDao.getNoteById(id)
    
    suspend fun insertNote(note: QuickNoteEntity): Long = 
        quickNoteDao.insertNote(note)
    
    suspend fun updateNote(note: QuickNoteEntity) = 
        quickNoteDao.updateNote(note)
    
    suspend fun deleteNote(note: QuickNoteEntity) = 
        quickNoteDao.deleteNote(note)
    
    suspend fun deleteNoteById(id: Long) = 
        quickNoteDao.deleteById(id)
    
    suspend fun updateNotePinStatus(id: Long, pinned: Boolean) = 
        quickNoteDao.updatePinStatus(id, pinned)
    
    // ================== PASSWORD HISTORY ==================
    
    fun getRecentPasswords(userId: String, limit: Int = 50): Flow<List<PasswordHistoryEntity>> = 
        passwordHistoryDao.getRecentPasswords(userId, limit)
    
    fun getAllPasswords(userId: String): Flow<List<PasswordHistoryEntity>> = 
        passwordHistoryDao.getAllPasswords(userId)
    
    suspend fun insertPassword(password: PasswordHistoryEntity): Long = 
        passwordHistoryDao.insertPassword(password)
    
    suspend fun deletePassword(password: PasswordHistoryEntity) = 
        passwordHistoryDao.deletePassword(password)
    
    suspend fun deletePasswordById(id: Long) = 
        passwordHistoryDao.deleteById(id)
    
    suspend fun clearPasswordHistory(userId: String) = 
        passwordHistoryDao.clearHistory(userId)
    
    suspend fun trimPasswordHistory(userId: String, keepCount: Int = 50) = 
        passwordHistoryDao.trimHistory(userId, keepCount)
}
