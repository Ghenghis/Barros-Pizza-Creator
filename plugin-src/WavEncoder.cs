using System;
using System.IO;
using System.Text;
using UnityEngine;

namespace Barros.PizzaCreator.AI
{
    internal static class WavEncoder
    {
        public static byte[] Encode(AudioClip clip)
        {
            if (clip == null) return new byte[0];
            float[] samples = new float[clip.samples * clip.channels];
            clip.GetData(samples, 0);
            using (MemoryStream stream = new MemoryStream())
            using (BinaryWriter writer = new BinaryWriter(stream, Encoding.ASCII))
            {
                int byteCount = samples.Length * 2;
                writer.Write(Encoding.ASCII.GetBytes("RIFF"));
                writer.Write(36 + byteCount);
                writer.Write(Encoding.ASCII.GetBytes("WAVEfmt "));
                writer.Write(16);
                writer.Write((short)1);
                writer.Write((short)clip.channels);
                writer.Write(clip.frequency);
                writer.Write(clip.frequency * clip.channels * 2);
                writer.Write((short)(clip.channels * 2));
                writer.Write((short)16);
                writer.Write(Encoding.ASCII.GetBytes("data"));
                writer.Write(byteCount);
                for (int i = 0; i < samples.Length; i++)
                {
                    float clamped = Mathf.Clamp(samples[i], -1f, 1f);
                    writer.Write((short)(clamped * short.MaxValue));
                }
                return stream.ToArray();
            }
        }
    }
}

