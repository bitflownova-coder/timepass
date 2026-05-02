package com.bitflow.finance.ui.screens.dev_tools

import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.widget.Toast
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import java.io.File
import java.io.FileOutputStream
import com.google.zxing.BarcodeFormat
import com.google.zxing.EncodeHintType
import com.google.zxing.qrcode.QRCodeWriter
import com.google.zxing.qrcode.decoder.ErrorCorrectionLevel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QRCodeGeneratorScreen(
    onBackClick: () -> Unit
) {
    val context = LocalContext.current
    
    var contentType by remember { mutableStateOf("text") }
    var textContent by remember { mutableStateOf("") }
    var urlContent by remember { mutableStateOf("https://") }
    var wifiSsid by remember { mutableStateOf("") }
    var wifiPassword by remember { mutableStateOf("") }
    var wifiEncryption by remember { mutableStateOf("WPA") }
    var contactName by remember { mutableStateOf("") }
    var contactPhone by remember { mutableStateOf("") }
    var contactEmail by remember { mutableStateOf("") }
    
    var qrBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var qrSize by remember { mutableStateOf(256) }
    var qrForegroundColor by remember { mutableStateOf(Color.Black) }
    var qrBackgroundColor by remember { mutableStateOf(Color.White) }
    
    fun generateQRContent(): String {
        return when (contentType) {
            "url" -> urlContent
            "wifi" -> "WIFI:S:$wifiSsid;T:$wifiEncryption;P:$wifiPassword;;"
            "contact" -> buildString {
                append("BEGIN:VCARD\n")
                append("VERSION:3.0\n")
                if (contactName.isNotEmpty()) append("FN:$contactName\n")
                if (contactPhone.isNotEmpty()) append("TEL:$contactPhone\n")
                if (contactEmail.isNotEmpty()) append("EMAIL:$contactEmail\n")
                append("END:VCARD")
            }
            else -> textContent
        }
    }
    
    fun generateQR() {
        val content = generateQRContent()
        if (content.isNotBlank() && content != "https://") {
            qrBitmap = generateQRBitmap(
                content = content,
                size = qrSize,
                foreground = qrForegroundColor.toArgb(),
                background = qrBackgroundColor.toArgb()
            )
        }
    }
    
    fun saveQRToGallery() {
        qrBitmap?.let { bitmap ->
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    val contentValues = ContentValues().apply {
                        put(MediaStore.MediaColumns.DISPLAY_NAME, "QR_${System.currentTimeMillis()}.png")
                        put(MediaStore.MediaColumns.MIME_TYPE, "image/png")
                        put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/QRCodes")
                    }
                    val resolver = context.contentResolver
                    val uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, contentValues)
                    uri?.let {
                        resolver.openOutputStream(it)?.use { outputStream ->
                            bitmap.compress(Bitmap.CompressFormat.PNG, 100, outputStream)
                        }
                    }
                } else {
                    val imagesDir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES), "QRCodes")
                    imagesDir.mkdirs()
                    val file = File(imagesDir, "QR_${System.currentTimeMillis()}.png")
                    FileOutputStream(file).use { outputStream ->
                        bitmap.compress(Bitmap.CompressFormat.PNG, 100, outputStream)
                    }
                }
                Toast.makeText(context, "QR Code saved to gallery", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                Toast.makeText(context, "Failed to save: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    fun shareQR() {
        qrBitmap?.let { bitmap ->
            try {
                val cachePath = File(context.cacheDir, "images")
                cachePath.mkdirs()
                val file = File(cachePath, "qr_share.png")
                FileOutputStream(file).use { outputStream ->
                    bitmap.compress(Bitmap.CompressFormat.PNG, 100, outputStream)
                }
                
                val uri = FileProvider.getUriForFile(context, "${context.packageName}.provider", file)
                val shareIntent = Intent(Intent.ACTION_SEND).apply {
                    type = "image/png"
                    putExtra(Intent.EXTRA_STREAM, uri)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                context.startActivity(Intent.createChooser(shareIntent, "Share QR Code"))
            } catch (e: Exception) {
                Toast.makeText(context, "Failed to share: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("QR Code Generator", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Content Type Selection
            item {
                Card(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text("Content Type", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        
                        SingleChoiceSegmentedButtonRow(
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            SegmentedButton(
                                selected = contentType == "text",
                                onClick = { contentType = "text" },
                                shape = SegmentedButtonDefaults.itemShape(0, 4)
                            ) {
                                Text("Text", maxLines = 1)
                            }
                            SegmentedButton(
                                selected = contentType == "url",
                                onClick = { contentType = "url" },
                                shape = SegmentedButtonDefaults.itemShape(1, 4)
                            ) {
                                Text("URL", maxLines = 1)
                            }
                            SegmentedButton(
                                selected = contentType == "wifi",
                                onClick = { contentType = "wifi" },
                                shape = SegmentedButtonDefaults.itemShape(2, 4)
                            ) {
                                Text("WiFi", maxLines = 1)
                            }
                            SegmentedButton(
                                selected = contentType == "contact",
                                onClick = { contentType = "contact" },
                                shape = SegmentedButtonDefaults.itemShape(3, 4)
                            ) {
                                Text("Contact", maxLines = 1)
                            }
                        }
                    }
                }
            }
            
            // Content Input
            item {
                Card(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text("Content", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        
                        when (contentType) {
                            "text" -> {
                                OutlinedTextField(
                                    value = textContent,
                                    onValueChange = { textContent = it },
                                    label = { Text("Enter text") },
                                    modifier = Modifier.fillMaxWidth(),
                                    minLines = 3
                                )
                            }
                            "url" -> {
                                OutlinedTextField(
                                    value = urlContent,
                                    onValueChange = { urlContent = it },
                                    label = { Text("URL") },
                                    modifier = Modifier.fillMaxWidth(),
                                    singleLine = true,
                                    leadingIcon = { Icon(Icons.Default.Link, null) }
                                )
                            }
                            "wifi" -> {
                                OutlinedTextField(
                                    value = wifiSsid,
                                    onValueChange = { wifiSsid = it },
                                    label = { Text("Network Name (SSID)") },
                                    modifier = Modifier.fillMaxWidth(),
                                    singleLine = true,
                                    leadingIcon = { Icon(Icons.Default.Wifi, null) }
                                )
                                
                                OutlinedTextField(
                                    value = wifiPassword,
                                    onValueChange = { wifiPassword = it },
                                    label = { Text("Password") },
                                    modifier = Modifier.fillMaxWidth(),
                                    singleLine = true,
                                    leadingIcon = { Icon(Icons.Default.Lock, null) }
                                )
                                
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    listOf("WPA", "WEP", "nopass").forEach { enc ->
                                        FilterChip(
                                            selected = wifiEncryption == enc,
                                            onClick = { wifiEncryption = enc },
                                            label = { Text(if (enc == "nopass") "Open" else enc) }
                                        )
                                    }
                                }
                            }
                            "contact" -> {
                                OutlinedTextField(
                                    value = contactName,
                                    onValueChange = { contactName = it },
                                    label = { Text("Name") },
                                    modifier = Modifier.fillMaxWidth(),
                                    singleLine = true,
                                    leadingIcon = { Icon(Icons.Default.Person, null) }
                                )
                                
                                OutlinedTextField(
                                    value = contactPhone,
                                    onValueChange = { contactPhone = it },
                                    label = { Text("Phone") },
                                    modifier = Modifier.fillMaxWidth(),
                                    singleLine = true,
                                    leadingIcon = { Icon(Icons.Default.Phone, null) }
                                )
                                
                                OutlinedTextField(
                                    value = contactEmail,
                                    onValueChange = { contactEmail = it },
                                    label = { Text("Email") },
                                    modifier = Modifier.fillMaxWidth(),
                                    singleLine = true,
                                    leadingIcon = { Icon(Icons.Default.Email, null) }
                                )
                            }
                        }
                    }
                }
            }
            
            // QR Customization
            item {
                Card(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text("Customization", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        
                        // Size
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("Size: ${qrSize}x${qrSize}")
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                listOf(128, 256, 512).forEach { size ->
                                    FilterChip(
                                        selected = qrSize == size,
                                        onClick = { qrSize = size },
                                        label = { Text("${size}") }
                                    )
                                }
                            }
                        }
                        
                        // Colors
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(16.dp)
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text("Foreground", style = MaterialTheme.typography.labelMedium)
                                Row(
                                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                                    modifier = Modifier.padding(top = 8.dp)
                                ) {
                                    listOf(
                                        Color.Black,
                                        Color(0xFF1E40AF),
                                        Color(0xFF166534),
                                        Color(0xFF991B1B),
                                        Color(0xFF7C3AED)
                                    ).forEach { color ->
                                        Box(
                                            modifier = Modifier
                                                .size(32.dp)
                                                .clip(RoundedCornerShape(4.dp))
                                                .background(color)
                                                .border(
                                                    width = if (qrForegroundColor == color) 2.dp else 0.dp,
                                                    color = MaterialTheme.colorScheme.primary,
                                                    shape = RoundedCornerShape(4.dp)
                                                )
                                                .clickable { qrForegroundColor = color }
                                        )
                                    }
                                }
                            }
                            
                            Column(modifier = Modifier.weight(1f)) {
                                Text("Background", style = MaterialTheme.typography.labelMedium)
                                Row(
                                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                                    modifier = Modifier.padding(top = 8.dp)
                                ) {
                                    listOf(
                                        Color.White,
                                        Color(0xFFFEF3C7),
                                        Color(0xFFD1FAE5),
                                        Color(0xFFDBEAFE),
                                        Color(0xFFFCE7F3)
                                    ).forEach { color ->
                                        Box(
                                            modifier = Modifier
                                                .size(32.dp)
                                                .clip(RoundedCornerShape(4.dp))
                                                .background(color)
                                                .border(
                                                    width = if (qrBackgroundColor == color) 2.dp else 0.dp,
                                                    color = MaterialTheme.colorScheme.primary,
                                                    shape = RoundedCornerShape(4.dp)
                                                )
                                                .clickable { qrBackgroundColor = color }
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // Generate Button
            item {
                Button(
                    onClick = { generateQR() },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = when (contentType) {
                        "text" -> textContent.isNotBlank()
                        "url" -> urlContent.isNotBlank() && urlContent != "https://"
                        "wifi" -> wifiSsid.isNotBlank()
                        "contact" -> contactName.isNotBlank() || contactPhone.isNotBlank() || contactEmail.isNotBlank()
                        else -> false
                    }
                ) {
                    Icon(Icons.Default.QrCode, null, modifier = Modifier.size(20.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Generate QR Code")
                }
            }
            
            // QR Code Display
            qrBitmap?.let { bitmap ->
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(16.dp)
                        ) {
                            Text("Generated QR Code", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            
                            Image(
                                bitmap = bitmap.asImageBitmap(),
                                contentDescription = "QR Code",
                                modifier = Modifier
                                    .size(256.dp)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(qrBackgroundColor)
                            )
                            
                            Row(
                                horizontalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                OutlinedButton(
                                    onClick = { saveQRToGallery() }
                                ) {
                                    Icon(Icons.Default.Save, null, modifier = Modifier.size(20.dp))
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text("Save")
                                }
                                
                                Button(
                                    onClick = { shareQR() }
                                ) {
                                    Icon(Icons.Default.Share, null, modifier = Modifier.size(20.dp))
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text("Share")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

// QR Code generation using ZXing library
private fun generateQRBitmap(
    content: String,
    size: Int,
    foreground: Int,
    background: Int
): Bitmap? {
    return try {
        val hints = hashMapOf<EncodeHintType, Any>(
            EncodeHintType.ERROR_CORRECTION to ErrorCorrectionLevel.H,
            EncodeHintType.MARGIN to 1,
            EncodeHintType.CHARACTER_SET to "UTF-8"
        )
        
        val writer = QRCodeWriter()
        val bitMatrix = writer.encode(content, BarcodeFormat.QR_CODE, size, size, hints)
        
        val bitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        for (x in 0 until size) {
            for (y in 0 until size) {
                bitmap.setPixel(x, y, if (bitMatrix[x, y]) foreground else background)
            }
        }
        bitmap
    } catch (e: Exception) {
        e.printStackTrace()
        null
    }
}
