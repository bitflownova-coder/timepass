package com.bitflow.finance.workers

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.bitflow.finance.R
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.usecase.CashForecastUseCase
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.flow.firstOrNull
import java.time.format.DateTimeFormatter

@HiltWorker
class LowBalanceWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted workerParams: WorkerParameters,
    private val cashForecastUseCase: CashForecastUseCase,
    private val authRepository: AuthRepository
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            val userId = authRepository.currentUserId.firstOrNull() ?: return Result.success() // No user
            
            // Forecast for next 30 days
            val projections = cashForecastUseCase(userId, 30).firstOrNull() ?: return Result.failure()
            
            val LOW_BALANCE_THRESHOLD = 5000.0 // Hardcoded for now
            val lowBalanceEvent = projections.firstOrNull { it.endingBalance < LOW_BALANCE_THRESHOLD }
            
            if (lowBalanceEvent != null) {
                sendNotification(lowBalanceEvent.date, lowBalanceEvent.endingBalance)
            }
            
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    private fun sendNotification(date: java.time.LocalDate, amount: Double) {
        val notificationManager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channelId = "finance_alerts"
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(channelId, "Financial Alerts", NotificationManager.IMPORTANCE_HIGH).apply {
                description = "Alerts for low balance and spending limits"
            }
            notificationManager.createNotificationChannel(channel)
        }
        
        val dateStr = date.format(DateTimeFormatter.ofPattern("MMM dd"))
        val notification = NotificationCompat.Builder(applicationContext, channelId)
            .setSmallIcon(R.mipmap.ic_launcher) // Fallback icon
            .setContentTitle("⚠️ Low Balance Warning")
            .setContentText("Your balance is projected to drop to ₹${amount.toInt()} on $dateStr.")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()
            
        notificationManager.notify(1001, notification)
    }

    companion object {
        fun schedule(context: Context) {
             val request = androidx.work.PeriodicWorkRequestBuilder<LowBalanceWorker>(
                1, java.util.concurrent.TimeUnit.DAYS
            )
            .setConstraints(
                androidx.work.Constraints.Builder()
                    .setRequiresBatteryNotLow(true)
                    .build()
            )
            .build()

            androidx.work.WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                "LowBalanceWorker",
                androidx.work.ExistingPeriodicWorkPolicy.KEEP,
                request
            )
        }
    }
}
