package com.bitflow.finance.domain.usecase

import com.bitflow.finance.data.parser.ParsedTransaction
import com.bitflow.finance.data.parser.StatementParserFactory
import com.bitflow.finance.data.parser.UnknownStatementFormatException
import com.bitflow.finance.data.parser.StatementParsingException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.InputStream
import javax.inject.Inject

/**
 * Use case for parsing bank statements using smart format detection
 * 
 * This replaces the old StatementParser with the new dynamic parser system
 */
class ParseStatementSmartUseCase @Inject constructor() {
    
    /**
     * Parse a bank statement file with automatic format detection
     * 
     * @param inputStream The statement file input stream
     * @param fileName The name of the file (for logging)
     * @return ParseResult containing parsed transactions or error
     */
    suspend operator fun invoke(
        inputStream: InputStream,
        fileName: String
    ): ParseResult = withContext(Dispatchers.IO) {
        try {
            println("[Smart Parser] Parsing file: $fileName")
            
            // Use factory to auto-detect and parse
            val parseResult = StatementParserFactory.parseStatement(inputStream)
            val transactions = parseResult.transactions
            val detectedBalance = parseResult.detectedCurrentBalance
            
            println("[Smart Parser] Successfully parsed ${transactions.size} transactions")
            println("[Smart Parser] Detected balance: ₹$detectedBalance")
            
            if (transactions.isEmpty()) {
                ParseResult.Empty(fileName)
            } else {
                ParseResult.Success(
                    fileName = fileName,
                    transactions = transactions
                )
            }
        } catch (e: UnknownStatementFormatException) {
            println("[Smart Parser] Unknown format: ${e.message}")
            ParseResult.Error(
                fileName = fileName,
                error = "Unknown Format",
                message = e.message ?: "This bank statement format is not supported yet."
            )
        } catch (e: StatementParsingException) {
            println("[Smart Parser] Parsing error: ${e.message}")
            ParseResult.Error(
                fileName = fileName,
                error = "Parsing Failed",
                message = e.message ?: "Failed to parse this statement file."
            )
        } catch (e: Exception) {
            println("[Smart Parser] Unexpected error: ${e.message}")
            e.printStackTrace()
            ParseResult.Error(
                fileName = fileName,
                error = "Error",
                message = e.message ?: "An unexpected error occurred."
            )
        }
    }
    
    /**
     * Result of statement parsing
     */
    sealed class ParseResult {
        abstract val fileName: String
        
        data class Success(
            override val fileName: String,
            val transactions: List<ParsedTransaction>
        ) : ParseResult()
        
        data class Empty(
            override val fileName: String
        ) : ParseResult()
        
        data class Error(
            override val fileName: String,
            val error: String,
            val message: String
        ) : ParseResult()
    }
}
