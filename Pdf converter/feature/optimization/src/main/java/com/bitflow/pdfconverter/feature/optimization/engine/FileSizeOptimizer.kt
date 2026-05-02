package com.bitflow.pdfconverter.feature.optimization.engine

import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class FileSizeOptimizer @Inject constructor(
    private val compressor: PdfCompressor
) {
    /**
     * Binary-searches for the highest JPEG quality that produces an output file
     * at or below [maxSizeBytes]. Returns the resulting [File].
     *
     * If even quality=10 exceeds [maxSizeBytes], returns the best (smallest) result found.
     */
    suspend fun optimizeToSize(
        inputFile: File,
        dpi: Int,
        maxSizeBytes: Long,
        onProgress: (String) -> Unit = {}
    ): File {
        var lo = 10
        var hi = 95
        var bestFile: File? = null

        while (lo <= hi) {
            val mid = (lo + hi) / 2
            onProgress("Trying quality $mid%…")
            val candidate = compressor.compress(inputFile, dpi, mid)
            if (candidate.length() <= maxSizeBytes) {
                bestFile = candidate
                lo = mid + 1          // try higher quality
            } else {
                candidate.delete()    // too large, free disk
                hi = mid - 1          // try lower quality
            }
        }

        // Fallback: compress at minimum quality if nothing fit
        return bestFile ?: compressor.compress(inputFile, dpi, 10)
    }
}
