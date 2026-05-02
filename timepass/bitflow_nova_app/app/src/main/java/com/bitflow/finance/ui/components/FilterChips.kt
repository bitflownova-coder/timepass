package com.bitflow.finance.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import java.time.LocalDate

enum class TimeFilter(val label: String) {
    LAST_10("Last 10"),
    THIS_MONTH("This Month"),
    LAST_MONTH("Last Month"),
    THIS_QUARTER("This Quarter"),
    THIS_FY("This FY"),
    LAST_FY("Last FY"),
    ALL("All Time")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FilterChipsRow(
    selectedFilter: TimeFilter,
    onFilterSelected: (TimeFilter) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyRow(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        contentPadding = PaddingValues(horizontal = 16.dp)
    ) {
        items(TimeFilter.values()) { filter ->
            FilterChip(
                selected = selectedFilter == filter,
                onClick = { onFilterSelected(filter) },
                label = { Text(filter.label) }
            )
        }
    }
}

fun getDateRangeForFilter(filter: TimeFilter): Pair<LocalDate, LocalDate> {
    val today = LocalDate.now()
    return when (filter) {
        TimeFilter.LAST_10 -> {
            // Return null dates, handle separately with LIMIT 10
            today.minusDays(365) to today
        }
        TimeFilter.THIS_MONTH -> {
            today.withDayOfMonth(1) to today
        }
        TimeFilter.LAST_MONTH -> {
            val lastMonth = today.minusMonths(1)
            lastMonth.withDayOfMonth(1) to lastMonth.withDayOfMonth(lastMonth.lengthOfMonth())
        }
        TimeFilter.THIS_QUARTER -> {
            val quarter = (today.monthValue - 1) / 3
            val startMonth = quarter * 3 + 1
            val startDate = LocalDate.of(today.year, startMonth, 1)
            startDate to today
        }
        TimeFilter.THIS_FY -> {
            // Indian FY: April to March
            val fyStart = if (today.monthValue >= 4) {
                LocalDate.of(today.year, 4, 1)
            } else {
                LocalDate.of(today.year - 1, 4, 1)
            }
            fyStart to today
        }
        TimeFilter.LAST_FY -> {
            val fyStart = if (today.monthValue >= 4) {
                LocalDate.of(today.year - 1, 4, 1)
            } else {
                LocalDate.of(today.year - 2, 4, 1)
            }
            val fyEnd = fyStart.plusYears(1).minusDays(1)
            fyStart to fyEnd
        }
        TimeFilter.ALL -> {
            today.minusYears(10) to today
        }
    }
}
