package com.bitflow.pdfconverter.core.common.result

/**
 * A discriminated union that encapsulates a successful outcome with a value of type [T] or a failure with an error message.
 */
sealed class PdfResult<out T> {
    data class Success<T>(val data: T) : PdfResult<T>()
    data class Error(val message: String, val cause: Throwable? = null) : PdfResult<Nothing>()
    data object Loading : PdfResult<Nothing>()

    val isSuccess: Boolean get() = this is Success
    val isError: Boolean get() = this is Error
    val isLoading: Boolean get() = this is Loading

    fun getOrNull(): T? = (this as? Success)?.data

    fun <R> map(transform: (T) -> R): PdfResult<R> = when (this) {
        is Success -> Success(transform(data))
        is Error -> this
        is Loading -> Loading
    }

    inline fun onSuccess(action: (T) -> Unit): PdfResult<T> {
        if (this is Success) action(data)
        return this
    }

    inline fun onError(action: (String, Throwable?) -> Unit): PdfResult<T> {
        if (this is Error) action(message, cause)
        return this
    }
}

/** Wraps a suspending block in a [PdfResult], catching any exception. */
suspend fun <T> runCatchingPdf(block: suspend () -> T): PdfResult<T> = try {
    PdfResult.Success(block())
} catch (e: Exception) {
    PdfResult.Error(e.message ?: "Unknown error", e)
}

/** Calls [action] with the Throwable when this is an Error (mirrors kotlin.Result.onFailure) */
inline fun <T> PdfResult<T>.onFailure(action: (Throwable) -> Unit): PdfResult<T> {
    if (this is PdfResult.Error) action(cause ?: Exception(message))
    return this
}

/** Maps Success/Error similar to kotlin.Result.fold */
inline fun <T, R> PdfResult<T>.fold(
    onSuccess: (T) -> R,
    onFailure: (Throwable) -> R
): R = when (this) {
    is PdfResult.Success -> onSuccess(data)
    is PdfResult.Error   -> onFailure(cause ?: Exception(message))
    is PdfResult.Loading -> throw IllegalStateException("fold() called on Loading state")
}

/** Returns data or calls onFailure lambda (like kotlin.Result.getOrElse) */
inline fun <T> PdfResult<T>.getOrElse(onFailure: (Throwable) -> T): T = when (this) {
    is PdfResult.Success -> data
    is PdfResult.Error   -> onFailure(cause ?: Exception(message))
    is PdfResult.Loading -> throw IllegalStateException("getOrElse() called on Loading state")
}
