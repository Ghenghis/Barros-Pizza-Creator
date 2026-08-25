using System;
using System.Threading.Tasks;

namespace creator_ui.LLM
{
    public class LLMClient
    {
        private readonly LMStudioBackend _lmstudio;
        private readonly OpenAIBackend _openai;

        public LLMClient(LMStudioBackend lmstudio, OpenAIBackend openai)
        {
            _lmstudio = lmstudio;
            _openai = openai;
        }

        public static string MaskKey(string key)
        {
            if (string.IsNullOrEmpty(key) || key.Length < 8) return "****";
            return key.Substring(0, 4) + "..." + key.Substring(key.Length - 4);
        }

        public async Task<string> CompleteAsync(string systemPrompt, string userPrompt)
        {
            try
            {
                return await _lmstudio.CompleteAsync(systemPrompt, userPrompt);
            }
            catch (Exception lmEx)
            {
                UnityEngine.Debug.LogWarning($"[LLMClient] LMStudio failed: {lmEx.Message}. Falling back to OpenAI.");
                try
                {
                    return await _openai.CompleteAsync(systemPrompt, userPrompt);
                }
                catch (Exception openaiEx)
                {
                    throw new Exception(
                        $"No LLM backend available. LMStudio: {lmEx.Message}. OpenAI: {openaiEx.Message}");
                }
            }
        }
    }
}
