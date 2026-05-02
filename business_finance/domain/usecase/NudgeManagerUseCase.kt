package com.bitflow.finance.domain.usecase

import com.bitflow.finance.domain.model.FinancialPersona
import com.bitflow.finance.domain.model.DailyPulse
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flowOf
import java.time.DayOfWeek
import java.time.LocalDate
import javax.inject.Inject

data class SmartNudge(
    val message: String,
    val type: NudgeType,
    val actionLabel: String? = null
)

enum class NudgeType {
    INFO, WARNING, TIP, CELEBRATION
}

class NudgeManagerUseCase @Inject constructor(
    private val behaviorAnalyzerUseCase: BehaviorAnalyzerUseCase
) {

    operator fun invoke(userId: String): Flow<SmartNudge?> {
        return behaviorAnalyzerUseCase(userId).combine(flowOf(LocalDate.now())) { persona, date ->
            generateNudge(persona, date)
        }
    }

    private fun generateNudge(persona: FinancialPersona, date: LocalDate): SmartNudge? {
        val isWeekend = date.dayOfWeek == DayOfWeek.SATURDAY || date.dayOfWeek == DayOfWeek.SUNDAY
        val isMonthEnd = date.dayOfMonth >= 25

        return when (persona) {
            FinancialPersona.IMPULSE_SPENDER -> {
                if (isWeekend) {
                    SmartNudge("⚠️ Weakness Alert: Weekends are your high-spend zones. Stick to the list!", NudgeType.WARNING)
                } else null
            }
            FinancialPersona.PAYCHECK_TO_PAYCHECK -> {
                if (isMonthEnd) {
                    SmartNudge("🛡️ Survival Mode: 5 days to payday. Avoid non-essentials.", NudgeType.WARNING)
                } else null
            }
            FinancialPersona.LIFESTYLE_INFLATOR -> {
                SmartNudge("💡 Tip: Try saving 50% of your next raise/bonus.", NudgeType.TIP)
            }
            FinancialPersona.CONSCIOUS_SAVER -> {
                if (Math.random() < 0.3) {
                    SmartNudge("🎉 You're crushing it! Your savings rate is top 5%.", NudgeType.CELEBRATION)
                } else null
            }
            else -> null
        }
    }
}
