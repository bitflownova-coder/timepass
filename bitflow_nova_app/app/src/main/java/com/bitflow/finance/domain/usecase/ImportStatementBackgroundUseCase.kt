package com.bitflow.finance.domain.usecase

import com.bitflow.finance.data.parser.StatementParserFactory
import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.repository.AccountRepository
import com.bitflow.finance.domain.repository.TransactionRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.InputStream
import javax.inject.Inject

/**
 * Background import with progress tracking using smart parser
 */
class ImportStatementBackgroundUseCase @Inject constructor(
    private val transactionRepository: TransactionRepository,
    private val accountRepository: AccountRepository,
    private val detectDuplicates: DetectDuplicatesUseCase
) {
    
    suspend operator fun invoke(
        accountId: Long,
        inputStreamsWithNames: List<Pair<String, InputStream>>,
        onProgress: (ImportProgress) -> Unit
    ): BatchImportResult = withContext(Dispatchers.IO) {
        
        val results = mutableListOf<FileResult>()
        var totalProcessed = 0
        var totalImported = 0
        var totalSkipped = 0
        var totalDuplicates = 0
        
        inputStreamsWithNames.forEachIndexed { index, (fileName, stream) ->
            try {
                // Update progress
                onProgress(ImportProgress(
                    currentFile = index + 1,
                    totalFiles = inputStreamsWithNames.size,
                    fileName = fileName,
                    status = ProgressStatus.PARSING,
                    processedTransactions = 0,
                    totalTransactions = 0
                ))
                
                // Parse file using smart parser factory
                val parseResult = StatementParserFactory.parseStatement(stream)
                val parsedTransactions = parseResult.transactions
                val detectedBalance = parseResult.detectedCurrentBalance
                
                println("[BackgroundImport] File: $fileName - Parsed ${parsedTransactions.size} transactions")
                println("[BackgroundImport] File: $fileName - Detected balance: ₹$detectedBalance")
                
                onProgress(ImportProgress(
                    currentFile = index + 1,
                    totalFiles = inputStreamsWithNames.size,
                    fileName = fileName,
                    status = ProgressStatus.CHECKING_DUPLICATES,
                    processedTransactions = 0,
                    totalTransactions = parsedTransactions.size
                ))
                
                // Load existing transactions once for this file (major performance optimization)
                val existingTransactions = transactionRepository.getAllTransactionsForDeduplication(accountId)
                val existingKeys = existingTransactions.map { 
                    "${it.activityDate}|${it.amount}|${it.description}"
                }.toSet()
                
                // Process transactions with duplicate detection
                var fileImported = 0
                var fileSkipped = 0
                var fileDuplicates = 0
                val transactionsToInsert = mutableListOf<Activity>()
                
                // Convert all parsed transactions to Activity objects first
                val activities = parsedTransactions.map { parsed ->
                    Activity(
                        accountId = accountId,
                        activityDate = parsed.txnDate,
                        valueDate = parsed.valueDate,
                        description = parsed.description,
                        reference = parsed.reference,
                        amount = parsed.amount,
                        type = parsed.direction,
                        categoryId = null,
                        tags = emptyList(),
                        balanceAfterTxn = parsed.balanceAfterTxn
                    )
                }
                
                // Check duplicates using pre-loaded data (fast!)
                activities.forEachIndexed { txnIndex, activity ->
                    // Fast exact match check using set
                    val key = "${activity.activityDate}|${activity.amount}|${activity.description}"
                    val isDuplicate = existingKeys.contains(key)
                    
                    if (!isDuplicate) {
                        transactionsToInsert.add(activity)
                        fileImported++
                    } else {
                        fileDuplicates++
                    }
                    
                    // Update progress every 50 transactions (reduced UI updates for speed)
                    if (txnIndex % 50 == 0) {
                        onProgress(ImportProgress(
                            currentFile = index + 1,
                            totalFiles = inputStreamsWithNames.size,
                            fileName = fileName,
                            status = ProgressStatus.IMPORTING,
                            processedTransactions = txnIndex + 1,
                            totalTransactions = parsedTransactions.size
                        ))
                    }
                }
                
                // Insert transactions
                if (transactionsToInsert.isNotEmpty()) {
                    transactionRepository.insertTransactions(transactionsToInsert)
                    // Update account balance using the detected balance from parser
                    updateAccountBalance(accountId, detectedBalance)
                }
                
                totalProcessed += parsedTransactions.size
                totalImported += fileImported
                totalSkipped += fileSkipped
                totalDuplicates += fileDuplicates
                
                results.add(
                    FileResult(
                        fileName = fileName,
                        success = true,
                        parsedCount = parsedTransactions.size,
                        importedCount = fileImported,
                        skippedCount = fileSkipped,
                        duplicatesCount = fileDuplicates,
                        errorMessage = null
                    )
                )
                
                onProgress(ImportProgress(
                    currentFile = index + 1,
                    totalFiles = inputStreamsWithNames.size,
                    fileName = fileName,
                    status = ProgressStatus.COMPLETED,
                    processedTransactions = parsedTransactions.size,
                    totalTransactions = parsedTransactions.size
                ))
                
            } catch (e: Exception) {
                println("[BackgroundImport] Error processing $fileName: ${e.message}")
                e.printStackTrace()
                
                results.add(
                    FileResult(
                        fileName = fileName,
                        success = false,
                        parsedCount = 0,
                        importedCount = 0,
                        skippedCount = 0,
                        duplicatesCount = 0,
                        errorMessage = e.message ?: "Unknown error"
                    )
                )
                
                onProgress(ImportProgress(
                    currentFile = index + 1,
                    totalFiles = inputStreamsWithNames.size,
                    fileName = fileName,
                    status = ProgressStatus.FAILED,
                    processedTransactions = 0,
                    totalTransactions = 0,
                    errorMessage = e.message
                ))
            }
        }
        
        BatchImportResult(
            totalFiles = inputStreamsWithNames.size,
            successfulFiles = results.count { it.success },
            failedFiles = results.count { !it.success },
            totalProcessed = totalProcessed,
            totalImported = totalImported,
            totalSkipped = totalSkipped,
            totalDuplicates = totalDuplicates,
            fileResults = results
        )
    }
    
    /**
     * Update account balance using the detected balance from the parser
     * 
     * The parser has already done the smart work of detecting file order
     * (ascending vs descending) and extracting the correct current balance.
     * 
     * @param accountId The account to update
     * @param detectedBalance The current balance detected by the smart parser
     */
    private suspend fun updateAccountBalance(accountId: Long, detectedBalance: Double) {
        try {
            println("[BackgroundImport] === BALANCE UPDATE ===")
            println("[BackgroundImport] Account ID: $accountId")
            
            var currentBalance = detectedBalance
            
            // Only use fallback if parser didn't detect a valid balance
            if (currentBalance <= 0.0) {
                println("[BackgroundImport] ⚠️ Parser detected balance is 0 or negative, using fallback...")
                
                // Try database
                currentBalance = transactionRepository.getLatestTransactionBalance(accountId) ?: 0.0
                if (currentBalance > 0.0) {
                    println("[BackgroundImport] ✓ Using database latest balance: ₹$currentBalance")
                } else {
                    // Final fallback: Calculate
                    val account = accountRepository.getAccountById(accountId) ?: return
                    currentBalance = transactionRepository.calculateAccountBalance(accountId, account.initialBalance)
                    println("[BackgroundImport] ⚠️ Fallback to calculation: ₹$currentBalance (initial: ₹${account.initialBalance})")
                }
            } else {
                println("[BackgroundImport] ✓ Using parser-detected balance: ₹$currentBalance")
            }
            
            // Update account balance
            accountRepository.updateBalance(accountId, currentBalance)
            println("[BackgroundImport] ✅ Account balance updated to: ₹$currentBalance")
            
        } catch (e: Exception) {
            println("[BackgroundImport] ❌ Error updating account balance: ${e.message}")
            e.printStackTrace()
        }
    }
    
    data class ImportProgress(
        val currentFile: Int,
        val totalFiles: Int,
        val fileName: String,
        val status: ProgressStatus,
        val processedTransactions: Int,
        val totalTransactions: Int,
        val errorMessage: String? = null
    )
    
    enum class ProgressStatus {
        PARSING,
        CHECKING_DUPLICATES,
        IMPORTING,
        COMPLETED,
        FAILED
    }
    
    data class BatchImportResult(
        val totalFiles: Int,
        val successfulFiles: Int,
        val failedFiles: Int,
        val totalProcessed: Int,
        val totalImported: Int,
        val totalSkipped: Int,
        val totalDuplicates: Int,
        val fileResults: List<FileResult>
    )
    
    data class FileResult(
        val fileName: String,
        val success: Boolean,
        val parsedCount: Int,
        val importedCount: Int,
        val skippedCount: Int,
        val duplicatesCount: Int,
        val errorMessage: String?
    )
}
