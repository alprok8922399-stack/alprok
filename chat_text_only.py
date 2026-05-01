#!/usr/bin/env python3
"""
chat_text_only.py
CLI + экспортируемые функции для загрузки модели, предсказаний и простого history/memory.
Поддерживает: load_model, predict, llm_on, llm_off, save_memory, show_history, get_history, get_memory
"""

import os
import sys
import argparse
import json
import joblib
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

# --------------------
# Конфигурация путей
# --------------------
BASE_DIR = Path(__file__).resolve().parent
# предполагаем запуск из корня репозитория: если файл в src/, поднимаемся на уровень выше
if (BASE_DIR / "models").exists():
    ROOT = BASE_DIR
elif BASE_DIR.parent.exists() and (BASE_DIR.parent / "models").exists():
    ROOT = BASE_DIR.parent
else:
    # по умолчанию - родитель каталога
    ROOT = BASE_DIR

MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = DATA_DIR / "history.json"
MEMORY_FILE = DATA_DIR / "memory.json"

# --------------------
# Глобальные состояния
# --------------------
loaded_model = None
loaded_model_name: Optional[str] = None
llm_enabled = False
history: List[Dict[str, Any]] = []
memory: Dict[str, Any] = {}

# По умолчанию указана модель (подставлено автоматически)
DEFAULT_MODEL_NAME = None
# если в models/ есть ровно один файл *.pkl, используем его как default
pkl_list = sorted(MODELS_DIR.glob("*.pkl"))
if len(pkl_list) == 1:
    DEFAULT_MODEL_NAME = pkl_list[0].name
elif len(pkl_list) > 1:
    # выберем последний по алфавиту (обычно версия)
    DEFAULT_MODEL_NAME = pkl_list[-1].name

# --------------------
# Утилиты загрузки/сохранения
# --------------------
def _load_json_file(path: Path, default):
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def _save_json_file(path: Path, obj):
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# Инициализация history/memory при импорте
history = _load_json_file(HISTORY_FILE, [])
memory = _load_json_file(MEMORY_FILE, {})

# --------------------
# Основные функции (API)
# --------------------
def load_model(model_name: Optional[str] = None) -> bool:
    """
    Загрузить модель из MODELS_DIR. Если model_name None — используем DEFAULT_MODEL_NAME или
    последний найденный .pkl в каталоге.
    Возвращает True при успехе.
    """
    global loaded_model, loaded_model_name
    if model_name is None:
        model_name = DEFAULT_MODEL_NAME
    if model_name is None:
        pkl_files = sorted(MODELS_DIR.glob("*.pkl"))
        if not pkl_files:
            print("No .pkl model found in models/ directory.", file=sys.stderr)
            return False
        model_name = pkl_files[-1].name
    model_path = MODELS_DIR / model_name
    if not model_path.exists():
        print(f"Model file not found: {model_path}", file=sys.stderr)
        return False
    try:
        loaded_model = joblib.load(model_path)
        loaded_model_name = model_name
        return True
    except Exception as e:
        print(f"Failed to load model: {e}", file=sys.stderr)
        loaded_model = None
        loaded_model_name = None
        return False

def predict(f1: float, f2: float, f3: float, use_llm: bool = False) -> Dict[str, Any]:
    """
    Сделать предсказание. Возвращает dict: {"prediction": int, "prob": float}
    Добавляет запись в history.
    """
    global history
    if loaded_model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")
    import numpy as np
    X = np.array([[f1, f2, f3]])
    # Попробуем predict_proba, иначе predict
    prob = None
    pred = None
    try:
        probs = loaded_model.predict_proba(X)
        prob = float(probs[0, 1])
        pred = int(prob >= 0.5)
    except Exception:
        try:
            p = loaded_model.predict(X)
            pred = int(p[0])
            prob = 1.0 if pred == 1 else 0.0
        except Exception as e:
            raise RuntimeError(f"Model prediction failed: {e}")
    entry = {
        "timestamp": time.time(),
        "inputs": {"f1": f1, "f2": f2, "f3": f3},
        "prediction": pred,
        "prob": prob,
        "use_llm": bool(use_llm and llm_enabled),
        "model": loaded_model_name,
    }
    history.append(entry)
    # Сохраняем историю сразу
    _save_json_file(HISTORY_FILE, history)
    return {"prediction": pred, "prob": prob}

def llm_on() -> None:
    global llm_enabled
    llm_enabled = True

def llm_off() -> None:
    global llm_enabled
    llm_enabled = False

def save_memory() -> None:
    """
    Сохранить текущую memory в файл.
    """
    _save_json_file(MEMORY_FILE, memory)

def show_history() -> List[Dict[str, Any]]:
    """
    Сохранить и вернуть историю.
    """
    _save_json_file(HISTORY_FILE, history)
    return history

def get_history() -> List[Dict[str, Any]]:
    return history

def get_memory() -> Dict[str, Any]:
    return memory

# Экспортируемые имена
__all__ = [
    "load_model", "predict", "llm_on", "llm_off", "save_memory",
    "show_history", "get_history", "get_memory"
]

# --------------------
# CLI (вызовы функций)
# --------------------
def _cli():
    parser = argparse.ArgumentParser(prog="chat_text_only.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub_load = sub.add_parser("load_model")
    sub_load.add_argument("--model", type=str, default=None)

    sub_predict = sub.add_parser("predict")
    sub_predict.add_argument("--f1", type=float, required=True)
    sub_predict.add_argument("--f2", type=float, required=True)
    sub_predict.add_argument("--f3", type=float, required=True)
    sub_predict.add_argument("--use_llm", action="store_true")

    sub.add_parser("llm_on")
    sub.add_parser("llm_off")
    sub.add_parser("save_memory")
    sub.add_parser("show_history")

    args = parser.parse_args()

    try:
        if args.cmd == "load_model":
            ok = load_model(args.model)
            print("Loaded" if ok else "Load failed")
        elif args.cmd == "predict":
            res = predict(args.f1, args.f2, args.f3, use_llm=args.use_llm)
            print(json.dumps(res))
        elif args.cmd == "llm_on":
            llm_on()
            print("LLM enabled")
        elif args.cmd == "llm_off":
            llm_off()
            print("LLM disabled")
        elif args.cmd == "save_memory":
            save_memory()
            print("Memory saved")
        elif args.cmd == "show_history":
            h = show_history()
            print(json.dumps(h, indent=2))
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    _cli()
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
    
