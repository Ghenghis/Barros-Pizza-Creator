[CmdletBinding()]
param([string]$GameRoot = "S:\Unity_Games\PC3 - Pizza Creator")

$ErrorActionPreference = "Stop"
$settingsPath = Join-Path $GameRoot "BarrosAI\backend\settings.json"
if (-not (Test-Path $settingsPath)) { throw "Install Barro's AI Pizza Designer first. Settings not found: $settingsPath" }
$settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
foreach ($default in @{
    stt_provider = "disabled"
    stt_region = "westus"
    stt_language = "en-US"
    stt_key = ""
    stt_key_env = "AZURE_SPEECH_KEY"
    stt_key_file = ""
    tts_provider = "disabled"
    tts_region = "westus"
    tts_endpoint = ""
    tts_key = ""
    tts_key_env = "AZURE_SPEECH_KEY"
    tts_key_file = ""
}.GetEnumerator()) {
    if ($settings.PSObject.Properties.Name -notcontains $default.Key) {
        $settings | Add-Member -NotePropertyName $default.Key -NotePropertyValue $default.Value
    }
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$form = New-Object Windows.Forms.Form
$form.Text = "Barro's AI Provider & Voices"
$form.Width = 620
$form.Height = 760
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = [Drawing.Color]::FromArgb(235, 194, 166)

function Add-Label([string]$text, [int]$y) {
    $label = New-Object Windows.Forms.Label
    $label.Text = $text
    $label.Left = 24
    $label.Top = $y
    $label.Width = 180
    $form.Controls.Add($label)
}
function Add-TextBox([string]$value, [int]$y) {
    $box = New-Object Windows.Forms.TextBox
    $box.Text = $value
    $box.Left = 205
    $box.Top = $y - 3
    $box.Width = 365
    $form.Controls.Add($box)
    return $box
}

Add-Label "Provider" 28
$provider = New-Object Windows.Forms.ComboBox
$provider.Left = 205
$provider.Top = 24
$provider.Width = 365
$provider.DropDownStyle = "DropDownList"
[void]$provider.Items.AddRange(@("offline", "openai-compatible", "ollama", "anthropic"))
$provider.SelectedItem = [string]$settings.provider
if ($provider.SelectedIndex -lt 0) { $provider.SelectedIndex = 0 }
$form.Controls.Add($provider)

Add-Label "Endpoint" 72
$endpoint = Add-TextBox ([string]$settings.endpoint) 72
Add-Label "Model" 116
$model = Add-TextBox ([string]$settings.model) 116
Add-Label "API-key environment" 160
$keyEnvironment = Add-TextBox ([string]$settings.api_key_env) 160
Add-Label "Optional .env file" 204
$envFile = Add-TextBox ([string]$settings.env_file) 204
Add-Label "Voice input" 248
$sttProvider = New-Object Windows.Forms.ComboBox
$sttProvider.Left = 205
$sttProvider.Top = 244
$sttProvider.Width = 365
$sttProvider.DropDownStyle = "DropDownList"
[void]$sttProvider.Items.AddRange(@("disabled", "azure", "openai-compatible"))
$sttProvider.SelectedItem = [string]$settings.stt_provider
if ($sttProvider.SelectedIndex -lt 0) { $sttProvider.SelectedIndex = 0 }
$form.Controls.Add($sttProvider)
Add-Label "STT endpoint (optional)" 292
$speechEndpoint = Add-TextBox ([string]$settings.stt_endpoint) 292
Add-Label "Speech language" 336
$speechLanguage = Add-TextBox ([string]$settings.stt_language) 336

Add-Label "Agent voices" 380
$ttsProvider = New-Object Windows.Forms.ComboBox
$ttsProvider.Left = 205
$ttsProvider.Top = 376
$ttsProvider.Width = 365
$ttsProvider.DropDownStyle = "DropDownList"
[void]$ttsProvider.Items.AddRange(@("disabled", "azure"))
$ttsProvider.SelectedItem = [string]$settings.tts_provider
if ($ttsProvider.SelectedIndex -lt 0) { $ttsProvider.SelectedIndex = 0 }
$form.Controls.Add($ttsProvider)
Add-Label "Azure Speech region" 424
$ttsRegion = Add-TextBox ([string]$settings.tts_region) 424
Add-Label "Azure-key environment" 468
$ttsKeyEnvironment = Add-TextBox ([string]$settings.tts_key_env) 468

$help = New-Object Windows.Forms.Label
$help.Left = 24
$help.Top = 512
$help.Width = 546
$help.Height = 105
$help.Text = "Offline design works without a model. For interactive voice, choose Azure for Voice input and Agent voices, use westus, and reference AZURE_SPEECH_KEY from a private environment or .env file. The approved roster has 24 English voices. Voices start muted. Keys are read at runtime and are never written here or bundled."
$form.Controls.Add($help)

$cancel = New-Object Windows.Forms.Button
$cancel.Text = "Cancel"
$cancel.Left = 370
$cancel.Top = 650
$cancel.Width = 95
$cancel.DialogResult = [Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancel)
$save = New-Object Windows.Forms.Button
$save.Text = "Save"
$save.Left = 475
$save.Top = 650
$save.Width = 95
$save.BackColor = [Drawing.Color]::FromArgb(167, 43, 47)
$save.ForeColor = [Drawing.Color]::White
$save.DialogResult = [Windows.Forms.DialogResult]::OK
$form.Controls.Add($save)
$form.AcceptButton = $save
$form.CancelButton = $cancel

if ($form.ShowDialog() -eq [Windows.Forms.DialogResult]::OK) {
    $settings.provider = [string]$provider.SelectedItem
    $settings.endpoint = $endpoint.Text.Trim()
    $settings.model = $model.Text.Trim()
    $settings.api_key = ""
    $settings.api_key_env = $keyEnvironment.Text.Trim()
    $settings.env_file = $envFile.Text.Trim()
    $settings.stt_provider = [string]$sttProvider.SelectedItem
    $settings.stt_endpoint = $speechEndpoint.Text.Trim()
    $settings.stt_region = $ttsRegion.Text.Trim()
    $settings.stt_language = $speechLanguage.Text.Trim()
    $settings.stt_key = ""
    $settings.stt_key_env = $ttsKeyEnvironment.Text.Trim()
    $settings.stt_key_file = ""
    $settings.tts_provider = [string]$ttsProvider.SelectedItem
    $settings.tts_region = $ttsRegion.Text.Trim()
    $settings.tts_endpoint = ""
    $settings.tts_key = ""
    $settings.tts_key_env = $ttsKeyEnvironment.Text.Trim()
    $settings.tts_key_file = ""
    $settings | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $settingsPath -Encoding UTF8
    [Windows.Forms.MessageBox]::Show("Provider settings saved. Restart Pizza Creator to apply them.", "Barro's AI Provider", "OK", "Information") | Out-Null
}
