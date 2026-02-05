package com.bitflow.finance.data.parser

import java.io.InputStream

/**
 * Generic fallback parser that tries to handle common Indian bank statement formats
 * This parser is more lenient and tries multiple column name variations
 */
class GenericIndianBankParser : BankStatementParser {
    
    companion object {
        // Very generic keywords that should match most Indian bank statements
        private val HEADER_KEYWORDS = listOf(
            "date" to "dr",
            "date" to "cr",
            "date" to "withdrawal",
            "date" to "deposit",
            "date" to "debit",
            "date" to "credit",
            "txn" to "debit",
            "txn" to "credit",
            "transaction" to "debit",
            "transaction" to "credit"
        )
    }
    
    override fun getParserName(): String = "Generic Indian Bank Parser"
    
    override fun parse(inputStream: InputStream): ParseResult {
        println("[Generic Parser] Using generic Indian bank parser")
        
        // Try SBI parser first
        return try {
            println("[Generic Parser] Attempting SBI-style parsing...")
            SbiStatementParser().parse(inputStream)
        } catch (e: Exception) {
            println("[Generic Parser] SBI parsing failed: ${e.message}")
            
            // Try Bitflow parser
            try {
                println("[Generic Parser] Attempting Bitflow-style parsing...")
                BitflowStatementParser().parse(inputStream)
            } catch (e2: Exception) {
                println("[Generic Parser] Bitflow parsing also failed: ${e2.message}")
                throw StatementParsingException("Generic parser failed to parse file", e2)
            }
        }
    }
    
    /**
     * Check if this could be an Indian bank statement (very lenient check)
     */
    fun couldBeIndianBankStatement(lines: List<String>): Boolean {
        val searchLimit = minOf(40, lines.size)
        
        for (i in 0 until searchLimit) {
            val line = lines[i].lowercase()
            
            // Very basic check: has "date" and some amount column
            if (line.contains("date") && 
                (line.contains("debit") || line.contains("credit") || 
                 line.contains("dr") || line.contains("cr") ||
                 line.contains("withdrawal") || line.contains("deposit"))) {
                return true
            }
        }
        
        return false
    }
}
