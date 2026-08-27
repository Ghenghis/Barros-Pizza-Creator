using System;
using System.Diagnostics;
using System.IO;
using BepInEx;
using BepInEx.Configuration;
using UnityEngine;

namespace Barros.PizzaCreator.AI
{
    [BepInPlugin("com.barros.pizzacreator.ai", "Barro's AI Pizza Designer", "1.2.0")]
    [BepInProcess("Pizza Connection 3 - Pizza Creator.exe")]
    public sealed class BarrosAiPlugin : BaseUnityPlugin
    {
        private ConfigEntry<string> backendUrl;
        private ConfigEntry<bool> autoStartBackend;
        private ConfigEntry<string> pythonOverride;
        private MainThreadDispatcher dispatcher;
        private GameBridge game;
        private BackendClient backend;
        private RuntimeTabInstaller installer;
        private EvidenceRecorder evidence;
        private Process backendProcess;
        private bool injected;
        private float nextInstallAttempt;

        private void Awake()
        {
            backendUrl = Config.Bind("Backend", "Url", "http://127.0.0.1:48173", "Local AI sidecar URL.");
            autoStartBackend = Config.Bind("Backend", "AutoStart", true, "Start the bundled local sidecar with the game.");
            pythonOverride = Config.Bind("Backend", "PythonExecutable", "", "Optional full path to pythonw.exe.");
            dispatcher = gameObject.AddComponent<MainThreadDispatcher>();
            evidence = new EvidenceRecorder(Logger);
            game = new GameBridge(evidence);
            backend = new BackendClient(backendUrl.Value, dispatcher);
            if (autoStartBackend.Value) StartBackend();
            Logger.LogInfo("Barro's AI Pizza Designer 1.2.0-rc1 loaded. Waiting for Pizza Creator services.");
        }

        private void Update()
        {
            if (!injected && Kernel.InstanceProperty != null && Kernel.InstanceProperty.Value != null)
            {
                try
                {
                    Kernel.InstanceProperty.Value.Inject(game);
                    injected = game.Ready;
                    if (injected)
                    {
                        installer = new RuntimeTabInstaller(game, backend, evidence, Logger);
                        Logger.LogInfo("Injected the live Pizza Creator service and database bridge.");
                    }
                }
                catch (Exception exception) { Logger.LogWarning("Waiting for service injection: " + exception.Message); }
            }
            if (injected && Time.realtimeSinceStartup >= nextInstallAttempt)
            {
                nextInstallAttempt = Time.realtimeSinceStartup + 1.0f;
                if (installer == null || !installer.Installed)
                {
                    installer = new RuntimeTabInstaller(game, backend, evidence, Logger);
                    installer.TryInstall();
                }
            }
            if (Input.GetKeyDown(KeyCode.F10) && installer != null) installer.Activate();
            if (Input.GetKeyDown(KeyCode.F9) && game != null)
            {
                string detail;
                bool verified = game.VerifyLastSavedReload(out detail);
                evidence.Record(verified ? "action.reload.verified" : "action.reload.failed", detail);
                if (verified) evidence.Capture("reload");
                Logger.LogInfo("Reload verification: " + detail);
            }
        }

        private void StartBackend()
        {
            try
            {
                string root = BepInEx.Paths.GameRootPath;
                string package = Path.Combine(root, "BarrosAI");
                string main = Path.Combine(package, "backend", "main.py");
                string settings = Path.Combine(package, "backend", "settings.json");
                string python = pythonOverride.Value;
                if (string.IsNullOrEmpty(python)) python = Path.Combine(package, "runtime", "pythonw.exe");
                if (!File.Exists(python)) python = "pythonw.exe";
                if (!File.Exists(main))
                {
                    Logger.LogError("Backend source not found: " + main);
                    return;
                }
                ProcessStartInfo info = new ProcessStartInfo();
                info.FileName = python;
                info.Arguments = Quote(main) + " --settings " + Quote(settings);
                info.WorkingDirectory = Path.GetDirectoryName(main);
                info.UseShellExecute = false;
                info.CreateNoWindow = true;
                info.WindowStyle = ProcessWindowStyle.Hidden;
                backendProcess = Process.Start(info);
                Logger.LogInfo("Started local AI backend process.");
            }
            catch (Exception exception)
            {
                Logger.LogError("Could not start the local AI backend: " + exception.Message);
            }
        }

        private static string Quote(string value)
        {
            return "\"" + value.Replace("\"", "\\\"") + "\"";
        }

        private void OnApplicationQuit()
        {
            StopBackend();
        }

        private void OnDestroy()
        {
            StopBackend();
        }

        private void StopBackend()
        {
            try
            {
                if (backendProcess != null && !backendProcess.HasExited) backendProcess.Kill();
            }
            catch { }
            backendProcess = null;
        }
    }
}
