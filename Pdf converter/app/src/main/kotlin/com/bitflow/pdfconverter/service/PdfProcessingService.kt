package com.bitflow.pdfconverter.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.bitflow.pdfconverter.MainActivity
import com.bitflow.pdfconverter.R
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

/**
 * ForegroundService that runs heavy PDF operations (batch conversion, OCR, optimization)
 * off the main thread with a persistent notification showing progress.
 *
 * Expected intent extras:
 *   ACTION_EXTRA       — string key for the operation type (see ACTION_* constants)
 *   EXTRA_FILE_URI     — source file URI string
 *   EXTRA_DESCRIPTION  — human-readable description shown in the notification
 */
@AndroidEntryPoint
class PdfProcessingService : Service() {

    private val job = SupervisorJob()
    private val scope = CoroutineScope(Dispatchers.IO + job)

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification("Processing…", 0, 0, true))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.getStringExtra(ACTION_EXTRA) ?: ACTION_NOOP
        val fileUri = intent?.getStringExtra(EXTRA_FILE_URI) ?: ""
        val description = intent?.getStringExtra(EXTRA_DESCRIPTION) ?: action

        when (action) {
            ACTION_NOOP -> stopSelf(startId)
            else -> {
                scope.launch {
                    runOperation(action, fileUri, description, startId)
                }
            }
        }
        return START_NOT_STICKY
    }

    private suspend fun runOperation(
        action: String,
        fileUri: String,
        description: String,
        startId: Int
    ) {
        try {
            updateNotification(description, progress = 0, max = 100, indeterminate = true)
            // Actual heavy-lifting is performed by the calling ViewModel / Worker;
            // this service is responsible only for keeping the process alive.
            // Caller sends ACTION_COMPLETE to dismiss when done.
        } catch (e: Exception) {
            updateNotification("Error: ${e.localizedMessage}", 0, 0, false)
        } finally {
            stopSelf(startId)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
    }

    // ── Notification helpers ─────────────────────────────────────────────────

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "PDF Processing",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Shows progress of ongoing PDF operations"
            setShowBadge(false)
        }
        getSystemService(NotificationManager::class.java)
            .createNotificationChannel(channel)
    }

    private fun updateNotification(title: String, progress: Int, max: Int, indeterminate: Boolean) {
        val nm = getSystemService(NotificationManager::class.java)
        nm.notify(NOTIFICATION_ID, buildNotification(title, progress, max, indeterminate))
    }

    private fun buildNotification(
        title: String,
        progress: Int,
        max: Int,
        indeterminate: Boolean
    ): Notification {
        val tapIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        val cancelIntent = PendingIntent.getService(
            this,
            1,
            Intent(this, PdfProcessingService::class.java).apply {
                putExtra(ACTION_EXTRA, ACTION_CANCEL)
            },
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_save)
            .setContentTitle(title)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setContentIntent(tapIntent)
            .setProgress(max, progress, indeterminate)
            .addAction(android.R.drawable.ic_delete, "Cancel", cancelIntent)
            .build()
    }

    companion object {
        private const val CHANNEL_ID = "pdf_processing_channel"
        const val NOTIFICATION_ID = 1001

        const val ACTION_EXTRA = "action"
        const val EXTRA_FILE_URI = "fileUri"
        const val EXTRA_DESCRIPTION = "description"

        const val ACTION_NOOP = "noop"
        const val ACTION_CANCEL = "cancel"
        const val ACTION_OCR = "ocr"
        const val ACTION_BATCH_COMPRESS = "batch_compress"
        const val ACTION_BATCH_CONVERT = "batch_convert"

        fun start(context: Context, action: String, fileUri: String, description: String) {
            val intent = Intent(context, PdfProcessingService::class.java).apply {
                putExtra(ACTION_EXTRA, action)
                putExtra(EXTRA_FILE_URI, fileUri)
                putExtra(EXTRA_DESCRIPTION, description)
            }
            context.startForegroundService(intent)
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, PdfProcessingService::class.java))
        }
    }
}
