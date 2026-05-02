package com.bitflow.finance.util

import com.bitflow.finance.data.local.dao.UserAccountDao
import com.bitflow.finance.data.local.entity.UserAccountEntity
import java.time.LocalDate
import java.time.ZoneId
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Tracks user activity streaks for gamification.
 * A streak is maintained when the user logs at least one transaction per day.
 */
@Singleton
class StreakManager @Inject constructor(
    private val userAccountDao: UserAccountDao
) {

    /**
     * Called when a transaction is logged. Updates streak if appropriate.
     */
    suspend fun onTransactionLogged(userId: String) {
        val user = userAccountDao.getUserById(userId) ?: return
        val today = LocalDate.now().atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli()
        
        val lastLogDate = user.lastLogDate
        val daysSinceLastLog = if (lastLogDate != null) {
            val lastDate = java.time.Instant.ofEpochMilli(lastLogDate)
                .atZone(ZoneId.systemDefault()).toLocalDate()
            java.time.temporal.ChronoUnit.DAYS.between(lastDate, LocalDate.now()).toInt()
        } else {
            -1 // First log ever
        }

        val newStreak = when {
            daysSinceLastLog == 0 -> user.currentStreak // Already logged today
            daysSinceLastLog == 1 -> user.currentStreak + 1 // Continuing streak
            else -> 1 // Starting fresh streak
        }

        val newLongestStreak = maxOf(user.longestStreak, newStreak)

        val updatedUser = user.copy(
            currentStreak = newStreak,
            longestStreak = newLongestStreak,
            lastLogDate = today
        )

        userAccountDao.updateUser(updatedUser)
    }

    /**
     * Gets the current streak for a user.
     */
    suspend fun getStreak(userId: String): StreakInfo {
        val user = userAccountDao.getUserById(userId)
        return if (user != null) {
            // Check if streak is still valid (logged yesterday or today)
            val lastLogDate = user.lastLogDate
            val isActiveStreak = if (lastLogDate != null) {
                val lastDate = java.time.Instant.ofEpochMilli(lastLogDate)
                    .atZone(ZoneId.systemDefault()).toLocalDate()
                val daysSince = java.time.temporal.ChronoUnit.DAYS.between(lastDate, LocalDate.now()).toInt()
                daysSince <= 1
            } else {
                false
            }

            StreakInfo(
                currentStreak = if (isActiveStreak) user.currentStreak else 0,
                longestStreak = user.longestStreak,
                isActiveToday = lastLogDate != null && 
                    java.time.Instant.ofEpochMilli(lastLogDate)
                        .atZone(ZoneId.systemDefault()).toLocalDate() == LocalDate.now()
            )
        } else {
            StreakInfo(0, 0, false)
        }
    }

    data class StreakInfo(
        val currentStreak: Int,
        val longestStreak: Int,
        val isActiveToday: Boolean
    )
}
