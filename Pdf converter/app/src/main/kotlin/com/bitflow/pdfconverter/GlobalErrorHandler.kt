package com.bitflow.pdfconverter

import android.content.Intent
import android.os.Build
import android.util.Log
import java.io.File
import java.io.FileWriter
import java.io.PrintWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Catches unhandled exceptions, writes a crash log to the app's files directory,
 * then restarts the app with a brief error message.
 *
 * Install in [PdfConverterApp.onCreate] with:
 *   Thread.setDefaultUncaughtExceptionHandler(GlobalErrorHandler(this))
 */
class GlobalErrorHandler(
    private val app: PdfConverterApp
) : Thread.UncaughtExceptionHandler {

    private val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()

    override fun uncaughtException(thread: Thread, throwable: Throwable) {
        try {
            writeCrashLog(throwable)
            restartApp()
        } catch (e: Exception) {
            Log.e(TAG, "Error inside GlobalErrorHandler", e)
        } finally {
            // Forward to the system default handler so the OS can also handle the crash
            defaultHandler?.uncaughtException(thread, throwable)
        }
    }

    private fun writeCrashLog(throwable: Throwable) {
        val logsDir = File(app.filesDir, "crash_logs").also { it.mkdirs() }
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val logFile = File(logsDir, "crash_$timestamp.txt")

        PrintWriter(FileWriter(logFile)).use { pw ->
            pw.println("=== PDF Converter Crash Report ===")
            pw.println("Time     : $timestamp")
            pw.println("Device   : ${Build.MANUFACTURER} ${Build.MODEL}")
            pw.println("Android  : ${Build.VERSION.RELEASE} (SDK ${Build.VERSION.SDK_INT})")
            pw.println("Thread   : ${Thread.currentThread().name}")
            pw.println()
            throwable.printStackTrace(pw)
        }
        Log.e(TAG, "Crash log written to ${logFile.absolutePath}")

        // Keep only the latest 5 crash logs to avoid filling storage
        logsDir.listFiles()
            ?.sortedByDescending { it.lastModified() }
            ?.drop(MAX_CRASH_LOGS)
            ?.forEach { it.delete() }
    }

    private fun restartApp() {
        val intent = app.packageManager
            .getLaunchIntentForPackage(app.packageName)
            ?.apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
                putExtra(EXTRA_CRASHED, true)
            } ?: return
        app.startActivity(intent)
    }

    companion object {
        private const val TAG = "GlobalErrorHandler"
        private const val MAX_CRASH_LOGS = 5
        const val EXTRA_CRASHED = "crashed"
    }
}
