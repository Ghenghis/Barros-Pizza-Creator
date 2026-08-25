using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Barros.PizzaCreator.AI
{
    public sealed class BackendClient
    {
        private readonly string baseUrl;
        private readonly MainThreadDispatcher dispatcher;

        public BackendClient(string baseUrl, MainThreadDispatcher dispatcher)
        {
            this.baseUrl = (baseUrl ?? "http://127.0.0.1:48173").TrimEnd('/');
            this.dispatcher = dispatcher;
        }

        public void Compose(string endpoint, AiRequest request, Action<AiResponse> callback)
        {
            Post<AiRequest, AiResponse>(endpoint, request, callback);
        }

        public void Transcribe(byte[] wav, Action<TranscriptionResponse> callback)
        {
            TranscriptionRequest request = new TranscriptionRequest();
            request.AudioBase64 = Convert.ToBase64String(wav);
            Post<TranscriptionRequest, TranscriptionResponse>("/transcribe", request, callback);
        }

        public void Health(Action<bool, string> callback)
        {
            ThreadPool.QueueUserWorkItem(delegate
            {
                bool ok = false;
                string message = "Offline";
                try
                {
                    HttpWebRequest request = (HttpWebRequest)WebRequest.Create(baseUrl + "/health");
                    request.Method = "GET";
                    request.Timeout = 2500;
                    using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                    using (StreamReader reader = new StreamReader(response.GetResponseStream()))
                    {
                        string body = reader.ReadToEnd();
                        AiResponse parsed = JsonConvert.DeserializeObject<AiResponse>(body);
                        ok = response.StatusCode == HttpStatusCode.OK;
                        message = parsed != null && !string.IsNullOrEmpty(parsed.Provider) ? parsed.Provider : "Ready";
                    }
                }
                catch (Exception exception) { message = exception.Message; }
                bool result = ok;
                string detail = message;
                dispatcher.Enqueue(delegate { callback(result, detail); });
            });
        }

        public void History(Action<System.Collections.Generic.List<ConversationLine>> callback)
        {
            ThreadPool.QueueUserWorkItem(delegate
            {
                System.Collections.Generic.List<ConversationLine> lines = new System.Collections.Generic.List<ConversationLine>();
                try
                {
                    HttpWebRequest request = (HttpWebRequest)WebRequest.Create(baseUrl + "/history");
                    request.Method = "GET";
                    request.Timeout = 4000;
                    using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                    using (StreamReader reader = new StreamReader(response.GetResponseStream()))
                    {
                        JObject root = JObject.Parse(reader.ReadToEnd());
                        JArray entries = root["entries"] as JArray;
                        if (entries != null)
                        {
                            int start = Math.Max(0, entries.Count - 12);
                            for (int i = start; i < entries.Count; i++)
                            {
                                JObject entry = entries[i] as JObject;
                                if (entry == null) continue;
                                string prompt = entry["prompt"] == null ? "" : entry["prompt"].ToString();
                                JObject responseObject = entry["response"] as JObject;
                                string answer = responseObject == null || responseObject["message"] == null ? "" : responseObject["message"].ToString();
                                if (!string.IsNullOrEmpty(prompt)) lines.Add(new ConversationLine("You (earlier)", prompt));
                                if (!string.IsNullOrEmpty(answer)) lines.Add(new ConversationLine("Barro's AI (earlier)", answer));
                            }
                        }
                    }
                }
                catch { }
                dispatcher.Enqueue(delegate { callback(lines); });
            });
        }

        private void Post<TRequest, TResponse>(string endpoint, TRequest payload, Action<TResponse> callback)
            where TResponse : new()
        {
            ThreadPool.QueueUserWorkItem(delegate
            {
                TResponse result = new TResponse();
                try
                {
                    byte[] data = Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(payload));
                    HttpWebRequest request = (HttpWebRequest)WebRequest.Create(baseUrl + endpoint);
                    request.Method = "POST";
                    request.ContentType = "application/json; charset=utf-8";
                    request.Timeout = 120000;
                    request.ReadWriteTimeout = 120000;
                    request.ContentLength = data.Length;
                    using (Stream stream = request.GetRequestStream()) stream.Write(data, 0, data.Length);
                    using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                    using (StreamReader reader = new StreamReader(response.GetResponseStream()))
                        result = JsonConvert.DeserializeObject<TResponse>(reader.ReadToEnd());
                }
                catch (WebException webException)
                {
                    string error = webException.Message;
                    if (webException.Response != null)
                    {
                        try
                        {
                            using (StreamReader reader = new StreamReader(webException.Response.GetResponseStream()))
                                error = reader.ReadToEnd();
                        }
                        catch { }
                    }
                    ApplyError(result, error);
                }
                catch (Exception exception) { ApplyError(result, exception.Message); }
                TResponse completed = result;
                dispatcher.Enqueue(delegate { callback(completed); });
            });
        }

        private static void ApplyError<T>(T target, string error)
        {
            if (target == null) return;
            try
            {
                string clean = error;
                if (!string.IsNullOrEmpty(error) && error.TrimStart().StartsWith("{"))
                {
                    JObject parsed = JObject.Parse(error);
                    JToken token = parsed["error"];
                    if (token != null) clean = token.ToString();
                }
                System.Reflection.FieldInfo field = target.GetType().GetField("Error");
                if (field != null) field.SetValue(target, clean);
            }
            catch { }
        }
    }
}
