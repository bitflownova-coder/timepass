package com.bitflow.pdfconverter.feature.scanner.viewmodel

import android.graphics.Bitmap
import android.graphics.PointF
import com.bitflow.pdfconverter.core.common.mvi.MviViewModel
import com.bitflow.pdfconverter.core.common.result.runCatchingPdf
import com.bitflow.pdfconverter.core.data.repository.PdfDocumentRepository
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.feature.scanner.contract.*
import com.bitflow.pdfconverter.feature.scanner.processing.EdgeDetector
import com.bitflow.pdfconverter.feature.scanner.processing.ImageEnhancer
import com.bitflow.pdfconverter.feature.scanner.processing.PerspectiveCorrector
import com.bitflow.pdfconverter.feature.scanner.processing.ScanToPdfExporter
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.UUID
import javax.inject.Inject

@HiltViewModel
class ScannerViewModel @Inject constructor(
    private val pdfExporter: ScanToPdfExporter,
    private val fileManager: FileManager,
    private val repository: PdfDocumentRepository
) : MviViewModel<ScannerState, ScannerIntent, ScannerSideEffect>(ScannerState()) {

    override suspend fun handleIntent(intent: ScannerIntent) {
        when (intent) {
            ScannerIntent.CameraReady -> updateState { copy(isCameraReady = true) }

            is ScannerIntent.PhotoCaptured -> processCapture(intent.bitmap)

            is ScannerIntent.CornersAdjusted -> updateState {
                copy(pages = pages.map { p ->
                    if (p.id == intent.pageId) p.copy(cropCorners = intent.corners) else p
                })
            }

            is ScannerIntent.ApplyCrop -> applyCrop(intent.pageId)

            is ScannerIntent.FilterChanged -> updateState { copy(currentFilter = intent.filter) }

            is ScannerIntent.ApplyFilterToPage -> applyFilter(intent.pageId, intent.filter)

            is ScannerIntent.DeletePage -> updateState {
                copy(pages = pages.filterNot { it.id == intent.pageId })
            }

            is ScannerIntent.ReorderPages -> reorderPages(intent.from, intent.to)

            is ScannerIntent.ExportToPdf -> exportToPdf(intent.outputName)

            is ScannerIntent.ImportPhotosFromGallery -> importPhotos(intent.bitmaps)

            ScannerIntent.HideCropView -> updateState { copy(showCropView = false) }

            ScannerIntent.DismissError -> updateState { copy(errorMessage = null) }
        }
    }

    // ── Private helpers ──────────────────────────────────────────────────────

    private suspend fun processCapture(bitmap: Bitmap) {
        updateState { copy(isProcessing = true) }
        withContext(Dispatchers.Default) {
            val corners   = EdgeDetector.detectEdges(bitmap)
            val corrected = PerspectiveCorrector.correct(bitmap, corners)
            val filtered  = ImageEnhancer.apply(corrected, currentState.currentFilter)
            val page = ScannedPage(
                id              = UUID.randomUUID().toString(),
                originalBitmap  = bitmap,
                processedBitmap = filtered,
                cropCorners     = corners,
                appliedFilter   = currentState.currentFilter
            )
            updateState { copy(pages = pages + page, isProcessing = false, showCropView = true) }
        }
        // Don't send NavigateToCrop side effect — crop is shown inline in ScannerScreen
    }

    private suspend fun applyCrop(pageId: String) {
        val page = currentState.pages.find { it.id == pageId } ?: return
        updateState { copy(isProcessing = true) }
        withContext(Dispatchers.Default) {
            val corrected = PerspectiveCorrector.correct(page.originalBitmap, page.cropCorners)
            val filtered  = ImageEnhancer.apply(corrected, page.appliedFilter)
            updateState {
                copy(
                    pages = pages.map { p ->
                        if (p.id == pageId) p.copy(processedBitmap = filtered) else p
                    },
                    isProcessing = false
                )
            }
        }
    }

    private suspend fun applyFilter(pageId: String, filter: ImageFilter) {
        val page = currentState.pages.find { it.id == pageId } ?: return
        withContext(Dispatchers.Default) {
            val corrected = PerspectiveCorrector.correct(page.originalBitmap, page.cropCorners)
            val filtered  = ImageEnhancer.apply(corrected, filter)
            updateState {
                copy(pages = pages.map { p ->
                    if (p.id == pageId) p.copy(processedBitmap = filtered, appliedFilter = filter) else p
                })
            }
        }
    }

    private fun reorderPages(from: Int, to: Int) {
        val pages = currentState.pages.toMutableList()
        if (from !in pages.indices || to !in pages.indices) return
        val item = pages.removeAt(from)
        pages.add(to, item)
        updateState { copy(pages = pages) }
    }

    private suspend fun exportToPdf(name: String) {
        if (currentState.pages.isEmpty()) {
            sendEffect(ScannerSideEffect.ShowError("No pages to export"))
            return
        }
        updateState { copy(isProcessing = true) }
        val result = withContext(Dispatchers.IO) {
            runCatchingPdf {
                pdfExporter.export(
                    pages      = currentState.pages.map { it.processedBitmap },
                    outputName = name
                )
            }
        }
        result
            .onSuccess { file ->
                fileManager.publishToDownloads(file, "Scanner")
                val now = System.currentTimeMillis()
                repository.saveDocument(
                    PdfDocument(
                        name      = file.nameWithoutExtension,
                        filePath  = file.absolutePath,
                        sizeBytes = file.length(),
                        pageCount = currentState.pages.size,
                        createdAt = now,
                        modifiedAt = now
                    )
                )
                updateState { copy(isProcessing = false, showCropView = false) }
                sendEffect(ScannerSideEffect.PdfExported(file.absolutePath))
            }
            .onError { msg, _ ->
                updateState { copy(isProcessing = false, errorMessage = msg) }
                sendEffect(ScannerSideEffect.ShowError(msg))
            }
    }

    /** Adds gallery-picked bitmaps directly as pages (no perspective correction needed). */
    private suspend fun importPhotos(bitmaps: List<Bitmap>) {
        if (bitmaps.isEmpty()) return
        updateState { copy(isProcessing = true) }
        withContext(Dispatchers.Default) {
            bitmaps.forEach { bitmap ->
                val filtered = ImageEnhancer.apply(bitmap, currentState.currentFilter)
                val w = bitmap.width.toFloat()
                val h = bitmap.height.toFloat()
                val fullCorners = listOf(
                    android.graphics.PointF(0f, 0f),
                    android.graphics.PointF(w, 0f),
                    android.graphics.PointF(w, h),
                    android.graphics.PointF(0f, h)
                )
                val page = ScannedPage(
                    id              = UUID.randomUUID().toString(),
                    originalBitmap  = bitmap,
                    processedBitmap = filtered,
                    cropCorners     = fullCorners,
                    appliedFilter   = currentState.currentFilter
                )
                updateState { copy(pages = pages + page) }
            }
        }
        updateState { copy(isProcessing = false) }
    }
}
