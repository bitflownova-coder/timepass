package com.bitflow.pdfconverter.feature.utility.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.bitflow.pdfconverter.core.filesystem.FileManager
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Periodic WorkManager task that copies completed output PDFs to a designated sync folder.
 * Designed as a placeholder — wire up Google Drive via DriveManager for actual cloud sync.
 */
@HiltWorker
class OfflineSyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val fileManager: FileManager
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        try {
            val outputFiles = fileManager.outputDir.listFiles()
                ?.filter { it.extension == "pdf" }
                ?: return@withContext Result.success()

            // Offline: just verify files exist and are readable
            val validCount = outputFiles.count { it.canRead() && it.length() > 0 }

            // TODO: Upload to Google Drive when DriveManager is wired up
            // outputFiles.forEach { file -> driveManager.upload(file) }

            Result.success()
        } catch (e: Exception) {
            if (runAttemptCount < 3) Result.retry() else Result.failure()
        }
    }

    companion object {
        const val SYNC_WORK_NAME = "offline_sync_work"
    }
}
