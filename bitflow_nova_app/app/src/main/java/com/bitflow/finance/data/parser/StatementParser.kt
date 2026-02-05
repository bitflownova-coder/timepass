package com.bitflow.finance.data.parser

import com.bitflow.finance.domain.model.ActivityType
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.text.PDFTextStripper
import org.apache.poi.ss.usermodel.CellType
import org.apache.poi.ss.usermodel.DateUtil
import org.apache.poi.ss.usermodel.WorkbookFactory
import java.io.BufferedReader
import java.io.ByteArrayInputStream
import java.io.InputStream
import java.io.InputStreamReader
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale
import android.content.Context

data class ParsedTransaction(
    val txnDate: LocalDate,
    val valueDate: LocalDate?,
    val description: String,
    val reference: String?,
    val amount: Double,
    val direction: ActivityType,
    val balanceAfterTxn: Double
)

/**
 * Result of parsing a bank statement
 * @param transactions List of parsed transactions
 * @param detectedCurrentBalance The current account balance extracted from the statement
 *        (uses smart logic to detect ascending vs descending file order)
 */
data class ParseResult(
    val transactions: List<ParsedTransaction>,
    val detectedCurrentBalance: Double
)

interface StatementParser {
    suspend fun parse(inputStream: InputStream): List<ParsedTransaction>
    fun initialize(context: Context)
}

class UniversalStatementParser : StatementParser {
    
    companion object {
        // Maximum file size to prevent OutOfMemory crashes on low-end devices
        // 10MB is a reasonable limit for bank statements (most are < 2MB)
        private const val MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 // 10 MB
    }
    
    private var isInitialized = false
    
    override fun initialize(context: Context) {
        if (!isInitialized) {
            PDFBoxResourceLoader.init(context)
            isInitialized = true
        }
    }

    override suspend fun parse(inputStream: InputStream): List<ParsedTransaction> {
        // Read stream into byte array to allow multiple parsing attempts
        // Note: This is required for file type detection and PDF parsing
        val bytes = inputStream.readBytes()
        
        // Prevent OutOfMemory crash on low-end devices with large files
        if (bytes.size > MAX_FILE_SIZE_BYTES) {
            println("[Parser] File too large: ${bytes.size} bytes (max: $MAX_FILE_SIZE_BYTES). Aborting.")
            return emptyList()
        }
        println("[Parser] Read ${bytes.size} bytes from input stream")
        
        // Detect file type
        val fileType = detectFileType(bytes)
        println("[Parser] Detected file type: $fileType")
        
        return when (fileType) {
            FileType.PDF -> {
                try {
                    println("[Parser] Attempting PDF parsing...")
                    val pdfStream = ByteArrayInputStream(bytes)
                    val result = parsePdf(pdfStream)
                    println("[Parser] PDF parsing succeeded: ${result.size} transactions")
                    result
                } catch (e: Exception) {
                    println("[Parser] PDF parsing failed: ${e.message}")
                    e.printStackTrace()
                    emptyList()
                }
            }
            FileType.EXCEL -> {
                try {
                    println("[Parser] Attempting Excel parsing...")
                    val excelStream = ByteArrayInputStream(bytes)
                    val result = parseExcel(excelStream)
                    println("[Parser] Excel parsing succeeded: ${result.size} transactions")
                    result
                } catch (e: Exception) {
                    println("[Parser] Excel parsing failed: ${e.javaClass.simpleName} - ${e.message}")
                    e.printStackTrace()
                    println("[Parser] Trying CSV fallback...")
                    try {
                        val csvStream = ByteArrayInputStream(bytes)
                        parseCsv(csvStream)
                    } catch (csvE: Exception) {
                        println("[Parser] CSV fallback also failed: ${csvE.message}")
                        emptyList()
                    }
                }
            }
            FileType.CSV -> {
                println("[Parser] Attempting CSV/TSV parsing...")
                val csvStream = ByteArrayInputStream(bytes)
                val result = parseCsv(csvStream)
                println("[Parser] CSV parsing completed: ${result.size} transactions")
                result
            }
        }
    }
    
