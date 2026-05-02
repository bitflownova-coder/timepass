package com.bitflow.pdfconverter.feature.security.engine

import android.graphics.pdf.PdfDocument
import android.graphics.pdf.PdfRenderer
import android.graphics.Bitmap
import android.os.ParcelFileDescriptor
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.pdmodel.encryption.AccessPermission
import com.tom_roush.pdfbox.pdmodel.encryption.StandardProtectionPolicy
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PdfEncryptor @Inject constructor(
    private val fileManager: FileManager
) {
    /**
     * Applies AES-256 password protection using PdfBox StandardProtectionPolicy.
     * The output PDF will require [userPassword] to open and [ownerPassword] for full access.
     */
    fun encrypt(inputFile: File, userPassword: String, ownerPassword: String): File {
        val outputFile = fileManager.newOutputFile("${inputFile.nameWithoutExtension}_locked.pdf")
        PDDocument.load(inputFile).use { doc ->
            val permissions = AccessPermission()
            val policy = StandardProtectionPolicy(ownerPassword, userPassword, permissions)
            policy.encryptionKeyLength = 256
            doc.protect(policy)
            doc.save(outputFile)
        }
        return outputFile
    }

    /**
     * Removes password protection by loading with [password] and saving without encryption.
     */
    fun decrypt(inputFile: File, password: String): File {
        val outputFile = fileManager.newOutputFile("${inputFile.nameWithoutExtension}_unlocked.pdf")
        PDDocument.load(inputFile, password).use { doc ->
            doc.setAllSecurityToBeRemoved(true)
            doc.save(outputFile)
        }
        return outputFile
    }

    /**
     * Renders the PDF to bitmaps and writes a new clean PdfDocument — effectively stripping
     * any existing password from the rendered output.
     */
    fun renderAndSave(inputFile: File): File {
        val outputFile = fileManager.newOutputFile("${inputFile.nameWithoutExtension}_clean.pdf")
        val parcelFd = ParcelFileDescriptor.open(inputFile, ParcelFileDescriptor.MODE_READ_ONLY)
        val renderer = PdfRenderer(parcelFd)
        val doc = PdfDocument()

        for (i in 0 until renderer.pageCount) {
            val page = renderer.openPage(i)
            val bmp = Bitmap.createBitmap(page.width, page.height, Bitmap.Config.ARGB_8888)
            page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            page.close()
            val pageInfo = PdfDocument.PageInfo.Builder(bmp.width, bmp.height, i + 1).create()
            val pdfPage = doc.startPage(pageInfo)
            pdfPage.canvas.drawBitmap(bmp, 0f, 0f, null)
            bmp.recycle()
            doc.finishPage(pdfPage)
        }
        renderer.close()
        parcelFd.close()
        FileOutputStream(outputFile).use { doc.writeTo(it) }
        doc.close()
        return outputFile
    }
}
