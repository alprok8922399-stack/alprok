#!/usr/bin/env python3
# chat_text_only.py
# Гибридный чат-бот: локальная логика/ML + опциональный облачный LLM
# Требования: см. requirements.txt (логрег, joblib, sklearn, requests и т.д.)

import os
import sys
import argparse
import joblib
import pickle
import json
from typing import Any, Dict, List, Optional

# -----------------------
# Параметры / пути (настройте под устройство)
# -----------------------
MODEL_DIR = "/storage/emulated/0/models"
MODEL_FILENAME = "logreg_calibrated_model.pkl"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)
MEMORY_PATH = "/storage/emulated/0/chat_memory.json"
HISTORY_PATH = "/storage/emulated/0/chat_history.txt"

# -----------------------
# Утилиты
# -----------------------
def check_paths(root: str = ".") -> bool:
    """
    Проверяет и создаёт базовые каталоги и файлы.
    Возвращает True при успехе, False при критической ошибке.
    """
    try:
        # Проверить и создать папку для моделей
        mdl_dir = MODEL_DIR if os.path.isabs(MODEL_DIR) else os.path.join(root, MODEL_DIR)
        if not os.path.exists(mdl_dir):
            os.makedirs(mdl_dir, exist_ok=True)

        # Проверить директорию памяти/истории
        mem_dir = os.path.dirname(MEMORY_PATH) or root
        hist_dir = os.path.dirname(HISTORY_PATH) or root
        if not os.path.exists(mem_dir):
            os.makedirs(mem_dir, exist_ok=True)
        if not os.path.exists(hist_dir):
            os.makedirs(hist_dir, exist_ok=True)

        # Создать пустые файлы, если их нет
        for p, init in [(MEMORY_PATH, "{}"), (HISTORY_PATH, "")]:
            path_abs = p if os.path.isabs(p) else os.path.join(root, p)
            if not os.path.exists(path_abs):
                with open(path_abs, "w", encoding="utf-8") as f:
                    f.write(init)
        return True
    except Exception as e:
        print(f"ERROR: check_paths failed: {e}", file=sys.stderr)
        return False

def load_model(path: str = MODEL_PATH) -> Any:
    """Загружает модель (.pkl или joblib) и возвращает объект."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found: {path}")
    try:
        # Попробовать joblib, затем pickle
        try:
            return joblib.load(path)
        except Exception:
            with open(path, "rb") as f:
                return pickle.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}")

def save_model(model: Any, path: str = MODEL_PATH) -> None:
    """Сохранить модель (joblib)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)

def predict_local(model: Any, features: List[float]) -> Dict[str, Any]:
    """
    Предполагается, что model.predict_proba и model.predict доступны.
    features: список признаков (1D)
    Возвращает dict с label и prob.
    """
    import numpy as np
    X = np.array(features).reshape(1, -1)
    try:
        proba = model.predict_proba(X)[0][1]
    except Exception:
        # fallback: если модель даёт только predict
        pred = int(model.predict(X)[0])
        proba = float(pred)
    label = 1 if proba >= 0.5 else 0
    return {"label": label, "probability": float(proba)}