    private enum class FileType {
        PDF, EXCEL, CSV
    }
    
    private fun detectFileType(bytes: ByteArray): FileType {
        if (bytes.size < 8) return FileType.CSV
        
        // Check for PDF signature: %PDF
        if (bytes[0] == 0x25.toByte() && bytes[1] == 0x50.toByte() && 
            bytes[2] == 0x44.toByte() && bytes[3] == 0x46.toByte()) {
            return FileType.PDF
        }
        
        // Check for Excel 2007+ (XLSX) signature: PK (zip format)
        if (bytes[0] == 0x50.toByte() && bytes[1] == 0x4B.toByte()) {
            return FileType.EXCEL
        }
        
        // Check for Excel 97-2003 (XLS) signature: D0 CF 11 E0 A1 B1 1A E1
        if (bytes.size >= 8 &&
            bytes[0] == 0xD0.toByte() && bytes[1] == 0xCF.toByte() &&
            bytes[2] == 0x11.toByte() && bytes[3] == 0xE0.toByte()) {
            return FileType.EXCEL
        }
        
        return FileType.CSV
    }
    
    /**
     * Parse PDF bank statements
     * Supports: HDFC, ICICI, SBI, Axis, Kotak and other Indian banks
     */
    private fun parsePdf(inputStream: InputStream): List<ParsedTransaction> {
        val transactions = mutableListOf<ParsedTransaction>()
        
        try {
            val document = PDDocument.load(inputStream)
            val stripper = PDFTextStripper()
            val text = stripper.getText(document)
            document.close()
            
            println("[PDF] Extracted ${text.length} characters")
            
            // Parse text line by line
            val lines = text.lines()
            
            // Common Indian bank PDF patterns
            // Format examples:
            // HDFC: "DD/MM/YYYY  Description  Ref  Dr Amount  Cr Amount  Balance"
            // ICICI: "DD MMM YYYY  Narration  Cheque  Withdrawal  Deposit  Balance"
            // SBI: "DD MMM YY  Description  Ref  Debit  Credit  Balance"
            
            var inTransactionSection = false
            val datePatterns = listOf(
                DateTimeFormatter.ofPattern("dd/MM/yyyy", Locale.ENGLISH),
                DateTimeFormatter.ofPattern("dd-MM-yyyy", Locale.ENGLISH),
                DateTimeFormatter.ofPattern("dd MMM yyyy", Locale.ENGLISH),
                DateTimeFormatter.ofPattern("dd-MMM-yyyy", Locale.ENGLISH),
                DateTimeFormatter.ofPattern("dd MMM yy", Locale.ENGLISH),
                DateTimeFormatter.ofPattern("dd-MMM-yy", Locale.ENGLISH)
            )
            
            for (line in lines) {
                val trimmed = line.trim()
                if (trimmed.isEmpty()) continue
                
                // Skip header lines
                if (trimmed.contains("Statement", ignoreCase = true) ||
                    trimmed.contains("Account Number", ignoreCase = true) ||
                    trimmed.contains("Customer", ignoreCase = true)) {
                    continue
                }
                
                // Detect transaction section start
                if (trimmed.contains("Date", ignoreCase = true) && 
                    (trimmed.contains("Debit", ignoreCase = true) || 
                     trimmed.contains("Withdrawal", ignoreCase = true) ||
                     trimmed.contains("Credit", ignoreCase = true))) {
                    inTransactionSection = true
                    continue
                }
                
                if (!inTransactionSection) continue
                
                // Try to parse transaction line
                val parsed = parseTransactionLine(trimmed, datePatterns)
                if (parsed != null) {
                    transactions.add(parsed)
                }
            }
            
            println("[PDF] Parsed ${transactions.size} transactions")
        } catch (e: Exception) {
            println("[PDF] Error: ${e.message}")
            e.printStackTrace()
        }
        
        return transactions
    }
    
