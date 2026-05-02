package com.bitflow.finance.widget

import android.content.Context
import android.content.Intent
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.action.actionStartActivity
import androidx.glance.action.clickable
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import androidx.glance.appwidget.provideContent
import androidx.glance.background
import androidx.glance.layout.Alignment
import androidx.glance.layout.Box
import androidx.glance.layout.Column
import androidx.glance.layout.padding
import androidx.glance.layout.size
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import androidx.glance.unit.ColorProvider
import com.bitflow.finance.ui.MainActivity

class QuickAddWidget : GlanceAppWidget() {

    override suspend fun provideGlance(context: Context, id: GlanceId) {
        provideContent {
            QuickAddWidgetContent()
        }
    }
}

@Composable
fun QuickAddWidgetContent() {
    val primaryColor = ColorProvider(android.graphics.Color.parseColor("#3B82F6"))
    val textWhite = ColorProvider(android.graphics.Color.WHITE)

    Box(
        modifier = GlanceModifier
            .size(60.dp)
            .background(primaryColor)
            .clickable(actionStartActivity<MainActivity>(
                // Pass an intent extra to open add transaction screen directly?
                // For now, just opening the app is good.
                // Ideal implementation would pass a deep link or extra.
            )),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = "+",
            style = TextStyle(
                color = textWhite,
                fontSize = androidx.compose.ui.unit.TextUnit(32f, androidx.compose.ui.unit.TextUnitType.Sp)
            )
        )
    }
}

class QuickAddWidgetReceiver : GlanceAppWidgetReceiver() {
    override val glanceAppWidget: GlanceAppWidget = QuickAddWidget()
}
