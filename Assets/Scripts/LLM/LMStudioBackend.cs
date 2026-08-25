using System;
using System.Net.Http;
using System.Threading.Tasks;
using UnityEngine;

namespace creator_ui.LLM
{
    public class LMStudioBackend
    {
        private readonly HttpClient _http;
        private readonly string _baseUrl;
        private readonly string _model;

        public LMStudioBackend(string baseUrl, string model)
        {
            _baseUrl = baseUrl;
            _model = model;
            _http = new HttpClient { Timeout = TimeSpan.FromSeconds(5) };
        }

        public async Task<string> CompleteAsync(string systemPrompt, string userPrompt)
        {
            var messages = new[]
            {
                new LLMMessage("system", systemPrompt),
                new LLMMessage("user", userPrompt)
            };
            // Manual JSON building to avoid System.Text.Json namespace issues
            var payload = "{\"model\":\"" + _model + "\",\"messages\":" +
                          LLMJson.ArrayOf(messages) +
                          ",\"temperature\":0.7,\"response_format\":{\"type\":\"json_object\"}}";
            var content = new StringContent(payload, System.Text.Encoding.UTF8, "application/json");
            var resp = await _http.PostAsync($"{_baseUrl}/v1/chat/completions", content);
            resp.EnsureSuccessStatusCode();
            var body = await resp.Content.ReadAsStringAsync();
            var parsed = JsonUtility.FromJson<LLMResponse>(body);
            return parsed.choices[0].message.content;
        }
    }

    public static class LLMJson
    {
        public static string ArrayOf(LLMMessage[] msgs)
        {
            var sb = new System.Text.StringBuilder("[");
            for (int i = 0; i < msgs.Length; i++)
            {
                if (i > 0) sb.Append(",");
                sb.Append("{\"role\":\"").Append(Escape(msgs[i].role)).Append("\",\"content\":\"").Append(Escape(msgs[i].content)).Append("\"}");
            }
            sb.Append("]");
            return sb.ToString();
        }

        private static string Escape(string s)
        {
            if (s == null) return "";
            return s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\r", "\\r").Replace("\t", "\\t");
        }
    }
}
