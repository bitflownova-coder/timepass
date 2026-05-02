package com.bitflow.finance.data.parser

import java.io.BufferedReader
import java.io.ByteArrayInputStream
import java.io.InputStream
import java.io.InputStreamReader

/**
 * Factory that detects the bank statement format and returns the appropriate parser
 * 
 * Detection Strategy:
 * 1. Detect if file is Excel or CSV/text
 * 2. If Excel, convert to text format first
 * 3. Read first 40 lines of the file
 * 4. Look for identifying keywords in headers
 * 5. Return the matching parser implementation
 */
object StatementParserFactory {
    
    private val PARSERS = listOf(
        // Check Bitflow first (most specific - has "Particulars")
        ParserDetector(
            name = "Bitflow",
            keywords = listOf(
                listOf("particulars", "withdrawal"),
                listOf("particulars", "deposit"),
                listOf("date", "particulars", "withdrawal"),
                listOf("date", "particulars", "deposit")
            ),
            parserProvider = { BitflowStatementParser() }
        ),
        // Then SBI (specific column names)
        ParserDetector(
            name = "SBI",
            keywords = listOf(
                listOf("trans date", "debit"),
                listOf("txn date", "debit"),
                listOf("transaction date", "dr."),
                listOf("transaction date", "dr"),
                listOf("date", "debit(dr.)"),
                listOf("date", "narration", "debit"),
                listOf("date", "description", "debit")
            ),
            parserProvider = { SbiStatementParser() }
        ),
        // Generic fallback (least specific)
        ParserDetector(
            name = "Generic",
            keywords = listOf(
                listOf("date", "dr"),
                listOf("date", "cr"),
                listOf("date", "debit"),
                listOf("date", "credit"),
                listOf("date", "withdrawal"),
                listOf("date", "deposit")
            ),
            parserProvider = { GenericIndianBankParser() }
        )
    )
    
    /**
     * Detect the appropriate parser for the given input stream
     * 
     * @param inputStream The statement file input stream
     * @return The appropriate BankStatementParser implementation
     * @throws UnknownStatementFormatException if no matching parser is found
     */
    fun detectParser(inputStream: InputStream): BankStatementParser {
        // Read stream into byte array to preserve it
        val bytes = inputStream.readBytes()
        
        // Read first 40 lines for detection
        val previewStream = ByteArrayInputStream(bytes)
        val reader = BufferedReader(InputStreamReader(previewStream))
        val lines = mutableListOf<String>()
        
        try {
            var linesRead = 0
            var line = reader.readLine()
            while (line != null && linesRead < 40) {
                lines.add(line)
                linesRead++
                line = reader.readLine()
            }
        } catch (e: Exception) {
            println("[Parser Factory] Error reading file: ${e.message}")
            throw UnknownStatementFormatException("Failed to read file: ${e.message}")
        }
        
        println("[Parser Factory] Read ${lines.size} lines for format detection")
        
        return detectParserFromLines(lines)
    }
    
    /**
     * Detect parser from lines (works for both text and converted Excel files)
     */
    private fun detectParserFromLines(lines: List<String>): BankStatementParser {
        // Try to detect format
        for (detector in PARSERS) {
            if (detector.matches(lines)) {
                println("[Parser Factory] Detected format: ${detector.name}")
                return detector.parserProvider()
            }
        }
        
        // No matching parser found
        println("[Parser Factory] No matching parser found. Tried: ${PARSERS.map { it.name }}")
        println("[Parser Factory] First 10 lines:")
        lines.take(10).forEachIndexed { index, line ->
            println("[Parser Factory]   Line $index: $line")
        }
        
        throw UnknownStatementFormatException(
            "Unknown statement format. Supported formats: ${PARSERS.joinToString { it.name }}"
        )
    }
    