    /**
     * Parse a single transaction line from PDF text
     */
    private fun parseTransactionLine(line: String, datePatterns: List<DateTimeFormatter>): ParsedTransaction? {
        try {
            // Split by one or more spaces (more flexible for PDFs with tight layouts)
            val parts = line.split(Regex("\\s+"))
            if (parts.size < 3) return null
            
            // Try to find date in first few parts
            var txnDate: LocalDate? = null
            var startIdx = 0
            
            for (i in 0 until minOf(3, parts.size)) {
                for (formatter in datePatterns) {
                    try {
                        txnDate = LocalDate.parse(parts[i].trim(), formatter)
                        startIdx = i + 1
                        break
                    } catch (e: Exception) {
                        // Try next format
                    }
                }
                if (txnDate != null) break
            }
            
            if (txnDate == null) return null
            
            // Extract amounts (look for numbers with commas/dots)
            val amountPattern = Regex("[0-9,]+\\.?[0-9]*")
            val amounts = parts.mapNotNull { part ->
                val cleaned = part.replace(",", "")
                amountPattern.find(cleaned)?.value?.toDoubleOrNull()
            }.filter { it > 0 }
            
            if (amounts.isEmpty()) return null
            
            // Description is usually after date and before amounts
            val description = parts.getOrNull(startIdx)?.trim() ?: "Transaction"
            
            // Determine debit/credit
            // Usually: Date | Description | Debit | Credit | Balance
            // Or: Date | Description | Withdrawal | Deposit | Balance
            val isDebit = amounts.size >= 2 && amounts[0] > 0
            val amount = amounts[0]
            val balance = amounts.lastOrNull() ?: 0.0
            
            return ParsedTransaction(
                txnDate = txnDate,
                valueDate = null,
                description = description,
                reference = null,
                amount = amount,
                direction = if (isDebit) ActivityType.EXPENSE else ActivityType.INCOME,
                balanceAfterTxn = balance
            )
        } catch (e: Exception) {
            return null
        }
    }

