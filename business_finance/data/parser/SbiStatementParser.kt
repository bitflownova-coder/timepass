package com.bitflow.finance.data.parser

import com.bitflow.finance.domain.model.ActivityType
import java.io.BufferedReader
import java.io.InputStream
import java.io.InputStreamReader
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException

/**
 * Parser for SBI (State Bank of India) bank statements
 * 
 * Expected columns:
 * - Trans Date / Txn Date / Transaction Date
 * - Description / Narration / Description/Narration
 * - Debit(Dr.) / Debit / Dr. / Withdrawal
 * - Credit(Cr.) / Credit / Cr. / Deposit
 * - Balance
 */
class SbiStatementParser : BankStatementParser {
    
    companion object {
        // Header keywords that identify SBI format
        private val HEADER_KEYWORDS = listOf(
            "trans date" to "debit",
            "txn date" to "debit",
            "transaction date" to "dr.",
            "transaction date" to "dr",
            "date" to "debit(dr.)",
            "date" to "debit",
            "txn date" to "dr.",
            "txn date" to "dr"
        )
        
        // Date formats commonly used by SBI
        // Note: MMM is case-insensitive and matches 3-letter month abbreviations (Jan, Feb, etc.)
        private val DATE_FORMATS = listOf(
            DateTimeFormatter.ofPattern("d MMM yyyy").withLocale(java.util.Locale.ENGLISH),  // "1 Aug 2024"
            DateTimeFormatter.ofPattern("dd MMM yyyy").withLocale(java.util.Locale.ENGLISH), // "01 Aug 2024"
            DateTimeFormatter.ofPattern("d/M/yyyy"),     // "1/8/2024"
            DateTimeFormatter.ofPattern("dd/MM/yyyy"),   // "01/08/2024"
            DateTimeFormatter.ofPattern("d-M-yyyy"),     // "1-8-2024"
            DateTimeFormatter.ofPattern("dd-MM-yyyy"),   // "01-08-2024"
            DateTimeFormatter.ofPattern("d MMM yy").withLocale(java.util.Locale.ENGLISH),    // "1 Aug 24"
            DateTimeFormatter.ofPattern("dd MMM yy").withLocale(java.util.Locale.ENGLISH),   // "01 Aug 24"
            DateTimeFormatter.ofPattern("yyyy-MM-dd")    // "2024-08-01"
        )
    }
    
    override fun getParserName(): String = "SBI Statement Parser"
    
