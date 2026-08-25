using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace Barros.PizzaCreator.AI
{
    public enum DesignerMode
    {
        Chat,
        Lab,
        Crew,
        Voice
    }

    [Serializable]
    public sealed class AiCatalogSize
    {
        [JsonProperty("size")] public string Size = "Medium";
        [JsonProperty("grams")] public float Grams;
        [JsonProperty("cost")] public float Cost;
    }

    [Serializable]
    public sealed class AiCatalogIngredient
    {
        [JsonProperty("id")] public string Id = "";
        [JsonProperty("name")] public string Name = "";
        [JsonProperty("type_id")] public string TypeId = "";
        [JsonProperty("craziness")] public float Craziness;
        [JsonProperty("sizes")] public List<AiCatalogSize> Sizes = new List<AiCatalogSize>();
    }

    [Serializable]
    public sealed class AiRecipeIngredient
    {
        [JsonProperty("id")] public string Id = "";
        [JsonProperty("size")] public string Size = "Medium";
        [JsonProperty("target_grams")] public float TargetGrams;
        [JsonProperty("distribution")] public string Distribution = "even";
        [JsonProperty("note")] public string Note = "";
        [JsonProperty("repaired_from")] public string RepairedFrom = "";
    }

    [Serializable]
    public sealed class AiRecipeScores
    {
        [JsonProperty("taste")] public float Taste;
        [JsonProperty("cost")] public float Cost;
        [JsonProperty("profit")] public float Profit;
        [JsonProperty("popularity")] public float Popularity;
        [JsonProperty("novelty")] public float Novelty;
        [JsonProperty("originality")] public float Originality;
        [JsonProperty("source")] public string Source = "backend-estimate";
    }

    [Serializable]
    public sealed class AiRecipe
    {
        [JsonProperty("name")] public string Name = "AI Pizza";
        [JsonProperty("summary")] public string Summary = "";
        [JsonProperty("shape")] public string Shape = "Round";
        [JsonProperty("profit_factor")] public float ProfitFactor = 0.6f;
        [JsonProperty("ingredients")] public List<AiRecipeIngredient> Ingredients = new List<AiRecipeIngredient>();
        [JsonProperty("scores")] public AiRecipeScores Scores = new AiRecipeScores();
        [JsonProperty("rationale")] public string Rationale = "";
        [JsonProperty("warnings")] public List<string> Warnings = new List<string>();
        [JsonProperty("seed")] public int Seed;
    }

    [Serializable]
    public sealed class AiAgentOpinion
    {
        [JsonProperty("agent")] public string Agent = "";
        [JsonProperty("role")] public string Role = "";
        [JsonProperty("message")] public string Message = "";
        [JsonProperty("score")] public float Score;
        [JsonProperty("status")] public string Status = "ready";
    }

    [Serializable]
    public sealed class AiConsensus
    {
        [JsonProperty("name")] public string Name = "";
        [JsonProperty("score")] public float Score;
        [JsonProperty("flavor")] public float Flavor;
        [JsonProperty("profit")] public float Profit;
        [JsonProperty("popularity")] public float Popularity;
        [JsonProperty("originality")] public float Originality;
    }

    [Serializable]
    public sealed class AiResponse
    {
        [JsonProperty("ok")] public bool Ok;
        [JsonProperty("message")] public string Message = "";
        [JsonProperty("error")] public string Error = "";
        [JsonProperty("provider")] public string Provider = "";
        [JsonProperty("recipes")] public List<AiRecipe> Recipes = new List<AiRecipe>();
        [JsonProperty("agents")] public List<AiAgentOpinion> Agents = new List<AiAgentOpinion>();
        [JsonProperty("consensus")] public AiConsensus Consensus;
        [JsonProperty("warnings")] public List<string> Warnings = new List<string>();
    }

    [Serializable]
    public sealed class AiConstraints
    {
        [JsonProperty("heat")] public string Heat = "Medium";
        [JsonProperty("shape")] public string Shape = "Round";
        [JsonProperty("price_ceiling")] public float PriceCeiling;
        [JsonProperty("max_ingredients")] public int MaxIngredients = 8;
        [JsonProperty("profit_factor")] public float ProfitFactor = 0.6f;
        [JsonProperty("exclude")] public List<string> Exclude = new List<string>();
    }

    [Serializable]
    public sealed class AiAttachment
    {
        [JsonProperty("name")] public string Name = "";
        [JsonProperty("mime_type")] public string MimeType = "application/octet-stream";
        [JsonProperty("data_base64")] public string DataBase64 = "";
        [JsonProperty("text")] public string Text = "";
    }

    [Serializable]
    public sealed class AiRequest
    {
        [JsonProperty("prompt")] public string Prompt = "";
        [JsonProperty("catalog")] public List<AiCatalogIngredient> Catalog = new List<AiCatalogIngredient>();
        [JsonProperty("constraints")] public AiConstraints Constraints = new AiConstraints();
        [JsonProperty("count")] public int Count = 1;
        [JsonProperty("seed")] public int Seed;
        [JsonProperty("current_pizza")] public string CurrentPizza = "";
        [JsonProperty("attachments")] public List<AiAttachment> Attachments = new List<AiAttachment>();
    }

    [Serializable]
    public sealed class TranscriptionRequest
    {
        [JsonProperty("audio_base64")] public string AudioBase64 = "";
        [JsonProperty("filename")] public string Filename = "voice.wav";
    }

    [Serializable]
    public sealed class TranscriptionResponse
    {
        [JsonProperty("ok")] public bool Ok;
        [JsonProperty("text")] public string Text = "";
        [JsonProperty("error")] public string Error = "";
    }

    public sealed class ConversationLine
    {
        public string Speaker;
        public string Text;
        public DateTime Time;

        public ConversationLine(string speaker, string text)
        {
            Speaker = speaker;
            Text = text;
            Time = DateTime.Now;
        }
    }
}