# -----------------------
# Память / история
# -----------------------
def load_memory(path: str = MEMORY_PATH) -> Dict[str, Any]:
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_memory(mem: Dict[str, Any], path: str = MEMORY_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

def append_history(entry: str, path: str = HISTORY_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def show_history(path: str = HISTORY_PATH, last_n: int = 50) -> None:
    if not os.path.exists(path):
        print("No history.")
        return
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for ln in lines[-last_n:]:
        print(ln.rstrip())

# -----------------------
# LLM stub (опционально подключаемый)
# -----------------------
class LLMClient:
    def __init__(self):
        self.enabled = False
        self.api_key = None
        self.endpoint = None

    def enable(self, api_key: str, endpoint: Optional[str] = None):
        self.enabled = True
        self.api_key = api_key
        self.endpoint = endpoint

    def disable(self):
        self.enabled = False
        self.api_key = None
        self.endpoint = None

    def ask(self, prompt: str) -> str:
        if not self.enabled:
            return "LLM disabled."
        # Заглушка: замените реальным вызовом к облачному LLM
        return f"[LLM response for: {prompt}]"

# -----------------------
# CLI и основной поток
# -----------------------
def parse_args():
    p = argparse.ArgumentParser(description="chat_text_only CLI")
    p.add_argument("--cmd", type=str, default="interactive",
                   help="Commands: interactive, predict, load_model, save_memory, show_history, llm_on, llm_off")
    p.add_argument("--features", type=str, default="",
                   help="Comma-separated features for predict, e.g. '0.1,1.2,0.0'")
    p.add_argument("--model-path", type=str, default=MODEL_PATH)
    p.add_argument("--llm-key", type=str, default="")
    return p.parse_args()

def interactive_loop(model: Optional[Any], llm: LLMClient):
    print("Entering interactive text CLI. Type 'quit' to exit.")
    while True:
        try:
            text = input("> ").strip()
        except EOFError:
            break
        if not text:
            continue
        if text.lower() in ("quit", "exit"):
            break
        if text.startswith("/"):
            # простые команды внутри интерактива
            cmd = text[1:].split()
            if cmd[0] == "llm_on":
                key = cmd[1] if len(cmd) > 1 else ""
                llm.enable(key)
                print("LLM enabled.")
                append_history("SYSTEM: LLM enabled.")
                continue
            if cmd[0] == "llm_off":
                llm.disable()
                print("LLM disabled.")
                append_history("SYSTEM: LLM disabled.")
                continue
            if cmd[0] == "show_history":
                show_history()
                continue
            if cmd[0] == "save_memory":
                mem = load_memory()
                save_memory(mem)
                print("Memory saved.")
                continue
            print("Unknown slash command.")
            continue

        # Обработка сообщения: попытка предсказания локальной моделью, затем опционально LLM
        append_history("USER: " + text)
        response = ""
        if model is not None:
            try:
                # Попытка извлечь числовые признаки из текста (если это простой CSV)
                parts = [float(x) for x in text.split(",")] if "," in text else None
                if parts:
                    pred = predict_local(model, parts)
                    response = f"Local predict: label={pred['label']} prob={pred['probability']:.3f}"
                else:
                    response = "Local model: input not numeric CSV; use features or LLM."
            except Exception as e:
                response = f"Local model error: {e}"
        else:
            response = "No local model loaded."

        if llm.enabled:
            llm_resp = llm.ask(text)
            response += " | LLM: " + llm_resp

        print(response)
        append_history("BOT: " + response)

def main():
    args = parse_args()

    # Проверка путей — вызвать с текущей рабочей директорией
    if not check_paths("."):
        print("check_paths failed — abort.", file=sys.stderr)
        sys.exit(1)

    model = None
    llm = LLMClient()

    # Выполнение команд
    cmd = args.cmd.lower()
    if cmd == "load_model":
        try:
            model = load_model(args.model_path)
            print(f"Model loaded: {args.model_path}")
        except Exception as e:
            print(f"Failed to load model: {e}", file=sys.stderr)
            sys.exit(2)
        return

    if cmd == "predict":
        try:
            model = load_model(args.model_path)
        except Exception as e:
            print(f"Failed to load model for predict: {e}", file=sys.stderr)
            sys.exit(3)
        if not args.features:
            print("No features provided. Use --features '0.1,0.2,0.3'")
            sys.exit(4)
        feats = [float(x) for x in args.features.split(",")]
        out = predict_local(model, feats)
        print(json.dumps(out, ensure_ascii=False))
        return

    if cmd == "llm_on":
        if not args.llm_key:
            print("Provide --llm-key <key>")
            sys.exit(5)
        llm.enable(args.llm_key)
        print("LLM enabled.")
        return

    if cmd == "llm_off":
        llm.disable()
        print("LLM disabled.")
        return

    if cmd == "save_memory":
        mem = load_memory()
        save_memory(mem)
        print("Memory saved.")
        return

    if cmd == "show_history":
        show_history()
        return

    # По умолчанию — интерактивный режим
    try:
        # Попытка загрузить модель, если есть
        if os.path.exists(args.model_path):
            try:
                model = load_model(args.model_path)
                print("Local model loaded.")
            except Exception as e:
                print(f"Warning: failed to load model at start: {e}", file=sys.stderr)
        interactive_loop(model, llm)
    except KeyboardInterrupt:
        print("\nExiting.")

if __name__ == "__main__":
    main()
    
