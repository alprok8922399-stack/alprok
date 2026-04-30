# chat_text_only.py — упрощённая версия: загрузка модели, CLI, история, команды llm_on/llm_off/load_model
import os, joblib, sys
MODEL_PATH = "models/logreg_calibrated.pkl"

def load_model(path=MODEL_PATH):
    if os.path.exists(path):
        return joblib.load(path)
    return None

model = load_model()
history = []
memory = {}

def predict(text):
    X = [text]  # замените на вашу векторизацию
    if model:
        return model.predict(X)[0]
    return "LLM_OFF"

def handle_cmd(cmd):
    global model
    if cmd.startswith("load_model "):
        p = cmd.split(" ",1)[1]
        model = load_model(p)
        return f"loaded:{bool(model)}"
    if cmd=="llm_on":
        memory["llm"] = True
        return "LLM enabled"
    if cmd=="llm_off":
        memory["llm"] = False
        return "LLM disabled"
    return "unknown command"

def loop():
    print("Chat CLI. /exit to quit.")
    while True:
        txt = input("> ").strip()
        if not txt: continue
        if txt=="/exit": break
        if txt.startswith("/cmd "):
            out = handle_cmd(txt[5:])
        else:
            out = predict(txt)
            history.append((txt,out))
        print(out)

if __name__=="__main__":
    loop()
  if __name__ == "__main__":
    if not check_paths("."):
        print("Fix missing files/dirs and rerun.")
        exit(1)
    # существующий код запуска

