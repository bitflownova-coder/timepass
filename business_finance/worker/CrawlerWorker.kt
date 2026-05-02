package com.bitflow.finance.worker

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.pm.ServiceInfo
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.ForegroundInfo
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import com.bitflow.finance.R
import com.bitflow.finance.crawler.CrawlerEngine
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@HiltWorker
class CrawlerWorker @AssistedInject constructor(
    @Assisted private val context: Context,
    @Assisted workerParams: WorkerParameters,
    private val crawlerRepository: com.bitflow.finance.domain.repository.CrawlerRepository,
    private val controlManager: com.bitflow.finance.crawler.CrawlerControlManager
) : CoroutineWorker(context, workerParams) {

    private val notificationManager = 
        context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

    override suspend fun doWork(): Result {
        val url = inputData.getString("KEY_URL") ?: return Result.failure()
        val depth = inputData.getInt("KEY_DEPTH", 1)
        var sessionId = inputData.getLong("KEY_SESSION_ID", 0L)
        
        setForeground(createForegroundInfo(url))

        return try {
            // 1. Create or use existing session
            if (sessionId == 0L) {
                sessionId = crawlerRepository.createSession(url, depth, "")
            } else {
                // Ensure status is RUNNING if we picked up a PENDING session
                crawlerRepository.updateStatus(sessionId, "RUNNING")
            }
            
            val crawler = CrawlerEngine(context)
            controlManager.register(sessionId, crawler) // REGISTER
            
            val logs = StringBuilder()
            
            crawler.start(sessionId, url, depth, 
                onLog = { log ->
                    logs.appendLine(log)
                },
                onProgress = { count ->
                     try {
                        kotlinx.coroutines.runBlocking {
                            crawlerRepository.updateProgress(sessionId, count)
                        }
                     } catch (e: Exception) {
                         // Ignore DB update errors
                     }
                }
            )
            
            showCompletionNotification(url, true)
            crawlerRepository.completeSession(sessionId, true)
            Result.success(workDataOf("LOGS" to logs.toString()))
        } catch (e: Exception) {
            showCompletionNotification(url, false)
            if (sessionId != 0L) {
                crawlerRepository.completeSession(sessionId, false)
            }
            Result.failure(workDataOf("ERROR" to e.message))
        } finally {
            if (sessionId != 0L) {
                controlManager.unregister(sessionId) // UNREGISTER
            }
        }
    }

    private fun createForegroundInfo(url: String): ForegroundInfo {
        val channelId = "crawler_channel"
        val notificationId = 1001

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Website Crawler",
                NotificationManager.IMPORTANCE_LOW
            )
            notificationManager.createNotificationChannel(channel)
        }

        val notification = NotificationCompat.Builder(context, channelId)
            .setContentTitle("Crawling Website")
            .setContentText("Scanning $url...")
            .setSmallIcon(R.mipmap.ic_launcher_round)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()

        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ForegroundInfo(
                notificationId,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
            )
        } else {
            ForegroundInfo(notificationId, notification)
        }
    }

    private fun showCompletionNotification(url: String, isSuccess: Boolean) {
        val channelId = "crawler_channel"
        val notificationId = 1002

        val title = if (isSuccess) "Crawl Finished" else "Crawl Failed"
        val text = if (isSuccess) "Successfully scanned $url" else "Failed to scan $url"

        val notification = NotificationCompat.Builder(context, channelId)
            .setContentTitle(title)
            .setContentText(text)
            .setSmallIcon(R.mipmap.ic_launcher_round)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        notificationManager.notify(notificationId, notification)
    }
}
