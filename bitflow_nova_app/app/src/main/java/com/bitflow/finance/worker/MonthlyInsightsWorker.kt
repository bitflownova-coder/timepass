package com.bitflow.finance.worker

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.*
import com.bitflow.finance.ui.MainActivity
import com.bitflow.finance.R
import com.bitflow.finance.data.local.AppDatabase
import com.bitflow.finance.domain.model.AppMode
import java.time.LocalDate
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.flow.first

class MonthlyInsightsWorker(
    private val context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    companion object {
        private const val CHANNEL_ID = "monthly_insights"
        private const val NOTIFICATION_ID = 1001
        private const val WORK_NAME = "monthly_insights_work"

        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiresBatteryNotLow(true)
                .build()

            // Calculate delay until 1st of next month at 9 AM
            val now = LocalDate.now()
            val nextMonth = now.plusMonths(1).withDayOfMonth(1)
            val daysUntil = java.time.temporal.ChronoUnit.DAYS.between(now, nextMonth)
            
            val request = PeriodicWorkRequestBuilder<MonthlyInsightsWorker>(30, TimeUnit.DAYS)
                .setConstraints(constraints)
                .setInitialDelay(daysUntil, TimeUnit.DAYS)
                .build()

            WorkManager.getInstance(context)
                .enqueueUniquePeriodicWork(
                    WORK_NAME,
                    ExistingPeriodicWorkPolicy.KEEP,
                    request
                )
        }
    }

    override suspend fun doWork(): Result {
        return try {
            val db = AppDatabase.getInstance(applicationContext)
            val now = LocalDate.now()
            val lastMonth = now.minusMonths(1)
            val twoMonthsAgo = now.minusMonths(2)


            // Get last month's transactions
            val lastMonthTransactions = db.transactionDao()
                .getTransactionsInPeriod(lastMonth.withDayOfMonth(1), now.withDayOfMonth(1), "default", AppMode.PERSONAL)
                .first()

            val lastMonthSpent = lastMonthTransactions
                .filter { it.direction.name == "EXPENSE" }
                .sumOf { it.amount }

            // Get previous month's transactions for comparison
            val prevMonthTransactions = db.transactionDao()
                .getTransactionsInPeriod(twoMonthsAgo.withDayOfMonth(1), lastMonth.withDayOfMonth(1), "default", AppMode.PERSONAL)
                .first()

            val prevMonthSpent = prevMonthTransactions
                .filter { it.direction.name == "EXPENSE" }
                .sumOf { it.amount }


            val difference = prevMonthSpent - lastMonthSpent
            val emoji = if (difference > 0) "🎉" else "📊"
            val message = if (difference > 0) {
                "You saved ₹${"%,.0f".format(difference)} more than last month! $emoji"
            } else {
                "You spent ₹${"%,.0f".format(-difference)} more than last month. Review your spending!"
            }

            showNotification("Monthly Insights", message)
            Result.success()
        } catch (e: Exception) {
            Result.failure()
        }
    }

    private fun showNotification(title: String, message: String) {
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Monthly Insights",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "Monthly spending insights and tips"
            }
            notificationManager.createNotificationChannel(channel)
        }

        val intent = Intent(context, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            context, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        notificationManager.notify(NOTIFICATION_ID, notification)
    }
}