    /**
     * Parse a statement file using auto-detected parser
     * 
     * @param inputStream The statement file input stream
     * @return ParseResult containing transactions and detected current balance
     * @throws UnknownStatementFormatException if format cannot be detected
     * @throws StatementParsingException if parsing fails
     */
    fun parseStatement(inputStream: InputStream): ParseResult {
        // Read into byte array to allow multiple reads
        val bytes = inputStream.readBytes()
        
        // Detect if Excel file
        val lines = if (isExcelFile(bytes)) {
            println("[Parser Factory] Detected Excel file, converting to text...")
            try {
                val excelStream = ByteArrayInputStream(bytes)
                ExcelReader.readExcelAsLines(excelStream)
            } catch (e: Exception) {
                println("[Parser Factory] Excel conversion failed: ${e.message}")
                throw StatementParsingException("Failed to read Excel file: ${e.message}", e)
            }
        } else {
            // Text file (CSV/TSV)
            println("[Parser Factory] Detected text file (CSV/TSV)")
            val textStream = ByteArrayInputStream(bytes)
            val reader = BufferedReader(InputStreamReader(textStream))
            reader.readLines()
        }
        
        println("[Parser Factory] Read ${lines.size} lines for format detection")
        
        // Detect parser using lines
        val parser = detectParserFromLines(lines)
        
        // Parse using detected parser
        // Convert lines back to input stream
        val textData = lines.joinToString("\n")
        val parsingStream = ByteArrayInputStream(textData.toByteArray())
        return parser.parse(parsingStream)
    }
    
    /**
     * Check if the file is an Excel file based on magic bytes
     */
    private fun isExcelFile(bytes: ByteArray): Boolean {
        if (bytes.size < 8) return false
        
        // Check for Excel magic bytes
        // XLSX: PK (ZIP format) - 50 4B 03 04
        val isXlsx = bytes[0] == 0x50.toByte() && 
                     bytes[1] == 0x4B.toByte() && 
                     bytes[2] == 0x03.toByte() && 
                     bytes[3] == 0x04.toByte()
        
        // XLS: D0 CF 11 E0 A1 B1 1A E1 (OLE2 format)
        val isXls = bytes[0] == 0xD0.toByte() && 
                    bytes[1] == 0xCF.toByte() && 
                    bytes[2] == 0x11.toByte() && 
                    bytes[3] == 0xE0.toByte()
        
        return isXlsx || isXls
    }
    
    /**
     * Add a custom parser to the factory
     * This allows extending the factory with new bank formats
     */
    fun registerParser(
        name: String,
        keywords: List<List<String>>,
        parserProvider: () -> BankStatementParser
    ) {
        // This would be used for dynamic parser registration in the future
        // For now, parsers are statically defined in PARSERS list
        println("[Parser Factory] Custom parser registration not yet implemented")
    }
    
    /**
     * Helper class for parser detection
     */
    private data class ParserDetector(
        val name: String,
        val keywords: List<List<String>>,
        val parserProvider: () -> BankStatementParser
    ) {
        /**
         * Check if any line in the file matches this parser's keywords
         * Prioritize lines that look like headers (have commas/tabs)
         */
        fun matches(lines: List<String>): Boolean {
            // First pass: Look for header-like rows (rows with multiple separators)
            for (line in lines) {
                val lineLower = line.lowercase()
                
                // Skip empty lines
                if (lineLower.isBlank()) continue
                
                // Consider it a potential header if it has commas or tabs
                val hasMultipleSeparators = lineLower.count { it == ',' || it == '\t' } >= 3
                
                if (hasMultipleSeparators) {
                    // Check each keyword combination
                    for (keywordSet in keywords) {
                        val allMatch = keywordSet.all { keyword ->
                            lineLower.contains(keyword)
                        }
                        
                        if (allMatch) {
                            println("[Parser Factory] Matched $name format with keywords: $keywordSet in header-like row")
                            println("[Parser Factory]   Matched line: ${line.take(150)}")
                            return true
                        }
                    }
                }
            }
            
            // Second pass: Check all lines (for backward compatibility)
            for (line in lines) {
                val lineLower = line.lowercase()
                
                // Check each keyword combination
                for (keywordSet in keywords) {
                    val allMatch = keywordSet.all { keyword ->
                        lineLower.contains(keyword)
                    }
                    
                    if (allMatch) {
                        println("[Parser Factory] Matched $name format with keywords: $keywordSet")
                        return true
                    }
                }
            }
            
            return false
        }
    }
}
