package com.bitflow.finance.data.parser

import com.bitflow.finance.domain.model.ActivityType
import java.io.BufferedReader
import java.io.InputStream
import java.io.InputStreamReader
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException

/**
 * Parser for Bitflow-style bank statements
 * 
 * Expected columns:
 * - Date / Transaction Date / Txn Date
 * - Particulars / Description / Narration
 * - Withdrawal / Debit / Dr.
 * - Deposit / Credit / Cr.
 * - Balance
 */
class BitflowStatementParser : BankStatementParser {
    
    companion object {
        // Header keywords that identify Bitflow format
        private val HEADER_KEYWORDS = listOf(
            "particulars" to "withdrawal",
            "particulars" to "deposit",
            "description" to "withdrawal",
            "narration" to "withdrawal"
        )
        
        // Date formats
        private val DATE_FORMATS = listOf(
            DateTimeFormatter.ofPattern("dd MMM yyyy"),
            DateTimeFormatter.ofPattern("dd/MM/yyyy"),
            DateTimeFormatter.ofPattern("dd-MM-yyyy"),
            DateTimeFormatter.ofPattern("yyyy-MM-dd"),
            DateTimeFormatter.ofPattern("dd MMM yy")
        )
    }
    
    override fun getParserName(): String = "Bitflow Statement Parser"
    
    override fun parse(inputStream: InputStream): ParseResult {
        val reader = BufferedReader(InputStreamReader(inputStream))
        val lines = reader.readLines()
        
        println("[Bitflow Parser] Scanning ${lines.size} lines for header...")
        
        // Step 1: Find header row
        val headerRowIndex = findHeaderRow(lines)
        if (headerRowIndex == -1) {
            throw StatementParsingException("Bitflow format header not found in first 40 lines")
        }
        
        println("[Bitflow Parser] Found header at row $headerRowIndex")
        
        // Step 2: Parse header to get column indices
        val headerLine = lines[headerRowIndex]
        val columnMapping = parseHeader(headerLine)
        
        println("[Bitflow Parser] Column mapping: $columnMapping")
        
        // Step 3: Parse data rows
        val transactions = mutableListOf<ParsedTransaction>()
        
        for (i in (headerRowIndex + 1) until lines.size) {
            try {
                val line = lines[i].trim()
                if (line.isEmpty()) continue
                
                val transaction = parseDataRow(line, columnMapping)
                if (transaction != null) {
                    transactions.add(transaction)
                }
            } catch (e: Exception) {
                println("[Bitflow Parser] Skipping row ${i + 1}: ${e.message}")
            }
        }
        
        println("[Bitflow Parser] Parsed ${transactions.size} transactions")
        
        // Step 4: SMART BALANCE DETECTION
        val detectedBalance = detectCurrentBalance(transactions)
        println("[Bitflow Parser] Detected current balance: ₹$detectedBalance")
        
        return ParseResult(transactions, detectedBalance)
    }
    
    /**
     * Smart balance detection: Detect file order and extract current balance
     * 
     * Logic:
     * - If first transaction date > last transaction date: File is DESCENDING (newest first)
     *   → Current balance is in FIRST row
     * - If first transaction date < last transaction date: File is ASCENDING (oldest first)
     *   → Current balance is in LAST row
     */
    private fun detectCurrentBalance(transactions: List<ParsedTransaction>): Double {
        if (transactions.isEmpty()) return 0.0
        
        // Get transactions with valid balance data
        val withBalance = transactions.filter { it.balanceAfterTxn > 0.0 }
        if (withBalance.isEmpty()) return 0.0
        
        if (withBalance.size == 1) {
            return withBalance.first().balanceAfterTxn
        }
        
        // Compare first and last transaction dates
        val firstDate = withBalance.first().txnDate
        val lastDate = withBalance.last().txnDate
        
        return when {
            firstDate.isAfter(lastDate) -> {
                // DESCENDING: Newest transaction first → Current balance is FIRST row
                val balance = withBalance.first().balanceAfterTxn
                println("[Bitflow Parser] 📊 File order: DESCENDING (newest first)")
                println("[Bitflow Parser] ✓ Using FIRST row balance: ₹$balance")
                balance
            }
            firstDate.isBefore(lastDate) -> {
                // ASCENDING: Oldest transaction first → Current balance is LAST row
                val balance = withBalance.last().balanceAfterTxn
                println("[Bitflow Parser] 📊 File order: ASCENDING (oldest first)")
                println("[Bitflow Parser] ✓ Using LAST row balance: ₹$balance")
                balance
            }
            else -> {
                // Unclear ordering (all same date?) - use latest by balance or first available
                val balance = withBalance.maxByOrNull { it.balanceAfterTxn }?.balanceAfterTxn ?: 0.0
                println("[Bitflow Parser] 📊 File order: UNCLEAR (same dates)")
                println("[Bitflow Parser] ⚠️ Using highest balance: ₹$balance")
                balance
            }
        }
    }
    
    private fun findHeaderRow(lines: List<String>): Int {
        val searchLimit = minOf(40, lines.size)
        
        for (i in 0 until searchLimit) {
            val line = lines[i].lowercase()
            
            // Check if this line contains Bitflow header keywords
            for ((keyword1, keyword2) in HEADER_KEYWORDS) {
                if (line.contains(keyword1) && line.contains(keyword2)) {
                    return i
                }
            }
        }
        
        return -1
    }
    
