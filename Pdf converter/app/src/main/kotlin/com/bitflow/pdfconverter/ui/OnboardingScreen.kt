package com.bitflow.pdfconverter.ui

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountBox
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.Storage
import androidx.compose.material.icons.filled.Work
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

private data class OnboardingPage(
    val icon: ImageVector,
    val title: String,
    val description: String
)

private val featurePages = listOf(
    OnboardingPage(
        icon = Icons.Default.CameraAlt,
        title = "Scan Documents",
        description = "Use your camera to scan physical documents. Auto-detect edges, crop, and enhance for crisp PDF output."
    ),
    OnboardingPage(
        icon = Icons.Default.Description,
        title = "Convert & Edit",
        description = "Convert images to PDF, merge or split documents, and annotate pages with highlights and notes."
    ),
    OnboardingPage(
        icon = Icons.Default.Lock,
        title = "Secure Your Files",
        description = "Password-protect PDFs, apply watermarks, redact sensitive content, and manage digital signatures."
    ),
    OnboardingPage(
        icon = Icons.Default.Storage,
        title = "All Offline",
        description = "Everything works without internet. Your files stay on your device — private and always accessible."
    )
)

// Step 0 = name+role, Steps 1-4 = feature pages
@Composable
fun OnboardingScreen(onFinished: (name: String, role: String) -> Unit) {
    // Step 0 = profile setup, 1+ = feature pages
    var step by remember { mutableIntStateOf(0) }
    var userName by remember { mutableStateOf("") }
    var selectedRole by remember { mutableStateOf("") }
    val nameError = step == 0 && userName.isBlank()

    Scaffold { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Skip / back controls row
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                if (step > 0 && step < featurePages.size) {
                    OutlinedButton(onClick = { onFinished(userName, selectedRole) }) {
                        Text("Skip")
                    }
                }
            }

            // Page content
            AnimatedContent(
                targetState = step,
                transitionSpec = { fadeIn() togetherWith fadeOut() },
                label = "onboarding_step"
            ) { currentStep ->
                if (currentStep == 0) {
                    ProfileSetupPage(
                        name = userName,
                        selectedRole = selectedRole,
                        onNameChange = { userName = it },
                        onRoleSelected = { selectedRole = it }
                    )
                } else {
                    val page = featurePages[currentStep - 1]
                    OnboardingPageContent(page)
                }
            }

            // Indicator + navigation
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                // Dots: 0 = profile, 1-4 = feature pages
                PageIndicator(pageCount = featurePages.size + 1, currentPage = step)

                Button(
                    onClick = {
                        if (step == 0) {
                            if (userName.isNotBlank()) step++
                        } else if (step < featurePages.size) {
                            step++
                        } else {
                            onFinished(userName, selectedRole)
                        }
                    },
                    enabled = step != 0 || userName.isNotBlank(),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(if (step < featurePages.size) "Next" else "Get Started")
                }
            }
        }
    }
}

@Composable
private fun ProfileSetupPage(
    name: String,
    selectedRole: String,
    onNameChange: (String) -> Unit,
    onRoleSelected: (String) -> Unit
) {
    val focusManager = LocalFocusManager.current
    val focusRequester = remember { FocusRequester() }

    LaunchedEffect(Unit) { focusRequester.requestFocus() }

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(28.dp),
        modifier = Modifier.padding(vertical = 16.dp)
    ) {
        // Avatar icon
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .size(100.dp)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.primaryContainer)
        ) {
            Icon(
                imageVector = Icons.Default.Person,
                contentDescription = null,
                modifier = Modifier.size(56.dp),
                tint = MaterialTheme.colorScheme.onPrimaryContainer
            )
        }

        Text(
            text = "Welcome!",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = "Tell us a bit about yourself to get started.",
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        // Name input
        OutlinedTextField(
            value = name,
            onValueChange = onNameChange,
            label = { Text("Your name") },
            leadingIcon = { Icon(Icons.Default.AccountBox, null) },
            singleLine = true,
            isError = name.isEmpty(),
            keyboardOptions = KeyboardOptions.Default.copy(imeAction = ImeAction.Done),
            keyboardActions = KeyboardActions(onDone = { focusManager.clearFocus() }),
            modifier = Modifier
                .fillMaxWidth()
                .focusRequester(focusRequester)
        )

        // Role selection
        Text(
            text = "I am a…",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.fillMaxWidth()
        )
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            RoleCard(
                icon = Icons.Default.School,
                label = "Student",
                selected = selectedRole == "Student",
                modifier = Modifier.weight(1f),
                onClick = { onRoleSelected("Student") }
            )
            RoleCard(
                icon = Icons.Default.Work,
                label = "Office / Business",
                selected = selectedRole == "Office",
                modifier = Modifier.weight(1f),
                onClick = { onRoleSelected("Office") }
            )
        }
    }
}

@Composable
private fun RoleCard(
    icon: ImageVector,
    label: String,
    selected: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    val borderColor = if (selected) MaterialTheme.colorScheme.primary
                      else MaterialTheme.colorScheme.outlineVariant
    val bgColor = if (selected) MaterialTheme.colorScheme.primaryContainer
                  else MaterialTheme.colorScheme.surfaceVariant

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(bgColor)
            .border(2.dp, borderColor, RoundedCornerShape(16.dp))
            .clickable(onClick = onClick)
            .padding(vertical = 20.dp, horizontal = 12.dp)
    ) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            modifier = Modifier.size(38.dp),
            tint = if (selected) MaterialTheme.colorScheme.primary
                   else MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelLarge,
            fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
            textAlign = TextAlign.Center,
            color = if (selected) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun OnboardingPageContent(page: OnboardingPage) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(24.dp),
        modifier = Modifier.padding(vertical = 32.dp)
    ) {
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .size(120.dp)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.primaryContainer)
        ) {
            Icon(
                imageVector = page.icon,
                contentDescription = null,
                modifier = Modifier.size(56.dp),
                tint = MaterialTheme.colorScheme.onPrimaryContainer
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = page.title,
            style = MaterialTheme.typography.headlineMedium,
            textAlign = TextAlign.Center
        )
        Text(
            text = page.description,
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun PageIndicator(pageCount: Int, currentPage: Int) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        repeat(pageCount) { index ->
            Box(
                modifier = Modifier
                    .size(if (index == currentPage) 12.dp else 8.dp)
                    .clip(CircleShape)
                    .background(
                        if (index == currentPage)
                            MaterialTheme.colorScheme.primary
                        else
                            MaterialTheme.colorScheme.outlineVariant
                    )
            )
        }
    }
}
