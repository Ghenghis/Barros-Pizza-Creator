using System.Text.Json.Serialization;

namespace creator_ui.LLM
{
    public class LLMMessage
    {
        [JsonPropertyName("role")]
        public string Role { get; set; } = "user";

        [JsonPropertyName("content")]
        public string Content { get; set; } = "";
    }
}
