using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

namespace Barros.PizzaCreator.AI
{
    internal static class FileDialog
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        private class OpenFileName
        {
            public int structSize = 0;
            public IntPtr dlgOwner = IntPtr.Zero;
            public IntPtr instance = IntPtr.Zero;
            public string filter = null;
            public string customFilter = null;
            public int maxCustFilter = 0;
            public int filterIndex = 0;
            public StringBuilder file = null;
            public int maxFile = 0;
            public StringBuilder fileTitle = null;
            public int maxFileTitle = 0;
            public string initialDir = null;
            public string title = null;
            public int flags = 0;
            public short fileOffset = 0;
            public short fileExtension = 0;
            public string defExt = null;
            public IntPtr custData = IntPtr.Zero;
            public IntPtr hook = IntPtr.Zero;
            public string templateName = null;
            public IntPtr reservedPtr = IntPtr.Zero;
            public int reservedInt = 0;
            public int flagsEx = 0;
        }

        [DllImport("comdlg32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool GetOpenFileName([In, Out] OpenFileName ofn);

        public static string PickAttachment()
        {
            OpenFileName value = new OpenFileName();
            value.structSize = Marshal.SizeOf(value);
            value.filter = "Images and recipes\0*.png;*.jpg;*.jpeg;*.webp;*.json;*.txt;*.md\0Images\0*.png;*.jpg;*.jpeg;*.webp\0Recipes and text\0*.json;*.txt;*.md\0All files\0*.*\0";
            value.file = new StringBuilder(4096);
            value.maxFile = value.file.Capacity;
            value.fileTitle = new StringBuilder(512);
            value.maxFileTitle = value.fileTitle.Capacity;
            value.title = "Attach an image, recipe, or note";
            value.flags = 0x00001000 | 0x00000800 | 0x00080000;
            return GetOpenFileName(value) ? value.file.ToString() : "";
        }

        public static AiAttachment ReadAttachment(string path)
        {
            FileInfo info = new FileInfo(path);
            if (!info.Exists) throw new FileNotFoundException("Attachment not found.", path);
            if (info.Length > 4 * 1024 * 1024) throw new InvalidOperationException("Attachments are limited to 4 MB.");
            AiAttachment attachment = new AiAttachment();
            attachment.Name = info.Name;
            string extension = info.Extension.ToLowerInvariant();
            if (extension == ".png") attachment.MimeType = "image/png";
            else if (extension == ".jpg" || extension == ".jpeg") attachment.MimeType = "image/jpeg";
            else if (extension == ".webp") attachment.MimeType = "image/webp";
            else if (extension == ".json") attachment.MimeType = "application/json";
            else attachment.MimeType = "text/plain";
            byte[] bytes = File.ReadAllBytes(path);
            if (attachment.MimeType.StartsWith("text/") || attachment.MimeType == "application/json")
                attachment.Text = Encoding.UTF8.GetString(bytes);
            else
                attachment.DataBase64 = Convert.ToBase64String(bytes);
            return attachment;
        }
    }
}

