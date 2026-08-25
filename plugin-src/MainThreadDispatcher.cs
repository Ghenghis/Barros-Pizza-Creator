using System;
using System.Collections.Generic;
using UnityEngine;

namespace Barros.PizzaCreator.AI
{
    public sealed class MainThreadDispatcher : MonoBehaviour
    {
        private readonly Queue<Action> pending = new Queue<Action>();
        private readonly object gate = new object();

        public void Enqueue(Action action)
        {
            if (action == null) return;
            lock (gate) pending.Enqueue(action);
        }

        private void Update()
        {
            while (true)
            {
                Action next = null;
                lock (gate)
                {
                    if (pending.Count > 0) next = pending.Dequeue();
                }
                if (next == null) break;
                try { next(); }
                catch (Exception exception) { Debug.LogException(exception); }
            }
        }
    }
}