    private fun parseHeader(headerLine: String): ColumnMapping {
        val columns = CsvUtils.splitCsvLine(headerLine).map { it.trim() }
        
        var dateIndex = -1
        var particularsIndex = -1
        var withdrawalIndex = -1
        var depositIndex = -1
        var balanceIndex = -1
        var referenceIndex = -1
        
        for ((index, col) in columns.withIndex()) {
            val colLower = col.lowercase().trim()
            
            when {
                dateIndex == -1 && (colLower.contains("date") && 
                    !colLower.contains("value")) -> dateIndex = index
                    
                particularsIndex == -1 && (colLower.contains("particulars") || 
                    colLower.contains("description") || 
                    colLower.contains("narration") ||
                    colLower.contains("remark")) -> particularsIndex = index
                    
                referenceIndex == -1 && (colLower.contains("ref") || 
                    colLower.contains("cheque") || 
                    colLower.contains("chq") ||
                    colLower.contains("transaction id")) -> referenceIndex = index
                    
                withdrawalIndex == -1 && (colLower.contains("withdrawal") || 
                    (colLower.contains("debit") && !colLower.contains("credit")) ||
                    colLower == "dr." || colLower == "dr" ||
                    colLower.contains("paid")) -> withdrawalIndex = index
                    
                depositIndex == -1 && (colLower.contains("deposit") || 
                    (colLower.contains("credit") && !colLower.contains("debit")) ||
                    colLower == "cr." || colLower == "cr" ||
                    colLower.contains("received")) -> depositIndex = index
                    
                balanceIndex == -1 && (colLower.contains("balance") || 
                    colLower.contains("closing balance")) -> balanceIndex = index
            }
        }
        
        if (dateIndex == -1 || particularsIndex == -1) {
            throw StatementParsingException("Required columns (Date, Particulars) not found")
        }
        
        if (withdrawalIndex == -1 && depositIndex == -1) {
            throw StatementParsingException("Amount columns (Withdrawal/Deposit) not found")
        }
        
        return ColumnMapping(
            dateIndex = dateIndex,
            particularsIndex = particularsIndex,
            withdrawalIndex = withdrawalIndex,
            depositIndex = depositIndex,
            balanceIndex = balanceIndex,
            referenceIndex = referenceIndex
        )
    }
    
    private fun parseDataRow(line: String, mapping: ColumnMapping): ParsedTransaction? {
        val columns = CsvUtils.splitCsvLine(line).map { it.trim() }
        
        // Ensure we have enough columns
        if (columns.size <= mapping.dateIndex || columns.size <= mapping.particularsIndex) {
            return null
        }
        
        // Parse date
        val dateStr = columns[mapping.dateIndex]
        if (dateStr.isBlank() || dateStr == "-" || dateStr.equals("date", ignoreCase = true)) {
            return null
        }
        
        val txnDate = parseDate(dateStr) ?: return null
        
        // Parse particulars/description
        val particulars = columns[mapping.particularsIndex].trim()
        if (particulars.isBlank() || particulars.equals("particulars", ignoreCase = true)) {
            return null
        }
        
        // Parse reference (optional)
        val reference = if (mapping.referenceIndex != -1 && columns.size > mapping.referenceIndex) {
            columns[mapping.referenceIndex].takeIf { it.isNotBlank() && it != "-" }
        } else null
        
        // Parse amounts
        var withdrawalAmount = 0.0
        var depositAmount = 0.0
        
        if (mapping.withdrawalIndex != -1 && columns.size > mapping.withdrawalIndex) {
            withdrawalAmount = parseAmount(columns[mapping.withdrawalIndex])
        }
        
        if (mapping.depositIndex != -1 && columns.size > mapping.depositIndex) {
            depositAmount = parseAmount(columns[mapping.depositIndex])
        }
        
        // Determine transaction type and amount
        val (amount, type) = when {
            withdrawalAmount > 0.0 -> withdrawalAmount to ActivityType.EXPENSE
            depositAmount > 0.0 -> depositAmount to ActivityType.INCOME
            else -> return null // Skip rows with no amount
        }
        
        // Parse balance (optional)
        val balance = if (mapping.balanceIndex != -1 && columns.size > mapping.balanceIndex) {
            parseAmount(columns[mapping.balanceIndex])
        } else 0.0
        
        return ParsedTransaction(
            txnDate = txnDate,
            valueDate = txnDate,
            description = particulars,
            reference = reference,
            amount = amount,
            direction = type,
            balanceAfterTxn = balance
        )
    }
    
    private fun parseDate(dateStr: String): LocalDate? {
        for (formatter in DATE_FORMATS) {
            try {
                return LocalDate.parse(dateStr, formatter)
            } catch (e: DateTimeParseException) {
                // Try next format
            }
        }
        
        println("[Bitflow Parser] Failed to parse date: $dateStr")
        return null
    }
    
    private fun parseAmount(amountStr: String): Double {
        if (amountStr.isBlank() || amountStr == "-" || amountStr == "0" || amountStr == "0.00") {
            return 0.0
        }
        
        return try {
            // Remove commas, currency symbols, and spaces
            amountStr.replace(",", "")
                .replace("₹", "")
                .replace("INR", "")
                .replace(" ", "")
                .trim()
                .toDoubleOrNull() ?: 0.0
        } catch (e: Exception) {
            0.0
        }
    }
    
    private data class ColumnMapping(
        val dateIndex: Int,
        val particularsIndex: Int,
        val withdrawalIndex: Int,
        val depositIndex: Int,
        val balanceIndex: Int,
        val referenceIndex: Int
    )
}
