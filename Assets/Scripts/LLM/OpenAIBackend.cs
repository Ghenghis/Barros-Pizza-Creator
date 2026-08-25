using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace creator_ui.LLM
{
    public class OpenAIBackend
    {
        private readonly HttpClient _http;
        private readonly string _apiKey;
        private readonly string _model;

        public OpenAIBackend(string apiKey, string model = "gpt-4o-mini")
        {
            _apiKey = apiKey;
            _model = model;
            _http = new HttpClient { Timeout = System.TimeSpan.FromSeconds(30) };
        }

        public async Task<string> CompleteAsync(string systemPrompt, string userPrompt)
        {
            _http.DefaultRequestHeaders.Authorization =
                new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", _apiKey);
            var payload = new
            {
                model = _model,
                messages = new[]
                {
                    new LLMMessage { Role = "system", Content = systemPrompt },
                    new LLMMessage { Role = "user", Content = userPrompt }
                },
                temperature = 0.7,
                response_format = new { type = "json_object" }
            };
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var resp = await _http.PostAsync("https://api.openai.com/v1/chat/completions", content);
            resp.EnsureSuccessStatusCode();
            var body = await resp.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(body);
            return doc.RootElement.GetProperty("choices")[0].GetProperty("message").GetProperty("content").GetString();
        }
    }
}
