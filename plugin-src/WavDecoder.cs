using System;
using System.IO;
using System.Text;
using UnityEngine;

namespace Barros.PizzaCreator.AI
{
    internal static class WavDecoder
    {
        public static AudioClip Decode(byte[] wav, string clipName)
        {
            if (wav == null || wav.Length < 44) throw new InvalidDataException("Voice response was not a complete WAV file.");
            using (MemoryStream stream = new MemoryStream(wav, false))
            using (BinaryReader reader = new BinaryReader(stream, Encoding.ASCII))
            {
                if (ReadTag(reader) != "RIFF") throw new InvalidDataException("Voice response is missing RIFF audio data.");
                reader.ReadInt32();
                if (ReadTag(reader) != "WAVE") throw new InvalidDataException("Voice response is not WAV audio.");

                short format = 0;
                short channels = 0;
                int sampleRate = 0;
                short bits = 0;
                byte[] pcm = null;
                while (stream.Position + 8 <= stream.Length)
                {
                    string tag = ReadTag(reader);
                    int length = reader.ReadInt32();
                    if (length < 0 || stream.Position + length > stream.Length) throw new InvalidDataException("Voice WAV contains an invalid chunk.");
                    if (tag == "fmt ")
                    {
                        format = reader.ReadInt16();
                        channels = reader.ReadInt16();
                        sampleRate = reader.ReadInt32();
                        reader.ReadInt32();
                        reader.ReadInt16();
                        bits = reader.ReadInt16();
                        int remaining = length - 16;
                        if (remaining > 0) reader.ReadBytes(remaining);
                    }
                    else if (tag == "data") pcm = reader.ReadBytes(length);
                    else reader.ReadBytes(length);
                    if ((length & 1) == 1 && stream.Position < stream.Length) reader.ReadByte();
                }
                if (format != 1 || channels < 1 || sampleRate < 8000 || bits != 16 || pcm == null)
                    throw new InvalidDataException("Voice WAV must be 16-bit PCM audio.");
                int sampleCount = pcm.Length / 2;
                int frameCount = sampleCount / channels;
                float[] samples = new float[frameCount * channels];
                for (int i = 0; i < samples.Length; i++)
                {
                    short value = (short)(pcm[i * 2] | (pcm[i * 2 + 1] << 8));
                    samples[i] = value / 32768f;
                }
                AudioClip clip = AudioClip.Create(string.IsNullOrEmpty(clipName) ? "BarrosAgentVoice" : clipName, frameCount, channels, sampleRate, false);
                clip.SetData(samples, 0);
                return clip;
            }
        }

        private static string ReadTag(BinaryReader reader)
        {
            return Encoding.ASCII.GetString(reader.ReadBytes(4));
        }
    }
}
