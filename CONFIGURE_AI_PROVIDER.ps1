[CmdletBinding()]
param([string]$GameRoot = "S:\Unity_Games\PC3 - Pizza Creator")

$ErrorActionPreference = "Stop"
$settingsPath = Join-Path $GameRoot "BarrosAI\backend\settings.json"
if (-not (Test-Path $settingsPath)) { throw "Install Barro's AI Pizza Designer first. Settings not found: $settingsPath" }
$settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$form = New-Object Windows.Forms.Form
$form.Text = "Barro's AI Provider"
$form.Width = 620
$form.Height = 520
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

$help = New-Object Windows.Forms.Label
$help.Left = 24
$help.Top = 335
$help.Width = 546
$help.Height = 66
$help.Text = "Offline works without a model. LM Studio usually uses http://127.0.0.1:1234/v1. Ollama usually uses http://127.0.0.1:11434. OpenAI uses https://api.openai.com/v1. API keys are read at runtime from the environment or .env file and are never bundled."
$form.Controls.Add($help)

$cancel = New-Object Windows.Forms.Button
$cancel.Text = "Cancel"
$cancel.Left = 370
$cancel.Top = 414
$cancel.Width = 95
$cancel.DialogResult = [Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancel)
$save = New-Object Windows.Forms.Button
$save.Text = "Save"
$save.Left = 475
$save.Top = 414
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
    $settings | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $settingsPath -Encoding UTF8
    [Windows.Forms.MessageBox]::Show("Provider settings saved. Restart Pizza Creator to apply them.", "Barro's AI Provider", "OK", "Information") | Out-Null
}

