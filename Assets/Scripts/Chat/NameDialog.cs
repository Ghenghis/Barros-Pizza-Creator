using creator_ui.Recipe;
using System;
using System.IO;
using UnityEngine;
using UnityEngine.UIElements;

namespace creator_ui.Chat
{
    public class NameDialog : MonoBehaviour
    {
        public UIDocument document;
        public VisualTreeAsset dialogTree;
        public Action<string> onSaved;

        private TextField _input;
        private RecipeData _currentRecipe;

        public void Show(RecipeData recipe)
        {
            _currentRecipe = recipe;
            var root = document.rootVisualElement;
            var layer = root.Q<VisualElement>("dialog-layer");
            if (layer == null)
            {
                layer = new VisualElement { name = "dialog-layer" };
                layer.style.position = Position.Absolute;
                layer.style.left = 0;
                layer.style.right = 0;
                layer.style.top = 0;
                layer.style.bottom = 0;
                root.Add(layer);
            }
            layer.Clear();
            layer.Add(dialogTree.Instantiate());
            _input = root.Q<TextField>("name-dialog__input");
            if (_input != null)
                _input.value = string.IsNullOrEmpty(recipe.name) ? "Pizza Nonamo" : recipe.name;
            var continueBtn = root.Q<Button>("name-dialog__continue");
            var cancelBtn = root.Q<Button>("name-dialog__cancel");
            if (continueBtn != null) continueBtn.clicked += OnContinue;
            if (cancelBtn != null) cancelBtn.clicked += OnCancel;
        }

        private void OnContinue()
        {
            if (_currentRecipe == null) return;
            var name = _input?.value?.Trim() ?? "";
            if (string.IsNullOrEmpty(name)) name = "Pizza Nonamo";
            _currentRecipe.name = name;
            var outDir = Path.Combine(Application.dataPath, "..", "output");
            Directory.CreateDirectory(outDir);
            var recipePath = Path.Combine(outDir, $"{name}.recipe.json");
            var finalPath = Path.Combine(outDir, $"{name}.final.json");
            JsonExporter.WriteRecipe(_currentRecipe, recipePath);
            JsonExporter.WriteFinal(_currentRecipe, finalPath);
            Debug.Log($"[NameDialog] Saved '{name}' to {recipePath} + {finalPath}");
            onSaved?.Invoke(name);
            Close();
        }

        private void OnCancel() => Close();

        private void Close()
        {
            var root = document.rootVisualElement;
            var layer = root.Q<VisualElement>("dialog-layer");
            if (layer != null) layer.Clear();
        }
    }
}
