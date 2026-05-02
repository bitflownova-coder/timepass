package com.bitflow.finance.util

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import java.util.Locale
import java.util.regex.Pattern

/**
 * Voice input utility for parsing spoken transaction descriptions.
 * Parses natural language like "Add ₹200 for coffee today" into structured data.
 */
object VoiceInputHelper {

    data class ParsedTransaction(
        val amount: Double?,
        val description: String?,
        val category: String?,
        val isExpense: Boolean = true
    )

    /**
     * Creates a SpeechRecognizer and returns results as a Flow.
     */
    fun startListening(context: Context): Flow<VoiceResult> = callbackFlow {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            trySend(VoiceResult.Error("Speech recognition not available"))
            close()
            return@callbackFlow
        }

        val recognizer = SpeechRecognizer.createSpeechRecognizer(context)
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }

        recognizer.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                trySend(VoiceResult.Listening)
            }

            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {}

            override fun onError(error: Int) {
                val message = when (error) {
                    SpeechRecognizer.ERROR_NO_MATCH -> "No speech recognized"
                    SpeechRecognizer.ERROR_AUDIO -> "Audio error"
                    SpeechRecognizer.ERROR_NETWORK -> "Network error"
                    else -> "Recognition error"
                }
                trySend(VoiceResult.Error(message))
            }

            override fun onResults(results: Bundle?) {
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val text = matches?.firstOrNull() ?: ""
                val parsed = parseSpokenText(text)
                trySend(VoiceResult.Success(text, parsed))
            }

            override fun onPartialResults(partialResults: Bundle?) {
                val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val text = matches?.firstOrNull() ?: ""
                trySend(VoiceResult.Partial(text))
            }

            override fun onEvent(eventType: Int, params: Bundle?) {}
        })

        recognizer.startListening(intent)

        awaitClose {
            recognizer.destroy()
        }
    }

    /**
     * Parses natural language transaction description.
     * Examples:
     * - "Add 200 for coffee" → amount=200, description="coffee", isExpense=true
     * - "Received 5000 from salary" → amount=5000, description="salary", isExpense=false
     */
    fun parseSpokenText(text: String): ParsedTransaction {
        val lowerText = text.lowercase()
        
        // Determine if income or expense
        val isExpense = !lowerText.contains("received") && 
                        !lowerText.contains("got") && 
                        !lowerText.contains("earned") &&
                        !lowerText.contains("income")

        // Extract amount
        val amountPattern = Pattern.compile("(\\d+(?:\\.\\d{1,2})?)")
        val amountMatcher = amountPattern.matcher(text)
        val amount = if (amountMatcher.find()) {
            amountMatcher.group(1)?.toDoubleOrNull()
        } else null

        // Extract description (after "for", "on", "from")
        val descPattern = Pattern.compile("(?:for|on|from)\\s+(.+?)(?:\\s+(?:today|yesterday|tomorrow))?$", Pattern.CASE_INSENSITIVE)
        val descMatcher = descPattern.matcher(text)
        val description = if (descMatcher.find()) {
            descMatcher.group(1)?.trim()
        } else {
            // Try to extract anything after the amount
            val cleanText = text.replace(Regex("\\d+(?:\\.\\d{1,2})?"), "").trim()
            cleanText.replace(Regex("^(add|spent|paid|received|got)\\s*", RegexOption.IGNORE_CASE), "").trim().takeIf { it.isNotEmpty() }
        }

        // Try to guess category from keywords
        val category = when {
            lowerText.contains("coffee") || lowerText.contains("food") || lowerText.contains("lunch") || lowerText.contains("dinner") -> "Food"
            lowerText.contains("uber") || lowerText.contains("ola") || lowerText.contains("travel") || lowerText.contains("fuel") -> "Transport"
            lowerText.contains("movie") || lowerText.contains("netflix") || lowerText.contains("entertainment") -> "Entertainment"
            lowerText.contains("grocery") || lowerText.contains("shopping") -> "Shopping"
            lowerText.contains("bill") || lowerText.contains("electricity") -> "Bills"
            lowerText.contains("salary") || lowerText.contains("payment") -> "Income"
            else -> null
        }

        return ParsedTransaction(
            amount = amount,
            description = description,
            category = category,
            isExpense = isExpense
        )
    }

    sealed class VoiceResult {
        object Listening : VoiceResult()
        data class Partial(val text: String) : VoiceResult()
        data class Success(val rawText: String, val parsed: ParsedTransaction) : VoiceResult()
        data class Error(val message: String) : VoiceResult()
    }
}
