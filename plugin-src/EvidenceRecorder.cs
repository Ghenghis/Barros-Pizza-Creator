using System;
using System.Collections.Generic;
using System.IO;
using BepInEx.Logging;
using Newtonsoft.Json;
using UnityEngine;

namespace Barros.PizzaCreator.AI
{
    public sealed class EvidenceRecorder
    {
        private readonly ManualLogSource log;
        private readonly string sessionId;
        private readonly string evidenceRoot;
        private readonly string eventPath;
        private readonly string screenshotRoot;

        public string EventPath { get { return eventPath; } }
        public string ScreenshotRoot { get { return screenshotRoot; } }

        public EvidenceRecorder(ManualLogSource logger)
        {
            log = logger;
            sessionId = DateTime.UtcNow.ToString("yyyyMMddTHHmmssZ");
            evidenceRoot = Path.Combine(BepInEx.Paths.GameRootPath, "BarrosAI", "evidence");
            eventPath = Path.Combine(evidenceRoot, "runtime-events.jsonl");
            screenshotRoot = Path.Combine(evidenceRoot, "screenshots");
            TryCreateDirectories();
            Record("session.start", "Barro's AI Pizza Designer 1.5.0");
        }

        public void Record(string eventName, string detail)
        {
            try
            {
                TryCreateDirectories();
                Dictionary<string, object> item = new Dictionary<string, object>();
                item["schema"] = 1;
                item["session"] = sessionId;
                item["utc"] = DateTime.UtcNow.ToString("o");
                item["event"] = eventName ?? "unknown";
                item["detail"] = detail ?? "";
                item["screen_width"] = Screen.width;
                item["screen_height"] = Screen.height;
                File.AppendAllText(eventPath, JsonConvert.SerializeObject(item) + Environment.NewLine);
                if (log != null) log.LogInfo("[BARROS_PROOF] event=" + eventName + " detail=" + detail);
            }
            catch (Exception exception)
            {
                if (log != null) log.LogWarning("Could not retain proof event '" + eventName + "': " + exception.Message);
            }
        }

        public string Capture(string evidenceName)
        {
            string safe = SafeName(evidenceName);
            string path = Path.Combine(screenshotRoot, safe + ".png");
            try
            {
                TryCreateDirectories();
                UnityEngine.ScreenCapture.CaptureScreenshot(path);
                Record("screenshot.requested", safe + ".png");
                return path;
            }
            catch (Exception exception)
            {
                Record("screenshot.failed", safe + ": " + exception.Message);
                return "";
            }
        }

        private void TryCreateDirectories()
        {
            Directory.CreateDirectory(evidenceRoot);
            Directory.CreateDirectory(screenshotRoot);
        }

        private static string SafeName(string value)
        {
            string input = string.IsNullOrEmpty(value) ? "capture" : value.ToLowerInvariant();
            char[] invalid = Path.GetInvalidFileNameChars();
            for (int i = 0; i < invalid.Length; i++) input = input.Replace(invalid[i], '-');
            return input.Replace(' ', '-');
        }
    }
}