    private fun parseExcel(inputStream: InputStream): List<ParsedTransaction> {
        println("[Excel] parseExcel called")
        val transactions = mutableListOf<ParsedTransaction>()
        
        try {
            println("[Excel] Creating workbook...")
            val workbook = WorkbookFactory.create(inputStream)
            println("[Excel] Workbook loaded successfully, sheets: ${workbook.numberOfSheets}")
            
            val sheet = workbook.getSheetAt(0)
            println("[Excel] Got sheet: ${sheet.sheetName}")
            println("[Excel] Physical rows: ${sheet.physicalNumberOfRows}")
            println("[Excel] First row num: ${sheet.firstRowNum}, Last row num: ${sheet.lastRowNum}")
            
            var isHeaderFound = false
            var dateIndex = -1
            var valueDateIndex = -1
            var descIndex = -1
            var refIndex = -1
            var debitIndex = -1
            var creditIndex = -1
            var balanceIndex = -1
            var amountIndex = -1 // For files with single Amount column
            var typeIndex = -1    // For files with Type column (Dr/Cr)

            val dateFormatter = DateTimeFormatter.ofPattern("dd-MMM-yy", Locale.ENGLISH)

            var rowCount = 0
            for (row in sheet) {
                rowCount++
                println("[Excel] Processing row $rowCount, cells: ${row.physicalNumberOfCells}")
                
                val cells = row.map { cell ->
                    when (cell.cellType) {
                        CellType.STRING -> cell.stringCellValue.trim()
                        CellType.NUMERIC -> {
                            if (DateUtil.isCellDateFormatted(cell)) {
                                cell.localDateTimeCellValue.toLocalDate().format(dateFormatter)
                            } else {
                                cell.numericCellValue.toString()
                            }
                        }
                        else -> ""
                    }
                }
                
                println("[Excel] Row $rowCount mapped cells: $cells")

                if (!isHeaderFound) {
                    println("[Excel] Checking row for headers: $cells")
                
                // Check for date column (more flexible matching)
                val hasDate = cells.any { cell ->
                    cell.contains("Date", ignoreCase = true) && 
                    !cell.contains("Value Date", ignoreCase = true) // Exclude "Value Date" from primary date check
                }
                
                // Check for description column
                val hasDesc = cells.any { it.contains("Description", ignoreCase = true) || 
                    it.contains("Narration", ignoreCase = true) || 
                    it.contains("Particulars", ignoreCase = true) }
                
                // Check for amount columns (Debit/Credit or Withdrawal/Deposit)
                val hasAmount = cells.any { 
                    it.contains("Debit", ignoreCase = true) || 
                    it.contains("Credit", ignoreCase = true) ||
                    it.contains("Withdrawal", ignoreCase = true) ||
                    it.contains("Deposit", ignoreCase = true)
                }

                if (hasDate && hasDesc && hasAmount) {
                    isHeaderFound = true
                    println("[Excel] ✓ Header row found at row $rowCount")
                    
                    // Find date column (exclude Value Date)
                    dateIndex = cells.indexOfFirst { cell ->
                        (cell.contains("Trans Date", ignoreCase = true) ||
                         cell.contains("Txn Date", ignoreCase = true) || 
                         cell.contains("Transaction Date", ignoreCase = true) ||
                         (cell.contains("Date", ignoreCase = true) && 
                          !cell.contains("Value", ignoreCase = true)))
                    }
                    valueDateIndex = cells.indexOfFirst { cell ->
                        cell.contains("Value Date", ignoreCase = true) ||
                        cell.contains("Value Dt", ignoreCase = true)
                    }
                    descIndex = cells.indexOfFirst { 
                        it.contains("Description", ignoreCase = true) || 
                        it.contains("Narration", ignoreCase = true) || 
                        it.contains("Particulars", ignoreCase = true) ||
                        it.contains("Details", ignoreCase = true)
                    }
                    refIndex = cells.indexOfFirst { 
                        it.contains("Ref No", ignoreCase = true) || 
                        it.contains("Ref.No", ignoreCase = true) ||
                        it.contains("Chq No", ignoreCase = true) ||
                        it.contains("Chq./Ref.No", ignoreCase = true) ||
                        it.contains("Cheque No", ignoreCase = true) ||
                        it.contains("Reference", ignoreCase = true)
                    }
                    debitIndex = cells.indexOfFirst { cell ->
                        (cell.contains("Debit", ignoreCase = true) ||
                         cell.contains("Dr.", ignoreCase = true) ||
                         cell.contains("Withdrawal", ignoreCase = true) ||
                         cell.contains("Paid Out", ignoreCase = true)) &&
                        !cell.contains("Credit", ignoreCase = true) // Exclude "Debit/Credit" combined headers
                    }
                    creditIndex = cells.indexOfFirst { cell ->
                        (cell.contains("Credit", ignoreCase = true) ||
                         cell.contains("Cr.", ignoreCase = true) ||
                         cell.contains("Deposit", ignoreCase = true) ||
                         cell.contains("Paid In", ignoreCase = true)) &&
                        !cell.contains("Debit", ignoreCase = true) // Exclude "Debit/Credit" combined headers
                    }
                    balanceIndex = cells.indexOfFirst { 
                        it.contains("Balance", ignoreCase = true) ||
                        it.contains("Closing Balance", ignoreCase = true)
                    }
                    amountIndex = cells.indexOfFirst {
                        it.contains("Amount", ignoreCase = true) && 
                        !it.contains("Balance", ignoreCase = true)
                    }
                    typeIndex = cells.indexOfFirst {
                        it.contains("Type", ignoreCase = true) ||
                        it.contains("Dr/Cr", ignoreCase = true) ||
                        it.contains("Debit/Credit", ignoreCase = true)
                    }
                    println("[Excel] ✓ Header found - Date:$dateIndex, Desc:$descIndex, Debit:$debitIndex, Credit:$creditIndex, Amount:$amountIndex, Type:$typeIndex, Balance:$balanceIndex")
                } else {
                    if (rowCount <= 20) { // Only log first 20 rows to avoid spam
                        println("[Excel] Row $rowCount not a header (hasDate=$hasDate, hasDesc=$hasDesc, hasAmount=$hasAmount)")
                    }
                }
            } else {
                // Parse data row - ensure we have minimum required columns
                if (dateIndex == -1 || descIndex == -1) {
                    println("[Excel] Missing required columns - Date:$dateIndex, Desc:$descIndex")
                    continue
                }
                
                // Check if we have enough cells for the required columns
                val maxRequiredIndex = listOf(dateIndex, descIndex).filter { it >= 0 }.maxOrNull() ?: -1
                if (cells.isEmpty() || cells.size <= maxRequiredIndex) continue
                
                try {
                    val dateStr = cells.getOrNull(dateIndex)?.replace(Regex("[^a-zA-Z0-9-]"), "")
                    if (dateStr.isNullOrEmpty()) continue

                        val txnDate = try {
                            LocalDate.parse(dateStr, dateFormatter)
                        } catch (e: Exception) {
                             // Fallback manual parsing for dd-MMM-yy
                            val parts = dateStr.split("-")
                            if (parts.size == 3) {
                                val day = parts[0].toInt()
                                val monthStr = parts[1].lowercase(Locale.ENGLISH)
                                val yearPart = parts[2].toInt()
                                val year = if (yearPart < 100) 2000 + yearPart else yearPart
                                val month = when {
                                    monthStr.startsWith("jan") -> 1
                                    monthStr.startsWith("feb") -> 2
                                    monthStr.startsWith("mar") -> 3
                                    monthStr.startsWith("apr") -> 4
                                    monthStr.startsWith("may") -> 5
                                    monthStr.startsWith("jun") -> 6
                                    monthStr.startsWith("jul") -> 7
                                    monthStr.startsWith("aug") -> 8
                                    monthStr.startsWith("sep") -> 9
                                    monthStr.startsWith("oct") -> 10
                                    monthStr.startsWith("nov") -> 11
                                    monthStr.startsWith("dec") -> 12
                                    else -> throw e
                                }
                                LocalDate.of(year, month, day)
                            } else {
                                throw e
                            }
                        }

                        val valueDateStr = cells.getOrNull(valueDateIndex)?.replace(Regex("[^a-zA-Z0-9-]"), "")
                        val valueDate = if (!valueDateStr.isNullOrEmpty()) {
                             try {
                                LocalDate.parse(valueDateStr, dateFormatter)
                            } catch (e: Exception) {
                                null
                            }
                        } else null

                        val description = cells.getOrNull(descIndex) ?: ""
                        val reference = cells.getOrNull(refIndex)

                        // Handle different column formats
                        val (amount, direction) = if (amountIndex >= 0 && typeIndex >= 0) {
                            // Format: Amount + Type (Dr/Cr)
                            val amountStr = cells.getOrNull(amountIndex)?.replace(Regex("[^0-9.]"), "") ?: ""
                            val typeStr = cells.getOrNull(typeIndex) ?: ""
                            val amt = amountStr.toDoubleOrNull() ?: 0.0
                            val dir = when {
                                typeStr.contains("Dr", ignoreCase = true) || typeStr.contains("Debit", ignoreCase = true) -> ActivityType.EXPENSE
                                typeStr.contains("Cr", ignoreCase = true) || typeStr.contains("Credit", ignoreCase = true) -> ActivityType.INCOME
                                else -> ActivityType.EXPENSE // Default to expense
                            }
                            Pair(amt, dir)
                        } else {
                            // Format: Separate Debit/Credit columns
                            val debitStr = cells.getOrNull(debitIndex)?.replace(Regex("[^0-9.]"), "") ?: ""
                            val creditStr = cells.getOrNull(creditIndex)?.replace(Regex("[^0-9.]"), "") ?: ""
                            val debit = debitStr.toDoubleOrNull() ?: 0.0
                            val credit = creditStr.toDoubleOrNull() ?: 0.0
                            
                            if (debit > 0) Pair(debit, ActivityType.EXPENSE)
                            else if (credit > 0) Pair(credit, ActivityType.INCOME)
                            else Pair(0.0, ActivityType.EXPENSE)
                        }
                        
                        val balanceStr = cells.getOrNull(balanceIndex)?.replace(Regex("[^0-9.]"), "") ?: "0"
                        val balance = balanceStr.toDoubleOrNull() ?: 0.0

                        if (amount > 0) {

                            transactions.add(
                                ParsedTransaction(
                                    txnDate = txnDate,
                                    valueDate = valueDate,
                                    description = description,
                                    reference = reference,
                                    amount = amount,
                                    direction = direction,
                                    balanceAfterTxn = balance
                                )
                            )
                        }
                    } catch (e: Exception) {
                        println("[Excel] Error parsing row: ${e.message}")
                        e.printStackTrace()
                    }
                }
            }
            
            println("[Excel] Parsed ${transactions.size} transactions")
            return transactions
        } catch (e: Exception) {
            println("[Excel] Error parsing Excel file: ${e.message}")
            e.printStackTrace()
            throw e
        }
    }

