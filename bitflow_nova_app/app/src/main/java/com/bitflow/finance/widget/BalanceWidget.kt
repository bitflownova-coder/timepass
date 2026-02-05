package com.bitflow.finance.widget

import android.content.Context
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.*
import androidx.glance.action.actionStartActivity
import androidx.glance.action.clickable
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import androidx.glance.appwidget.provideContent
import androidx.glance.layout.*
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import androidx.glance.unit.ColorProvider
import com.bitflow.finance.ui.MainActivity
import com.bitflow.finance.data.local.AppDatabase
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class BalanceWidget : GlanceAppWidget() {

    override suspend fun provideGlance(context: Context, id: GlanceId) {
        // Get balance data
        val balance = withContext(Dispatchers.IO) {
            try {
                val db = AppDatabase.getInstance(context)
                val accounts = db.accountDao().getAllAccountsSync()
                accounts.sumOf { it.currentBalance }
            } catch (e: Exception) {
                0.0
            }
        }

        provideContent {
            BalanceWidgetContent(balance)
        }
    }
}

@Composable
fun BalanceWidgetContent(balance: Double) {
    val primaryGreen = ColorProvider(android.graphics.Color.parseColor("#10B981"))
    val surfaceColor = ColorProvider(android.graphics.Color.parseColor("#1E293B"))
    val textWhite = ColorProvider(android.graphics.Color.WHITE)
    val textGray = ColorProvider(android.graphics.Color.parseColor("#94A3B8"))

    Box(
        modifier = GlanceModifier
            .fillMaxSize()
            .background(surfaceColor)
            .padding(16.dp)
            .clickable(actionStartActivity<MainActivity>()),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "💰",
                style = TextStyle(fontSize = 24.sp)
            )
            Spacer(modifier = GlanceModifier.height(8.dp))
            Text(
                text = "Total Balance",
                style = TextStyle(
                    color = textGray,
                    fontSize = 12.sp
                )
            )
            Spacer(modifier = GlanceModifier.height(4.dp))
            Text(
                text = "₹${"%,.0f".format(balance)}",
                style = TextStyle(
                    color = textWhite,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )
            )
            Spacer(modifier = GlanceModifier.height(8.dp))
            Row(
                modifier = GlanceModifier
                    .background(primaryGreen)
                    .padding(horizontal = 12.dp, vertical = 4.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "Tap to open",
                    style = TextStyle(
                        color = textWhite,
                        fontSize = 10.sp
                    )
                )
            }
        }
    }
}

class BalanceWidgetReceiver : GlanceAppWidgetReceiver() {
    override val glanceAppWidget: GlanceAppWidget = BalanceWidget()
}
