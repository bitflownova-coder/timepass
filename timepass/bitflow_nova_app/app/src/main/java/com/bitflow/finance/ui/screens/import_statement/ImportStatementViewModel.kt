package com.bitflow.finance.ui.screens.import_statement

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.Account
import com.bitflow.finance.domain.repository.AccountRepository
import com.bitflow.finance.domain.usecase.ImportResult
import com.bitflow.finance.domain.usecase.ImportStatementUseCase
import com.bitflow.finance.domain.usecase.ImportStatementBackgroundUseCase
import com.bitflow.finance.domain.usecase.ValidateStatementUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ImportStatementViewModel @Inject constructor(
    private val importStatementUseCase: ImportStatementUseCase,
    private val backgroundImportUseCase: ImportStatementBackgroundUseCase,
    private val validateStatementUseCase: ValidateStatementUseCase,
    private val accountRepository: AccountRepository,
    @ApplicationContext private val context: Context
) : ViewModel() {

    private val _uiState = MutableStateFlow(ImportUiState())
    val uiState: StateFlow<ImportUiState> = _uiState.asStateFlow()
    
    private val _importProgress = MutableStateFlow<ImportStatementBackgroundUseCase.ImportProgress?>(null)
    val importProgress: StateFlow<ImportStatementBackgroundUseCase.ImportProgress?> = _importProgress.asStateFlow()

    init {
        loadAccounts()
    }

    private fun loadAccounts() {
        viewModelScope.launch {
            accountRepository.getAllAccounts().collect { accounts ->
                _uiState.value = _uiState.value.copy(accounts = accounts)
            }
        }
    }

    fun selectAccount(account: Account) {
        _uiState.value = _uiState.value.copy(selectedAccount = account)
    }

    fun importFiles(uris: List<Uri>) {
        val selectedAcc = _uiState.value.selectedAccount
        println("[ImportViewModel] Selected account: ${selectedAcc?.id} - ${selectedAcc?.name}")
        val accountId = selectedAcc?.id ?: run {
            println("[ImportViewModel] ERROR: No account selected!")
            _uiState.value = _uiState.value.copy(error = "Please select an account first")
            return
        }
        
        // Validate files first
        val validationErrors = mutableListOf<String>()
        uris.forEach { uri ->
            val fileName = getFileNameFromUri(uri)
            val fileSize = getFileSizeFromUri(uri)
            
            val validation = validateStatementUseCase(fileName, fileSize)
            if (!validation.isValid) {
                validationErrors.add("$fileName: ${validation.errorMessage}")
            }
        }
        
        if (validationErrors.isNotEmpty()) {
            _uiState.value = _uiState.value.copy(
                error = "Validation failed:\n${validationErrors.joinToString("\n")}"
            )
            return
        }
        
        _uiState.value = _uiState.value.copy(isLoading = true)

        viewModelScope.launch {
            try {
                println("[ImportViewModel] Opening ${uris.size} files")
                
                // Get file names from URIs and create streams
                val inputStreamsWithNames = uris.mapNotNull { uri ->
                    val fileName = getFileNameFromUri(uri)
                    val stream = context.contentResolver.openInputStream(uri)
                    if (stream != null) {
                        println("[ImportViewModel] Opened: $fileName")
                        fileName to stream
                    } else {
                        println("[ImportViewModel] Failed to open: $fileName")
                        null
                    }
                }
                
                if (inputStreamsWithNames.isNotEmpty()) {
                    println("[ImportViewModel] Starting background import for ${inputStreamsWithNames.size} files")
                    
                    val result = backgroundImportUseCase(
                        accountId = accountId,
                        inputStreamsWithNames = inputStreamsWithNames,
                        onProgress = { progress ->
                            _importProgress.value = progress
                        }
                    )
                    
                    println("[ImportViewModel] Import complete: ${result.totalImported} imported, ${result.totalDuplicates} duplicates")
                    
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        batchResult = result,
                        importResult = null // Clear old single-file result
                    )
                    
                    // Close streams
                    inputStreamsWithNames.forEach { (_, stream) -> 
                        try { stream.close() } catch (e: Exception) {}
                    }
                } else {
                    println("[ImportViewModel] ERROR: Could not open any files")
                    _uiState.value = _uiState.value.copy(isLoading = false, error = "Could not open files")
                }
            } catch (e: Exception) {
                println("[ImportViewModel] ERROR: ${e.message}")
                e.printStackTrace()
                _uiState.value = _uiState.value.copy(isLoading = false, error = e.message)
            }
        }
    }
    
    fun clearProgress() {
        _importProgress.value = null
    }
    
    fun clearResults() {
        _uiState.value = _uiState.value.copy(
            importResult = null,
            batchResult = null,
            error = null
        )
    }
    
    private fun getFileSizeFromUri(uri: Uri): Long {
        return try {
            context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                val sizeIndex = cursor.getColumnIndex(android.provider.OpenableColumns.SIZE)
                cursor.moveToFirst()
                cursor.getLong(sizeIndex)
            } ?: 0L
        } catch (e: Exception) {
            0L
        }
    }

    private fun getFileNameFromUri(uri: Uri): String {
        return try {
            context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                val nameIndex = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                cursor.moveToFirst()
                cursor.getString(nameIndex)
            } ?: uri.lastPathSegment ?: "Unknown file"
        } catch (e: Exception) {
            uri.lastPathSegment ?: "Unknown file"
        }
    }
}

data class ImportUiState(
    val accounts: List<Account> = emptyList(),
    val selectedAccount: Account? = null,
    val isLoading: Boolean = false,
    val importResult: ImportResult? = null,
    val batchResult: ImportStatementBackgroundUseCase.BatchImportResult? = null,
    val error: String? = null
)