    private fun parseCsv(inputStream: InputStream): List<ParsedTransaction> {
        val reader = BufferedReader(InputStreamReader(inputStream))
        val transactions = mutableListOf<ParsedTransaction>()
        var isHeaderFound = false
        
        // Column indices (will be detected dynamically)
        var dateIndex = -1
        var valueDateIndex = -1
        var descIndex = -1
        var refIndex = -1
        var debitIndex = -1
        var creditIndex = -1
        var balanceIndex = -1

        val dateFormatter = DateTimeFormatter.ofPattern("dd-MMM-yy", Locale.ENGLISH)

        reader.useLines { lines ->
            lines.forEach { line ->
                val tokens = parseCsvLine(line)
                
                if (!isHeaderFound) {
                    // Check if this is the header row
                    // Flexible header detection
                    val hasDate = tokens.any { it.contains("Txn Date", ignoreCase = true) || it.contains("Date", ignoreCase = true) }
                    val hasDesc = tokens.any { it.contains("Description", ignoreCase = true) || it.contains("Narration", ignoreCase = true) || it.contains("Particulars", ignoreCase = true) }
                    
                    if (hasDate && hasDesc) {
                        isHeaderFound = true
                        
                        // Map indices
                        dateIndex = tokens.indexOfFirst { it.contains("Txn Date", ignoreCase = true) || it.contains("Date", ignoreCase = true) }
                        valueDateIndex = tokens.indexOfFirst { it.contains("Value Date", ignoreCase = true) }
                        descIndex = tokens.indexOfFirst { it.contains("Description", ignoreCase = true) || it.contains("Narration", ignoreCase = true) || it.contains("Particulars", ignoreCase = true) }
                        refIndex = tokens.indexOfFirst { it.contains("Ref No", ignoreCase = true) || it.contains("Cheque No", ignoreCase = true) }
                        debitIndex = tokens.indexOfFirst { it.contains("Debit", ignoreCase = true) || it.contains("Withdrawal", ignoreCase = true) }
                        creditIndex = tokens.indexOfFirst { it.contains("Credit", ignoreCase = true) || it.contains("Deposit", ignoreCase = true) }
                        balanceIndex = tokens.indexOfFirst { it.contains("Balance", ignoreCase = true) }
                        println("[CSV] Header row: ${tokens.joinToString(" | ")}")
                        println("[CSV] Header found - Date:$dateIndex, Desc:$descIndex, Debit:$debitIndex, Credit:$creditIndex")
                    }
                } else {
                    // Parse data row - early exit for empty/invalid rows
                    if (tokens.all { it.isBlank() }) return@forEach // Skip completely empty rows
                    if (tokens.size <= maxOf(dateIndex, descIndex, debitIndex, creditIndex)) return@forEach // Skip incomplete rows
                    
                    try {
                        val dateStr = tokens.getOrNull(dateIndex)?.trim()?.replace(Regex("[^a-zA-Z0-9- ]"), "")
                        if (dateStr.isNullOrEmpty() || dateStr.length < 6) return@forEach // Skip invalid dates

                        val txnDate = try {
                            LocalDate.parse(dateStr, dateFormatter)
                        } catch (e: Exception) {
                            // Fallback manual parsing for various formats
                            try {
                                // Try space-separated format: "1 Feb 2022" or dash-separated "01-Apr-24"
                                val parts = if (dateStr.contains(" ")) dateStr.split(" ") else dateStr.split("-")
                                if (parts.size == 3) {
                                    val day = parts[0].trim().toIntOrNull() ?: throw e
                                    val monthStr = parts[1].trim().lowercase(Locale.ENGLISH)
                                    val yearPart = parts[2].trim().toIntOrNull() ?: throw e
                                    val year = if (yearPart < 100) 2000 + yearPart else yearPart
                                    val month = when {
                                        monthStr.startsWith("jan") -> 1
                                        monthStr.startsWith("feb") -> 2
                                        monthStr.startsWith("mar") -> 3
                                        monthStr.startsWith("apr") -> 4
                                        monthStr.startsWith("may") -> 5
                                        monthStr.startsWith("jun") -> 6
                                        monthStr.startsWith("jul") -> 7
                                        monthStr.startsWith("aug") -> 8
                                        monthStr.startsWith("sep") -> 9
                                        monthStr.startsWith("oct") -> 10
                                        monthStr.startsWith("nov") -> 11
                                        monthStr.startsWith("dec") -> 12
                                        else -> throw e
                                    }
                                    LocalDate.of(year, month, day)
                                } else {
                                    throw e
                                }
                            } catch (ex: Exception) {
                                return@forEach // Skip this row if date parsing fails
                            }
                        }
                        
                        val valueDateStr = tokens.getOrNull(valueDateIndex)?.trim()?.replace(Regex("[^a-zA-Z0-9- ]"), "")
                        val valueDate = if (!valueDateStr.isNullOrEmpty()) {
                            try {
                                LocalDate.parse(valueDateStr, dateFormatter)
                            } catch (e: Exception) {
                                null // ValueDate is optional, just skip if parsing fails
                            }
                        } else null
                        
                        val description = tokens.getOrNull(descIndex)?.trim() ?: ""
                        val reference = tokens.getOrNull(refIndex)?.trim()
                        
                        val debitStr = tokens.getOrNull(debitIndex)?.replace(Regex("[^0-9.]"), "") ?: ""
                        val creditStr = tokens.getOrNull(creditIndex)?.replace(Regex("[^0-9.]"), "") ?: ""
                        val balanceStr = tokens.getOrNull(balanceIndex)?.replace(Regex("[^0-9.]"), "") ?: "0"

                        val debit = debitStr.toDoubleOrNull() ?: 0.0
                        val credit = creditStr.toDoubleOrNull() ?: 0.0
                        val balance = balanceStr.toDoubleOrNull() ?: 0.0

                        if (debit > 0 || credit > 0) {
                            val amount = if (debit > 0) debit else credit
                            val direction = if (debit > 0) ActivityType.EXPENSE else ActivityType.INCOME
                            
                            transactions.add(
                                ParsedTransaction(
                                    txnDate = txnDate,
                                    valueDate = valueDate,
                                    description = description,
                                    reference = reference,
                                    amount = amount,
                                    direction = direction,
                                    balanceAfterTxn = balance
                                )
                            )
                        }
                    } catch (e: Exception) {
                        println("[CSV] Error parsing row: ${e.message}")
                    }
                }
            }
        }
        println("[CSV] Parsed ${transactions.size} transactions from CSV")
        return transactions
    }

    private fun parseCsvLine(line: String): List<String> {
        // Auto-detect delimiter: prefer tab when present, fallback to comma
        val tabCount = line.count { it == '\t' }
        val commaCount = line.count { it == ',' }
        val delimiter = when {
            tabCount > commaCount -> '\t'
            commaCount == 0 && tabCount == 0 -> ','
            else -> ','
        }

        if (delimiter == '\t') {
            return line.split('\t')
        }

        // Simple CSV parser that handles quoted fields containing commas
        val result = mutableListOf<String>()
        val sb = StringBuilder()
        var inQuotes = false
        
        for (char in line) {
            when {
                char == '"' -> inQuotes = !inQuotes
                char == delimiter && !inQuotes -> {
                    result.add(sb.toString())
                    sb.clear()
                }
                else -> sb.append(char)
            }
        }
        result.add(sb.toString())
        return result
    }
}
