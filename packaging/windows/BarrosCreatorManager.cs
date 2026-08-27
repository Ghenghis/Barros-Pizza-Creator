using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text.RegularExpressions;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: System.Reflection.AssemblyTitle("Barro's Pizza Creator Manager")]
[assembly: System.Reflection.AssemblyDescription("Windows installer, repair, launch and diagnostics manager for Barro's Pizza Creator 1.6")]
[assembly: System.Reflection.AssemblyCompany("Ghenghis")]
[assembly: System.Reflection.AssemblyProduct("Barro's Pizza Creator")]
[assembly: System.Reflection.AssemblyVersion("1.6.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("1.6.0.0")]

namespace BarrosPizzaCreator.Windows
{
    internal static class Program
    {
        internal const string GameExeName = "Pizza Connection 3 - Pizza Creator.exe";
        internal const string AssemblyHash = "ebf8698df7cb4af904c98c299994705ea529efbdf1e8ccb3e7ca8cb42a1cbc1c";
        internal const string FirstpassHash = "f9cbf0951fc4d4b0788c47bbe41a3820fa333d293175bbb7cb398eb4728fd284";
        internal static readonly string PackageRoot = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);

        [STAThread]
        private static int Main(string[] args)
        {
            string gameRoot = GetOption(args, "--game-root");
            if (string.IsNullOrWhiteSpace(gameRoot)) gameRoot = DetectGameRoot();

            try
            {
                if (HasOption(args, "--verify"))
                {
                    string message;
                    bool valid = VerifyGameRoot(gameRoot, out message);
                    Console.WriteLine(message);
                    return valid ? 0 : 2;
                }
                if (HasOption(args, "--install")) return InstallOrRepair(gameRoot);
                if (HasOption(args, "--uninstall")) return Uninstall(gameRoot);
                if (HasOption(args, "--launch")) return LaunchGame(gameRoot);
                if (HasOption(args, "--configure")) return RunTool("CONFIGURE_AI_PROVIDER.ps1", gameRoot);
                if (HasOption(args, "--diagnose")) return RunTool("DIAGNOSE_Barros_AI.ps1", gameRoot);
            }
            catch (Exception exception)
            {
                Log("fatal " + exception);
                Console.Error.WriteLine(exception.Message);
                return 1;
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new ManagerForm(gameRoot));
            return 0;
        }

        internal static bool VerifyGameRoot(string gameRoot, out string message)
        {
            if (string.IsNullOrWhiteSpace(gameRoot))
            {
                message = "Select the folder containing " + GameExeName + ".";
                return false;
            }
            string root = Path.GetFullPath(gameRoot);
            string exe = Path.Combine(root, GameExeName);
            string managed = Path.Combine(root, "Pizza Connection 3 - Pizza Creator_Data", "Managed");
            string assembly = Path.Combine(managed, "Assembly-CSharp.dll");
            string firstpass = Path.Combine(managed, "Assembly-CSharp-firstpass.dll");
            if (!File.Exists(exe) || !File.Exists(assembly) || !File.Exists(firstpass))
            {
                message = "This is not the complete Pizza Creator 0.11.272 folder.";
                return false;
            }
            if (!String.Equals(Sha256(assembly), AssemblyHash, StringComparison.OrdinalIgnoreCase) ||
                !String.Equals(Sha256(firstpass), FirstpassHash, StringComparison.OrdinalIgnoreCase))
            {
                message = "The selected game is a different build. Nothing was changed.";
                return false;
            }
            message = "Verified Pizza Creator 0.11.272 / Unity 2017.3.1p4.";
            return true;
        }

        internal static int InstallOrRepair(string gameRoot)
        {
            string message;
            if (!VerifyGameRoot(gameRoot, out message)) throw new InvalidOperationException(message);
            string bepinex = Path.Combine(PackageRoot, "dependencies", "BepInEx_win_x64_5.4.23.5.zip");
            string python = Path.Combine(PackageRoot, "dependencies", "python-3.12.10-embed-amd64.zip");
            if (!File.Exists(bepinex) || !File.Exists(python))
                throw new FileNotFoundException("The offline dependency archives are missing. Re-extract the complete Windows package.");
            return RunPowerShell("INSTALL_Barros_AI_Designer.ps1", gameRoot,
                "-BepInExArchive " + Quote(bepinex) + " -PythonArchive " + Quote(python) + " -NoGui");
        }

        internal static int Uninstall(string gameRoot)
        {
            if (string.IsNullOrWhiteSpace(gameRoot)) return 0;
            string exe = Path.Combine(gameRoot, GameExeName);
            if (!File.Exists(exe)) return 0;
            return RunPowerShell("UNINSTALL_Barros_AI_Designer.ps1", gameRoot, "");
        }

        internal static int LaunchGame(string gameRoot)
        {
            string message;
            if (!VerifyGameRoot(gameRoot, out message)) throw new InvalidOperationException(message);
            Process.Start(new ProcessStartInfo(Path.Combine(gameRoot, GameExeName)) { UseShellExecute = true });
            return 0;
        }

        internal static int RunTool(string scriptName, string gameRoot)
        {
            string message;
            if (!VerifyGameRoot(gameRoot, out message)) throw new InvalidOperationException(message);
            return RunPowerShell(scriptName, gameRoot, "");
        }

        internal static string DetectGameRoot()
        {
            List<string> candidates = new List<string>();
            string stored = ReadRegistryGameRoot();
            if (!String.IsNullOrWhiteSpace(stored)) candidates.Add(stored);
            candidates.Add(PackageRoot);
            string steam = ReadSteamPath();
            if (!String.IsNullOrWhiteSpace(steam)) AddSteamCandidates(candidates, steam);
            string programFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);
            candidates.Add(Path.Combine(programFiles, "Steam", "steamapps", "common", "Pizza Connection 3 - Pizza Creator"));
            candidates.Add(@"S:\Unity_Games\PC3 - Pizza Creator");

            foreach (string candidate in candidates)
            {
                string message;
                try { if (VerifyGameRoot(candidate, out message)) return Path.GetFullPath(candidate); }
                catch { }
            }
            return "";
        }

        private static void AddSteamCandidates(List<string> candidates, string steamRoot)
        {
            candidates.Add(Path.Combine(steamRoot, "steamapps", "common", "Pizza Connection 3 - Pizza Creator"));
            string libraries = Path.Combine(steamRoot, "steamapps", "libraryfolders.vdf");
            if (!File.Exists(libraries)) return;
            foreach (Match match in Regex.Matches(File.ReadAllText(libraries), "\\\"path\\\"\\s+\\\"([^\\\"]+)\\\""))
            {
                string path = match.Groups[1].Value.Replace("\\\\", "\\");
                candidates.Add(Path.Combine(path, "steamapps", "common", "Pizza Connection 3 - Pizza Creator"));
            }
        }

        private static string ReadSteamPath()
        {
            object value = Registry.GetValue(@"HKEY_CURRENT_USER\Software\Valve\Steam", "SteamPath", null);
            if (value == null) value = Registry.GetValue(@"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath", null);
            return value == null ? "" : Convert.ToString(value);
        }

        private static string ReadRegistryGameRoot()
        {
            object value = Registry.GetValue(@"HKEY_LOCAL_MACHINE\SOFTWARE\BarrosPizzaCreator", "GameRoot", null);
            return value == null ? "" : Convert.ToString(value);
        }

        private static int RunPowerShell(string scriptName, string gameRoot, string extraArguments)
        {
            string script = Path.Combine(PackageRoot, scriptName);
            if (!File.Exists(script)) throw new FileNotFoundException("Package file is missing.", script);
            string arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File " + Quote(script) +
                " -GameRoot " + Quote(Path.GetFullPath(gameRoot));
            if (!String.IsNullOrWhiteSpace(extraArguments)) arguments += " " + extraArguments;
            ProcessStartInfo info = new ProcessStartInfo("powershell.exe", arguments);
            info.WorkingDirectory = PackageRoot;
            bool administrator = IsAdministrator();
            info.UseShellExecute = !administrator;
            if (administrator)
            {
                info.CreateNoWindow = true;
                info.RedirectStandardOutput = true;
                info.RedirectStandardError = true;
            }
            else
            {
                info.Verb = "runas";
                info.WindowStyle = ProcessWindowStyle.Hidden;
            }
            Log("run script=" + scriptName + " administrator=" + administrator + " game=" + gameRoot);
            using (Process process = Process.Start(info))
            {
                string output = administrator ? process.StandardOutput.ReadToEnd() : "";
                string error = administrator ? process.StandardError.ReadToEnd() : "";
                process.WaitForExit();
                if (!String.IsNullOrWhiteSpace(output)) Log("stdout " + output.Trim());
                if (!String.IsNullOrWhiteSpace(error)) Log("stderr " + error.Trim());
                Log("exit " + process.ExitCode);
                return process.ExitCode;
            }
        }

        private static void Log(string text)
        {
            try
            {
                string directory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "BarrosPizzaCreator");
                Directory.CreateDirectory(directory);
                File.AppendAllText(Path.Combine(directory, "manager.log"), DateTime.UtcNow.ToString("o") + " " + text + Environment.NewLine);
            }
            catch { }
        }

        private static bool IsAdministrator()
        {
            WindowsPrincipal principal = new WindowsPrincipal(WindowsIdentity.GetCurrent());
            return principal.IsInRole(WindowsBuiltInRole.Administrator);
        }

        private static string Sha256(string path)
        {
            using (SHA256 hash = SHA256.Create())
            using (FileStream stream = File.OpenRead(path))
            {
                return BitConverter.ToString(hash.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
            }
        }

        private static string Quote(string value) { return "\"" + value.Replace("\"", "\\\"") + "\""; }
        private static bool HasOption(string[] args, string name)
        {
            foreach (string value in args) if (String.Equals(value, name, StringComparison.OrdinalIgnoreCase)) return true;
            return false;
        }
        private static string GetOption(string[] args, string name)
        {
            for (int i = 0; i + 1 < args.Length; i++)
                if (String.Equals(args[i], name, StringComparison.OrdinalIgnoreCase)) return args[i + 1];
            return "";
        }
    }

    internal sealed class ManagerForm : Form
    {
        private readonly TextBox gameRoot = new TextBox();
        private readonly Label status = new Label();

        internal ManagerForm(string detectedRoot)
        {
            Text = "Barro's Pizza Creator 1.6 — Windows Manager";
            StartPosition = FormStartPosition.CenterScreen;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            ClientSize = new Size(700, 430);
            BackColor = Color.FromArgb(42, 30, 29);
            ForeColor = Color.FromArgb(247, 224, 209);
            Font = new Font("Segoe UI", 10f);

            Label title = MakeLabel("BARRO'S PIZZA CREATOR", 24f, FontStyle.Bold, 28, 22, 640, 42);
            title.ForeColor = Color.FromArgb(239, 214, 199);
            Controls.Add(title);
            Controls.Add(MakeLabel("Complete offline v1.6 add-on manager for an existing Pizza Creator installation", 11f,
                FontStyle.Regular, 30, 68, 640, 28));
            Controls.Add(MakeLabel("Pizza Creator folder", 10f, FontStyle.Bold, 30, 112, 300, 24));

            gameRoot.SetBounds(30, 140, 545, 30);
            gameRoot.Text = detectedRoot ?? "";
            Controls.Add(gameRoot);
            Button browse = MakeButton("Browse…", 585, 139, 85, 32);
            browse.Click += delegate { Browse(); };
            Controls.Add(browse);

            AddAction("INSTALL / REPAIR", 30, 196, delegate { Run("Installing the complete add-on…", Program.InstallOrRepair); });
            AddAction("LAUNCH GAME", 250, 196, delegate { Run("Launching Pizza Creator…", Program.LaunchGame); });
            AddAction("CONFIGURE AI + VOICE", 470, 196, delegate { Run("Opening provider and voice setup…", delegate(string root) { return Program.RunTool("CONFIGURE_AI_PROVIDER.ps1", root); }); });
            AddAction("RUN DIAGNOSTICS", 30, 252, delegate { Run("Checking the installation…", delegate(string root) { return Program.RunTool("DIAGNOSE_Barros_AI.ps1", root); }); });
            AddAction("REMOVE ADD-ON", 250, 252, delegate { Run("Removing only Barro's add-on files…", Program.Uninstall); });
            AddAction("VERIFY GAME", 470, 252, Verify);

            status.SetBounds(30, 325, 640, 58);
            status.BorderStyle = BorderStyle.FixedSingle;
            status.Padding = new Padding(10);
            status.TextAlign = ContentAlignment.MiddleLeft;
            status.Text = "Choose Verify Game, then Install / Repair. Original game assemblies and saves are never replaced.";
            Controls.Add(status);
            Controls.Add(MakeLabel("Commercial Pizza Creator game files are not included in this package.", 9f,
                FontStyle.Italic, 31, 394, 630, 24));
        }

        private void AddAction(string text, int x, int y, Action action)
        {
            Button button = MakeButton(text, x, y, 200, 42);
            button.Click += delegate { action(); };
            Controls.Add(button);
        }

        private void Verify()
        {
            string message;
            bool valid = Program.VerifyGameRoot(gameRoot.Text, out message);
            status.Text = (valid ? "PASS — " : "NOT READY — ") + message;
        }

        private void Run(string workingMessage, Func<string, int> operation)
        {
            try
            {
                status.Text = workingMessage;
                Refresh();
                int code = operation(gameRoot.Text);
                status.Text = code == 0 ? "PASS — operation completed successfully." : "FAILED — operation returned code " + code + ".";
            }
            catch (Exception exception)
            {
                status.Text = "FAILED — " + exception.Message;
            }
        }

        private void Browse()
        {
            using (FolderBrowserDialog dialog = new FolderBrowserDialog())
            {
                dialog.Description = "Select the folder containing " + Program.GameExeName;
                dialog.ShowNewFolderButton = false;
                if (Directory.Exists(gameRoot.Text)) dialog.SelectedPath = gameRoot.Text;
                if (dialog.ShowDialog(this) == DialogResult.OK) gameRoot.Text = dialog.SelectedPath;
            }
            Verify();
        }

        private Label MakeLabel(string text, float size, FontStyle style, int x, int y, int width, int height)
        {
            Label label = new Label();
            label.Text = text;
            label.Font = new Font("Segoe UI", size, style);
            label.SetBounds(x, y, width, height);
            return label;
        }

        private Button MakeButton(string text, int x, int y, int width, int height)
        {
            Button button = new Button();
            button.Text = text;
            button.SetBounds(x, y, width, height);
            button.FlatStyle = FlatStyle.Flat;
            button.BackColor = Color.FromArgb(110, 31, 33);
            button.ForeColor = Color.White;
            button.FlatAppearance.BorderColor = Color.FromArgb(173, 41, 46);
            return button;
        }
    }
}
