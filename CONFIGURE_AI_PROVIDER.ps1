[CmdletBinding()]
param([string]$GameRoot = "S:\Unity_Games\PC3 - Pizza Creator")

$ErrorActionPreference = "Stop"
$settingsPath = Join-Path $GameRoot "BarrosAI\backend\settings.json"
if (-not (Test-Path $settingsPath)) { throw "Install Barro's AI Pizza Designer first. Settings not found: $settingsPath" }
$settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
foreach ($default in @{
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
$form.Height = 680
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
Add-Label "Speech endpoint" 248
$speechEndpoint = Add-TextBox ([string]$settings.stt_endpoint) 248
Add-Label "Speech model" 292
$speechModel = Add-TextBox ([string]$settings.stt_model) 292

Add-Label "Agent voices" 336
$ttsProvider = New-Object Windows.Forms.ComboBox
$ttsProvider.Left = 205
$ttsProvider.Top = 332
$ttsProvider.Width = 365
$ttsProvider.DropDownStyle = "DropDownList"
[void]$ttsProvider.Items.AddRange(@("disabled", "azure"))
$ttsProvider.SelectedItem = [string]$settings.tts_provider
if ($ttsProvider.SelectedIndex -lt 0) { $ttsProvider.SelectedIndex = 0 }
$form.Controls.Add($ttsProvider)
Add-Label "Azure Speech region" 380
$ttsRegion = Add-TextBox ([string]$settings.tts_region) 380
Add-Label "Speech-key environment" 424
$ttsKeyEnvironment = Add-TextBox ([string]$settings.tts_key_env) 424

$help = New-Object Windows.Forms.Label
$help.Left = 24
$help.Top = 468
$help.Width = 546
$help.Height = 86
$help.Text = "Offline works without a model. The approved roster has 24 English voices (12 feminine and 12 masculine). Agent voices are optional and start muted. For Azure voices, choose azure, use westus for this Speech resource, and put the key in the named Windows environment variable or your .env file. Keys are read at runtime and never saved here or bundled."
$form.Controls.Add($help)

$cancel = New-Object Windows.Forms.Button
$cancel.Text = "Cancel"
$cancel.Left = 370
$cancel.Top = 570
$cancel.Width = 95
$cancel.DialogResult = [Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancel)
$save = New-Object Windows.Forms.Button
$save.Text = "Save"
$save.Left = 475
$save.Top = 570
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
    $settings.stt_endpoint = $speechEndpoint.Text.Trim()
    $settings.stt_model = $speechModel.Text.Trim()
    $settings.tts_provider = [string]$ttsProvider.SelectedItem
    $settings.tts_region = $ttsRegion.Text.Trim()
    $settings.tts_endpoint = ""
    $settings.tts_key = ""
    $settings.tts_key_env = $ttsKeyEnvironment.Text.Trim()
    $settings.tts_key_file = ""
    $settings | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $settingsPath -Encoding UTF8
    [Windows.Forms.MessageBox]::Show("Provider settings saved. Restart Pizza Creator to apply them.", "Barro's AI Provider", "OK", "Information") | Out-Null
}
