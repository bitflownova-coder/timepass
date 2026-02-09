package com.bitflow.finance.ui.screens.dev_tools

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.TimeEntryEntity
import com.bitflow.finance.data.local.entity.QuickNoteEntity
import com.bitflow.finance.data.local.entity.PasswordHistoryEntity
import com.bitflow.finance.data.local.dao.ProjectTimeSummary
import com.bitflow.finance.data.repository.DevToolsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.*
import javax.inject.Inject

@HiltViewModel
class DevToolsViewModel @Inject constructor(
    private val repository: DevToolsRepository
) : ViewModel() {
    
    private val userId = "local_user"
    
    // ================== TIME TRACKER STATE ==================
    
    val allTimeEntries: StateFlow<List<TimeEntryEntity>> = repository.getAllTimeEntries(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val activeTimer: StateFlow<TimeEntryEntity?> = repository.getActiveTimer(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)
    
    val projectNames: StateFlow<List<String>> = repository.getAllProjectNames(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    private val _todayEntries = MutableStateFlow<List<TimeEntryEntity>>(emptyList())
    val todayEntries: StateFlow<List<TimeEntryEntity>> = _todayEntries.asStateFlow()
    
    private val _weekEntries = MutableStateFlow<List<TimeEntryEntity>>(emptyList())
    val weekEntries: StateFlow<List<TimeEntryEntity>> = _weekEntries.asStateFlow()
    
    private val _monthEntries = MutableStateFlow<List<TimeEntryEntity>>(emptyList())
    val monthEntries: StateFlow<List<TimeEntryEntity>> = _monthEntries.asStateFlow()
    
    init {
        loadTimeEntries()
    }
    
    private fun loadTimeEntries() {
        val calendar = Calendar.getInstance()
        
        // Today
        calendar.set(Calendar.HOUR_OF_DAY, 0)
        calendar.set(Calendar.MINUTE, 0)
        calendar.set(Calendar.SECOND, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        val startOfToday = calendar.timeInMillis
        
        calendar.add(Calendar.DAY_OF_YEAR, 1)
        val endOfToday = calendar.timeInMillis
        
        viewModelScope.launch {
            repository.getEntriesForDay(userId, startOfToday, endOfToday).collect {
                _todayEntries.value = it
            }
        }
        
        // Week
        calendar.timeInMillis = System.currentTimeMillis()
        calendar.set(Calendar.DAY_OF_WEEK, calendar.firstDayOfWeek)
        calendar.set(Calendar.HOUR_OF_DAY, 0)
        calendar.set(Calendar.MINUTE, 0)
        calendar.set(Calendar.SECOND, 0)
        val startOfWeek = calendar.timeInMillis
        
        viewModelScope.launch {
            repository.getEntriesAfter(userId, startOfWeek).collect {
                _weekEntries.value = it
            }
        }
        
        // Month
        calendar.timeInMillis = System.currentTimeMillis()
        calendar.set(Calendar.DAY_OF_MONTH, 1)
        calendar.set(Calendar.HOUR_OF_DAY, 0)
        calendar.set(Calendar.MINUTE, 0)
        calendar.set(Calendar.SECOND, 0)
        val startOfMonth = calendar.timeInMillis
        
        viewModelScope.launch {
            repository.getEntriesAfter(userId, startOfMonth).collect {
                _monthEntries.value = it
            }
        }
    }
    
    fun startTimer(projectName: String, taskDescription: String = "", hourlyRate: Double = 0.0, clientId: Long? = null, clientName: String = "", tags: String = "") {
        viewModelScope.launch {
            val entry = TimeEntryEntity(
                userId = userId,
                projectName = projectName,
                taskDescription = taskDescription,
                hourlyRate = hourlyRate,
                clientId = clientId,
                clientName = clientName,
                tags = tags,
                startTime = System.currentTimeMillis()
            )
            repository.insertTimeEntry(entry)
        }
    }
    
    fun stopTimer(entry: TimeEntryEntity) {
        viewModelScope.launch {
            val endTime = System.currentTimeMillis()
            val durationMinutes = ((endTime - entry.startTime) / 60000).toInt()
            val updated = entry.copy(
                endTime = endTime,
                durationMinutes = durationMinutes
            )
            repository.updateTimeEntry(updated)
        }
    }
    
    fun addManualEntry(
        projectName: String,
        taskDescription: String,
        startTime: Long,
        endTime: Long,
        hourlyRate: Double = 0.0,
        clientId: Long? = null,
        clientName: String = "",
        tags: String = "",
        notes: String = ""
    ) {
        viewModelScope.launch {
            val durationMinutes = ((endTime - startTime) / 60000).toInt()
            val entry = TimeEntryEntity(
                userId = userId,
                projectName = projectName,
                taskDescription = taskDescription,
                hourlyRate = hourlyRate,
                clientId = clientId,
                clientName = clientName,
                tags = tags,
                startTime = startTime,
                endTime = endTime,
                durationMinutes = durationMinutes,
                isManualEntry = true,
                notes = notes
            )
            repository.insertTimeEntry(entry)
        }
    }
    
    fun deleteTimeEntry(entry: TimeEntryEntity) {
        viewModelScope.launch {
            repository.deleteTimeEntry(entry)
        }
    }
    
    // ================== QUICK NOTES ==================
    
    val allNotes: StateFlow<List<QuickNoteEntity>> = repository.getAllNotes(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val folders: StateFlow<List<String>> = repository.getAllFolders(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()
    
    val filteredNotes: StateFlow<List<QuickNoteEntity>> = combine(
        allNotes,
        _searchQuery
    ) { notes, query ->
        if (query.isBlank()) notes
        else notes.filter { 
            it.title.contains(query, ignoreCase = true) || 
            it.content.contains(query, ignoreCase = true) 
        }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    fun setSearchQuery(query: String) {
        _searchQuery.value = query
    }
    
    fun addNote(title: String, content: String, folder: String = "default", color: Int = 0, tags: String = "") {
        viewModelScope.launch {
            val note = QuickNoteEntity(
                userId = userId,
                title = title,
                content = content,
                folder = folder,
                color = color,
                tags = tags
            )
            repository.insertNote(note)
        }
    }
    
    fun updateNote(note: QuickNoteEntity) {
        viewModelScope.launch {
            repository.updateNote(note.copy(updatedAt = System.currentTimeMillis()))
        }
    }
    
    fun deleteNote(note: QuickNoteEntity) {
        viewModelScope.launch {
            repository.deleteNote(note)
        }
    }
    
    fun toggleNotePin(note: QuickNoteEntity) {
        viewModelScope.launch {
            repository.updateNotePinStatus(note.id, !note.isPinned)
        }
    }
    
    // ================== PASSWORD HISTORY ==================
    
    val passwordHistory: StateFlow<List<PasswordHistoryEntity>> = repository.getRecentPasswords(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    fun savePasswordToHistory(password: String, length: Int, type: String, strength: String, label: String = "") {
        viewModelScope.launch {
            val entry = PasswordHistoryEntity(
                userId = userId,
                password = password,
                length = length,
                type = type,
                strength = strength,
                label = label
            )
            repository.insertPassword(entry)
            repository.trimPasswordHistory(userId, 50)
        }
    }
    
    fun deletePasswordFromHistory(entry: PasswordHistoryEntity) {
        viewModelScope.launch {
            repository.deletePassword(entry)
        }
    }
    
    fun clearPasswordHistory() {
        viewModelScope.launch {
            repository.clearPasswordHistory(userId)
        }
    }
}
