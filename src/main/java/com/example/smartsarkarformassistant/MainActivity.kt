package com.example.smartsarkarformassistant

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.smartsarkarformassistant.ui.theme.SmartSarkarFormAssistantTheme

// Design Tokens
val PrimaryBlue = Color(0xFF1A73E8)
val TextDark = Color(0xFF212121)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SmartSarkarFormAssistantTheme {
                // Simple state-based navigation for testing
                var currentScreen by remember { mutableStateOf("language") }

                Surface(modifier = Modifier.fillMaxSize()) {
                    when (currentScreen) {
                        "language" -> LanguageSelectionScreen(onNext = { currentScreen = "voice" })
                        "voice" -> VoiceSetupScreen(onBack = { currentScreen = "language" })
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LanguageSelectionScreen(onNext: () -> Unit) {
    var selectedLanguage by remember { mutableStateOf("English") }
    val languages = listOf("English", "हिन्दी", "नेपाली", "मराठी", "தமிழ்", "తెలుగు", "മലയാളം")

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Select Language", fontSize = 20.sp, fontWeight = FontWeight.Medium) }
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .padding(24.dp)
                .fillMaxSize()
        ) {
            Text(
                "Choose your preferred language",
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                color = TextDark,
                modifier = Modifier.padding(bottom = 24.dp)
            )

            languages.forEach { language ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { selectedLanguage = language }
                        .padding(vertical = 12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    RadioButton(
                        selected = (language == selectedLanguage),
                        onClick = { selectedLanguage = language }
                    )
                    Spacer(modifier = Modifier.width(16.dp))
                    Text(text = language, fontSize = 16.sp)
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            Button(
                onClick = onNext,
                modifier = Modifier.fillMaxWidth().height(56.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue)
            ) {
                Text("Continue", fontSize = 16.sp)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VoiceSetupScreen(onBack: () -> Unit) {
    // State for toggles and sliders
    var useMicrophone by remember { mutableStateOf(true) }
    var readAloud by remember { mutableStateOf(true) }
    var voiceGender by remember { mutableIntStateOf(0) } // 0 for Male, 1 for Female
    var speechSpeed by remember { mutableFloatStateOf(0.5f) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Voice Preferences", fontSize = 20.sp, fontWeight = FontWeight.Medium) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .padding(24.dp)
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            // Permission Section
            Text("Permissions", fontWeight = FontWeight.Bold, color = TextDark)
            Button(
                onClick = { /* Request Mic Permission */ },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFF5F5F5)),
                contentPadding = PaddingValues(16.dp)
            ) {
                Text("Allow Microphone Access", color = PrimaryBlue)
            }

            HorizontalDivider()

            // Toggles Section
            SettingsToggle(
                label = "Use microphone",
                description = "Speak to fill out your forms",
                checked = useMicrophone,
                onCheckedChange = { useMicrophone = it }
            )

            SettingsToggle(
                label = "Read responses aloud",
                description = "Assistant will speak back to you",
                checked = readAloud,
                onCheckedChange = { readAloud = it }
            )

            // Voice Gender Segment Control
            Column {
                Text("Voice Gender", fontWeight = FontWeight.Medium, color = TextDark)
                Spacer(modifier = Modifier.height(12.dp))
                SingleChoiceSegmentedButtonRow(modifier = Modifier.fillMaxWidth()) {
                    SegmentedButton(
                        selected = voiceGender == 0,
                        onClick = { voiceGender = 0 },
                        shape = SegmentedButtonDefaults.itemShape(index = 0, count = 2)
                    ) { Text("Male") }
                    SegmentedButton(
                        selected = voiceGender == 1,
                        onClick = { voiceGender = 1 },
                        shape = SegmentedButtonDefaults.itemShape(index = 1, count = 2)
                    ) { Text("Female") }
                }
            }

            // Speech Speed Slider
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Speech Speed", fontWeight = FontWeight.Medium, color = TextDark)
                    Text(if (speechSpeed < 0.4f) "Slow" else if (speechSpeed > 0.7f) "Fast" else "Normal")
                }
                Slider(
                    value = speechSpeed,
                    onValueChange = { speechSpeed = it },
                    colors = SliderDefaults.colors(thumbColor = PrimaryBlue, activeTrackColor = PrimaryBlue)
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            // Footer Button
            Button(
                onClick = { /* Navigate to Home_Screen */ },
                modifier = Modifier.fillMaxWidth().height(56.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue)
            ) {
                Text("Finish Setup", fontSize = 16.sp)
            }
        }
    }
}

@Composable
fun SettingsToggle(label: String, description: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(label, fontWeight = FontWeight.Medium, color = TextDark)
            Text(description, fontSize = 12.sp, color = Color.Gray)
        }
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            colors = SwitchDefaults.colors(checkedThumbColor = PrimaryBlue)
        )
    }
}
