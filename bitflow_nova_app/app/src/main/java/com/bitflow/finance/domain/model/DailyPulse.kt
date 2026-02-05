package com.bitflow.finance.domain.model

/**
 * "Peace of Mind" dashboard metric
 * Replaces complex budget bars and net worth displays
 */
data class DailyPulse(
    val safeToSpendToday: Double,
    val pulseStatus: PulseStatus,
    val message: String, // e.g., "You can spend ₹1,200 today and still save money"
    val progressPercentage: Float // 0.0 to 1.0 for gauge
)

enum class PulseStatus {
    GREAT,      // Green - plenty to spend
    GOOD,       // Green - healthy spending
    CAUTION,    // Yellow - approaching limit
    SLOW_DOWN   // Red - over budget
}
