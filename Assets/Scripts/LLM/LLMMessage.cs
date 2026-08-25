using System;

namespace creator_ui.LLM
{
    [Serializable]
    public class LLMMessage
    {
        public string role;
        public string content;

        public LLMMessage() { }
        public LLMMessage(string r, string c) { role = r; content = c; }
    }

    [Serializable]
    public class LLMRequest
    {
        public string model;
        public LLMMessage[] messages;
        public float temperature;
        public bool stream;
        public string response_format_type;

        public LLMRequest(string m, LLMMessage[] msgs, float temp, bool stream = false)
        {
            model = m;
            messages = msgs;
            temperature = temp;
            this.stream = stream;
            response_format_type = "json_object";
        }
    }

    [Serializable]
    public class LLMChoice
    {
        public LLMMessage message;
    }

    [Serializable]
    public class LLMResponse
    {
        public LLMChoice[] choices;
    }
}
