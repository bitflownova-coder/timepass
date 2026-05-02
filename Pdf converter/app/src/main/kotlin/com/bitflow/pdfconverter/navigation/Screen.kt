package com.bitflow.pdfconverter.navigation

sealed class Screen(val route: String) {
    data object Home : Screen("home")
    data object Scanner : Screen("scanner")
    data object ScannerCrop : Screen("scanner/crop")
    data object Converter : Screen("converter")
    data object ImageToPdf : Screen("converter/image_to_pdf")
    data object OfficeToPdf : Screen("converter/office_to_pdf")
    data object MergePdf : Screen("converter/merge")
    data object SplitPdf : Screen("converter/split")
    data object Editor : Screen("editor?fileUri={fileUri}") {
        fun withFile(fileUri: String) = "editor?fileUri=$fileUri"
        const val ARG_FILE_URI = "fileUri"
    }
    data object Optimization : Screen("optimization?fileUri={fileUri}") {
        fun withFile(fileUri: String) = "optimization?fileUri=$fileUri"
        const val ARG_FILE_URI = "fileUri"
    }
    data object Security : Screen("security?fileUri={fileUri}&section={section}") {
        fun withFile(fileUri: String) = "security?fileUri=$fileUri"
        fun withSection(section: String) = "security?section=$section"
        const val ARG_FILE_URI = "fileUri"
        const val ARG_SECTION = "section"
    }
    data object SmartTools : Screen("smarttools?section={section}") {
        fun withSection(section: String) = "smarttools?section=$section"
        const val ARG_SECTION = "section"
    }
    data object Ocr : Screen("smarttools/ocr?fileUri={fileUri}") {
        fun withFile(fileUri: String) = "smarttools/ocr?fileUri=$fileUri"
        const val ARG_FILE_URI = "fileUri"
    }
    data object QrScanner : Screen("smarttools/qr_scanner")
    data object QrGenerator : Screen("smarttools/qr_generator")
    data object PdfSearch : Screen("smarttools/pdf_search?fileUri={fileUri}") {
        fun withFile(fileUri: String) = "smarttools/pdf_search?fileUri=$fileUri"
        const val ARG_FILE_URI = "fileUri"
    }
    data object Storage : Screen("storage")
    data object Utility : Screen("utility?section={section}") {
        fun withSection(section: String) = "utility?section=$section"
        const val ARG_SECTION = "section"
    }
    data object PdfDownloader : Screen("pdf_downloader")
    data object Onboarding : Screen("onboarding")
    data object Settings : Screen("settings")
}