    override fun parse(inputStream: InputStream): ParseResult {
        val reader = BufferedReader(InputStreamReader(inputStream))
        val lines = reader.readLines()
        
        println("[SBI Parser] Scanning ${lines.size} lines for header...")
        
        // Step 1: Find header row
        val headerRowIndex = findHeaderRow(lines)
        if (headerRowIndex == -1) {
            throw StatementParsingException("SBI format header not found in first 40 lines")
        }
        
        println("[SBI Parser] Found header at row $headerRowIndex")
        
        // Step 2: Parse header to get column indices
        val headerLine = lines[headerRowIndex]
        val columnMapping = parseHeader(headerLine)
        
        println("[SBI Parser] Column mapping: $columnMapping")
        
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
                println("[SBI Parser] Skipping row ${i + 1}: ${e.message}")
            }
        }
        
        println("[SBI Parser] Parsed ${transactions.size} transactions")
        
        // Step 4: SMART BALANCE DETECTION
        val detectedBalance = detectCurrentBalance(transactions)
        println("[SBI Parser] Detected current balance: ₹$detectedBalance")
        
        return ParseResult(transactions, detectedBalance)
    }
    
    /**
     * Smart balance detection: Find the latest date and pick the correct balance based on file order.
     * 
     * Logic:
     * 1. Find the latest date in the file.
     * 2. Get all transactions on that date.
     * 3. Determine if file is Descending (Newest First) or Ascending (Oldest First) based on dates.
     * 4. Pick the appropriate row (First or Last) from the latest date's transactions.
     */
    private fun detectCurrentBalance(transactions: List<ParsedTransaction>): Double {
        if (transactions.isEmpty()) return 0.0
        
        // 1. Filter out "Opening Balance" rows to ensure we don't pick them
        val validTransactions = transactions.filter { 
            it.balanceAfterTxn > 0.0 && 
            !it.description.contains("Opening Balance", ignoreCase = true) &&
            !it.description.contains("Brought Forward", ignoreCase = true) &&
            !it.description.contains("B/F", ignoreCase = true)
        }
        
        if (validTransactions.isEmpty()) {
            return transactions.lastOrNull { it.balanceAfterTxn > 0.0 }?.balanceAfterTxn ?: 0.0
        }

        // 2. Find the latest date among all valid transactions
        val latestDate = validTransactions.maxOf { it.txnDate }
        
        // 3. Get all transactions that happened on that latest date
        val txnsOnLatestDate = validTransactions.filter { it.txnDate == latestDate }
        
        // 4. Determine file order using the FULL list of transactions (Dates only)
        // If the first transaction is newer than the last, it's Descending.
        val firstDate = transactions.first().txnDate
        val lastDate = transactions.last().txnDate
        val isDescending = firstDate.isAfter(lastDate)
        
        val finalTransaction = if (isDescending) {
            // Descending (Newest First): The "latest" transaction is the FIRST one in the list
            txnsOnLatestDate.first()
        } else {
            // Ascending (Oldest First) or Single Day: The "latest" transaction is the LAST one in the list
            txnsOnLatestDate.last()
        }
        
        println("[SBI Parser] Latest date found: $latestDate")
        println("[SBI Parser] File order detected (by date): ${if (isDescending) "DESCENDING" else "ASCENDING"}")
        println("[SBI Parser] ✓ Selected balance from latest transaction: ₹${finalTransaction.balanceAfterTxn}")
        
        return finalTransaction.balanceAfterTxn
    }

    /**
     * Removed complex math-based order detection as per user request.
     * Relying strictly on Date comparison and List position.
     */
    
    private fun findHeaderRow(lines: List<String>): Int {
        val searchLimit = minOf(40, lines.size)
        
        println("[SBI Parser] Searching for header in first $searchLimit lines...")
        
        for (i in 0 until searchLimit) {
            val line = lines[i].lowercase()
            
            // Print first 20 lines for debugging
            if (i < 20) {
                println("[SBI Parser] Line $i: ${line.take(100)}")
            }
            
            // Check if this line contains SBI header keywords
            for ((keyword1, keyword2) in HEADER_KEYWORDS) {
                if (line.contains(keyword1) && line.contains(keyword2)) {
                    println("[SBI Parser] Found header match at line $i with keywords: [$keyword1, $keyword2]")
                    return i
                }
            }
        }
        
        println("[SBI Parser] No header found matching SBI keywords")
        return -1
    }
    
    private fun parseHeader(headerLine: String): ColumnMapping {
        val columns = CsvUtils.splitCsvLine(headerLine).map { it.trim() }
        
        println("[SBI Parser] Header columns (${columns.size}): ${columns.joinToString(" | ")}")
        
        var dateIndex = -1
        var descriptionIndex = -1
        var debitIndex = -1
        var creditIndex = -1
        var balanceIndex = -1
        var referenceIndex = -1
        
        for ((index, col) in columns.withIndex()) {
            val colLower = col.lowercase().trim()
            
            when {
                dateIndex == -1 && (colLower.contains("trans date") || 
                    colLower.contains("txn date") || 
                    colLower.contains("transaction date") ||
                    colLower.contains("txn posted date") ||
                    colLower == "date") -> dateIndex = index
                    
                descriptionIndex == -1 && (colLower.contains("description") || 
                    colLower.contains("narration") || 
                    colLower.contains("particulars") ||
                    colLower.contains("remark")) -> descriptionIndex = index
                    
                referenceIndex == -1 && (colLower.contains("ref") || 
                    colLower.contains("cheque") || 
                    colLower.contains("chq") ||
                    colLower.contains("transaction id")) -> referenceIndex = index
                    
                debitIndex == -1 && (colLower.contains("debit") || 
                    colLower.contains("dr.") || 
                    colLower == "dr" ||
                    colLower.contains("withdrawal") ||
                    colLower.contains("paid")) -> debitIndex = index
                    
                creditIndex == -1 && (colLower.contains("credit") || 
                    colLower.contains("cr.") || 
                    colLower == "cr" ||
                    colLower.contains("deposit") ||
                    colLower.contains("received")) -> creditIndex = index
                    
                balanceIndex == -1 && (colLower.contains("balance") || 
                    colLower.contains("closing balance")) -> balanceIndex = index
            }
        }
        
        if (dateIndex == -1 || descriptionIndex == -1) {
            throw StatementParsingException("Required columns (Date, Description) not found")
        }
        
        if (debitIndex == -1 && creditIndex == -1) {
            throw StatementParsingException("Amount columns (Debit/Credit) not found")
        }
        
        return ColumnMapping(
            dateIndex = dateIndex,
            descriptionIndex = descriptionIndex,
            debitIndex = debitIndex,
            creditIndex = creditIndex,
            balanceIndex = balanceIndex,
            referenceIndex = referenceIndex
        )
    }
    
    private var debugRowCount = 0
    
    private fun parseDataRow(line: String, mapping: ColumnMapping): ParsedTransaction? {
        val columns = CsvUtils.splitCsvLine(line).map { it.trim() }
        
        // Debug: Print first 3 data rows to see column structure
        if (debugRowCount < 3) {
            println("[SBI Parser] Data row #$debugRowCount has ${columns.size} columns:")
            columns.forEachIndexed { i, col -> 
                val label = when(i) {
                    mapping.dateIndex -> "DATE"
                    mapping.descriptionIndex -> "DESC"
                    mapping.debitIndex -> "DEBIT"
                    mapping.creditIndex -> "CREDIT"
                    mapping.balanceIndex -> "BALANCE"
                    else -> ""
                }
                println("[SBI Parser]   Col[$i]$label: '$col'")
            }
            debugRowCount++
        }
        
        // Ensure we have enough columns
        if (columns.size <= mapping.dateIndex || columns.size <= mapping.descriptionIndex) {
            return null
        }
        
        // Parse date
        val dateStr = columns[mapping.dateIndex]
        if (dateStr.isBlank() || dateStr == "-" || dateStr.equals("date", ignoreCase = true)) {
            return null
        }
        
        val txnDate = parseDate(dateStr) ?: return null
        
        // Parse description
        val description = columns[mapping.descriptionIndex].trim()
        if (description.isBlank() || description.equals("description", ignoreCase = true)) {
            return null
        }
        
        // Parse reference (optional)
        val reference = if (mapping.referenceIndex != -1 && columns.size > mapping.referenceIndex) {
            columns[mapping.referenceIndex].takeIf { it.isNotBlank() && it != "-" }
        } else null
        
        // Parse amounts
        var debitAmount = 0.0
        var creditAmount = 0.0
        
        val debitStr = if (mapping.debitIndex != -1 && columns.size > mapping.debitIndex) {
            columns[mapping.debitIndex]
        } else ""
        
        val creditStr = if (mapping.creditIndex != -1 && columns.size > mapping.creditIndex) {
            columns[mapping.creditIndex]
        } else ""
        
        debitAmount = parseAmount(debitStr)
        creditAmount = parseAmount(creditStr)
        
        // Debug logging for first few transactions
        if (debitAmount > 0 || creditAmount > 0) {
            println("[SBI Parser] Row: debit='$debitStr'($debitAmount), credit='$creditStr'($creditAmount), desc='${description.take(30)}'")
        }
        
        // Determine transaction type and amount
        val (amount, type) = when {
            debitAmount > 0.0 -> debitAmount to ActivityType.EXPENSE
            creditAmount > 0.0 -> creditAmount to ActivityType.INCOME
            else -> return null // Skip rows with no amount
        }
        
        // Parse balance (optional)
        val balance = if (mapping.balanceIndex != -1 && columns.size > mapping.balanceIndex) {
            parseAmount(columns[mapping.balanceIndex])
        } else 0.0
        
        return ParsedTransaction(
            txnDate = txnDate,
            valueDate = txnDate,
            description = description,
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
        
        println("[SBI Parser] Failed to parse date: $dateStr")
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
        val descriptionIndex: Int,
        val debitIndex: Int,
        val creditIndex: Int,
        val balanceIndex: Int,
        val referenceIndex: Int
    )
}
