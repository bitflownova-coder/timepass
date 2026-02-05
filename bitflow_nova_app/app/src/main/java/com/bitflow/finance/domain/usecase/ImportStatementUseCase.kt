package com.bitflow.finance.domain.usecase

import com.bitflow.finance.data.parser.StatementParser
import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.repository.TransactionRepository
import java.io.InputStream
import javax.inject.Inject

class ImportStatementUseCase @Inject constructor(
    private val parser: StatementParser,
    private val transactionRepository: TransactionRepository,
    private val accountRepository: com.bitflow.finance.domain.repository.AccountRepository
) {
    suspend operator fun invoke(accountId: Long, inputStream: InputStream): ImportResult {
        println("[ImportUseCase] Starting import for account $accountId")
        val parsedTransactions = parser.parse(inputStream)
        println("[ImportUseCase] Parser returned ${parsedTransactions.size} transactions")
        return processTransactions(accountId, parsedTransactions)
    }

    suspend fun importWithFileNames(accountId: Long, inputStreamsWithNames: List<Pair<String, InputStream>>): ImportResult {
        println("[ImportUseCase] Starting batch import for account $accountId with ${inputStreamsWithNames.size} files")
        var totalImported = 0
        var totalSkipped = 0
        val fileResults = mutableListOf<FileImportResult>()
        
        inputStreamsWithNames.forEach { (fileName, stream) ->
            try {
                println("[ImportUseCase] Processing file: $fileName")
                val parsedTransactions = parser.parse(stream)
                println("[ImportUseCase] Parser returned ${parsedTransactions.size} transactions for $fileName")
                val result = processTransactions(accountId, parsedTransactions)
                println("[ImportUseCase] Processed $fileName: imported=${result.importedCount}, skipped=${result.skippedCount}")
                totalImported += result.importedCount
                totalSkipped += result.skippedCount
                
                fileResults.add(
                    FileImportResult(
                        fileName = fileName,
                        success = true,
                        importedCount = result.importedCount,
                        skippedCount = result.skippedCount,
                        errorMessage = null
                    )
                )
            } catch (e: Exception) {
                println("[ImportUseCase] Error processing $fileName: ${e.message}")
                fileResults.add(
                    FileImportResult(
                        fileName = fileName,
                        success = false,
                        importedCount = 0,
                        skippedCount = 0,
                        errorMessage = e.message ?: "Unknown error"
                    )
                )
            }
        }
        
        println("[ImportUseCase] Batch import complete: imported=$totalImported, skipped=$totalSkipped")
        return ImportResult(totalImported, totalSkipped, fileResults)
    }

    private suspend fun processTransactions(accountId: Long, parsedTransactions: List<com.bitflow.finance.data.parser.ParsedTransaction>): ImportResult {
        println("[ImportUseCase] Processing ${parsedTransactions.size} parsed transactions")
        var importedCount = 0
        var skippedCount = 0

        // Performance optimization: Get all existing transactions once
        val existingTransactions = transactionRepository.getAllTransactionsForDeduplication(accountId)
        
        // Create lookup set for fast duplicate detection: "date|amount|description"
        val existingKeys = existingTransactions.map { 
            "${it.activityDate}|${it.amount}|${it.description}"
        }.toSet()
        println("[ImportUseCase] Existing transactions: ${existingKeys.size}")

        val transactionsToInsert = mutableListOf<Activity>()

        for (parsed in parsedTransactions) {
            // Fast duplicate check using in-memory set
            val key = "${parsed.txnDate}|${parsed.amount}|${parsed.description}"
            
            if (key !in existingKeys) {
                transactionsToInsert.add(
                    Activity(
                        accountId = accountId,
                        activityDate = parsed.txnDate,
                        valueDate = parsed.valueDate,
                        description = parsed.description,
                        reference = parsed.reference,
                        amount = parsed.amount,
                        type = parsed.direction,
                        categoryId = null, // Auto-categorization logic can go here
                        tags = emptyList()
                    )
                )
                importedCount++
            } else {
                skippedCount++
            }
        }

        println("[ImportUseCase] Inserting ${transactionsToInsert.size} new transactions")
        if (transactionsToInsert.isNotEmpty()) {
            transactionRepository.insertTransactions(transactionsToInsert)
            
            // Update account balance based on new transactions
            updateAccountBalance(accountId)
        }

        return ImportResult(importedCount, skippedCount)
    }
    
    private suspend fun updateAccountBalance(accountId: Long) {
        try {
            val account = accountRepository.getAccountById(accountId) ?: return
            
            // Optimized: Use direct calculation query from repository
            val calculatedBalance = transactionRepository.calculateAccountBalance(accountId, account.initialBalance)
            
            println("[ImportUseCase] Updating account $accountId balance: ${account.currentBalance} -> $calculatedBalance")
            accountRepository.updateBalance(accountId, calculatedBalance)
        } catch (e: Exception) {
            println("[ImportUseCase] Error updating account balance: ${e.message}")
        }
    }
}

data class ImportResult(
    val importedCount: Int,
    val skippedCount: Int,
    val fileResults: List<FileImportResult> = emptyList()
)

data class FileImportResult(
    val fileName: String,
    val success: Boolean,
    val importedCount: Int,
    val skippedCount: Int,
    val errorMessage: String?
)
