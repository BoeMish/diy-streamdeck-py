import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

# ─── Проверка и установка библиотек ──────────────────────────────────────────
REQUIRED_LIBS = {
    "pygame":       "pygame",
    "serial":       "pyserial",
    "pyautogui":    "pyautogui",
    "pystray":      "pystray",
    "PIL":          "pillow",
}

def check_libraries():
    missing = []
    for import_name, pip_name in REQUIRED_LIBS.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append((import_name, pip_name))
    return missing

def install_libraries(pip_names, log_widget):
    for pip_name in pip_names:
        log_widget.insert("end", f"\n📦 Устанавливаю {pip_name}...\n")
        log_widget.see("end")
        log_widget.update()
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pip_name],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                log_widget.insert("end", f"✅ {pip_name} установлен\n")
            else:
                log_widget.insert("end", f"❌ Ошибка: {result.stderr}\n")
        except Exception as e:
            log_widget.insert("end", f"❌ Исключение: {e}\n")
        log_widget.see("end")
        log_widget.update()

def show_library_check_window():
    missing = check_libraries()
    if not missing:
        return True

    result = {"ok": False}

    root = tk.Tk()
    root.title("ConsoleDeck — Проверка зависимостей")
    root.resizable(False, False)
    root.geometry("460x380")

    tk.Label(root, text="Проверка библиотек", font=("Segoe UI", 13, "bold")).pack(pady=(16, 4))
    tk.Label(root, text="Следующие библиотеки не установлены:", font=("Segoe UI", 10)).pack()

    frame_list = tk.Frame(root, bd=1, relief="sunken")
    frame_list.pack(padx=20, pady=8, fill="x")
    for import_name, pip_name in missing:
        row = tk.Frame(frame_list)
        row.pack(fill="x", padx=8, pady=2)
        tk.Label(row, text="❌", width=3).pack(side="left")
        tk.Label(row, text=pip_name, font=("Segoe UI", 10, "bold"), width=14, anchor="w").pack(side="left")
        tk.Label(row, text=f"(import {import_name})", fg="gray", font=("Segoe UI", 9)).pack(side="left")

    log_frame = tk.Frame(root)
    log_frame.pack(padx=20, pady=4, fill="both", expand=True)
    log = tk.Text(log_frame, height=6, font=("Consolas", 9), state="normal", bg="#1e1e1e", fg="#cccccc")
    log.pack(fill="both", expand=True)
    log.insert("end", "Нажми «Установить» чтобы начать...\n")
    log.config(state="disabled")

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    def on_continue():
        result["ok"] = True
        root.destroy()

    def on_skip():
        result["ok"] = False
        root.destroy()

    def patch_continue():
        nonlocal result
        result["ok"] = True
        root.destroy()

    def do_install_fixed():
        log.config(state="normal")
        log.delete("1.0", "end")
        btn_install.config(state="disabled")
        btn_skip.config(state="disabled")

        pip_names = [pip for _, pip in missing]
        install_libraries(pip_names, log)

        still_missing = check_libraries()
        if not still_missing:
            log.insert("end", "\n✅ Все библиотеки установлены! Можно продолжить.\n")
            log.see("end")
            log.config(state="disabled")
            tk.Button(btn_frame, text="Продолжить →",
                      bg="#228822", fg="white", padx=12,
                      command=patch_continue).pack(side="left", padx=6)
        else:
            names = ", ".join(p for _, p in still_missing)
            log.insert("end", f"\n⚠️ Не удалось установить: {names}\nПопробуй вручную:\npip install {names}\n")
            log.config(state="disabled")
            btn_install.config(state="normal")
            btn_skip.config(state="normal")

    btn_install = tk.Button(btn_frame, text="📦 Установить всё",
                             bg="#4466cc", fg="white", padx=12, command=do_install_fixed)
    btn_install.pack(side="left", padx=6)

    btn_skip = tk.Button(btn_frame, text="Пропустить", command=on_skip)
    btn_skip.pack(side="left", padx=6)

    root.mainloop()
    return result["ok"]


# ─── Остальные импорты (после проверки) ──────────────────────────────────────
def run_app():
    import pygame
    import json
    import os
    import webbrowser
    import serial
    import serial.tools.list_ports
    import threading
    import time
    import argparse
    import pyautogui
    import pystray
    from PIL import Image, ImageDraw
    from tkinter import filedialog

    BAUDRATE    = 9600
    SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
    SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")

    FONT = FONT_SMALL = FONT_TINY = FONT_BOLD = SCREEN = None
    _desktop_toggle_state = {}

    BG          = (18, 18, 24)
    BTN_NONE    = (38, 38, 50)
    BTN_LINK    = (30, 80, 200)
    BTN_EXE     = (180, 80, 20)
    BTN_HOTKEY  = (20, 150, 90)
    BTN_DESKTOP = (120, 30, 170)
    TEXT_WHITE  = (240, 240, 240)
    TEXT_DIM    = (140, 140, 160)
    TEXT_GREEN  = (80, 200, 120)

    TYPE_COLORS = {
        "link": BTN_LINK, "exe": BTN_EXE,
        "hotkey": BTN_HOTKEY, "desktop_switch": BTN_DESKTOP, "none": BTN_NONE,
    }
    TYPE_ICONS = {
        "link": "🔗", "exe": "⚙", "hotkey": "⌨", "desktop_switch": "🖥", "none": "+",
    }

    # ── ЖЕЛЕЗОБЕТОННЫЙ ФИКС ДЛЯ РУССКОЙ РАСКЛАДКИ ──
    def apply_ru_shortcuts(window):
        def on_ctrl_key(event):
            # Аппаратные keycode кнопок на Windows (не зависят от языка)
            # 86 = V, 67 = C, 88 = X, 65 = A
            if event.keycode == 86:
                event.widget.event_generate("<<Paste>>")
                return "break"
            elif event.keycode == 67:
                event.widget.event_generate("<<Copy>>")
                return "break"
            elif event.keycode == 88:
                event.widget.event_generate("<<Cut>>")
                return "break"
            elif event.keycode == 65:
                try:
                    event.widget.select_range(0, 'end')
                    event.widget.icursor('end')
                except Exception:
                    pass
                return "break"
        # Перехватываем все нажатия при зажатом Control
        window.bind("<Control-KeyPress>", on_ctrl_key)

    # ── Настройки ──
    def load_settings():
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_settings(settings):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)

    def get_available_ports():
        return [p.device for p in serial.tools.list_ports.comports()]

    def setup_wizard():
        root = tk.Tk()
        apply_ru_shortcuts(root)
        root.title("ConsoleDeck — Первый запуск")
        root.resizable(False, False)
        root.geometry("420x260")

        tk.Label(root, text="Добро пожаловать в ConsoleDeck!",
                 font=("Segoe UI", 13, "bold")).pack(pady=(18, 4))
        tk.Label(root, text="Настройте параметры перед началом работы.",
                 font=("Segoe UI", 10)).pack(pady=(0, 14))

        folder_var = tk.StringVar(value=SCRIPT_DIR)
        frame_folder = tk.Frame(root)
        frame_folder.pack(fill="x", padx=20, pady=4)
        tk.Label(frame_folder, text="Папка для конфига:", width=20, anchor="w").pack(side="left")
        tk.Entry(frame_folder, textvariable=folder_var, width=22).pack(side="left", padx=4)
        def pick_folder():
            p = filedialog.askdirectory(title="Выбери папку")
            if p: folder_var.set(p)
        tk.Button(frame_folder, text="Обзор", command=pick_folder).pack(side="left")

        ports = get_available_ports()
        port_var = tk.StringVar(value=ports[0] if ports else "")
        frame_port = tk.Frame(root)
        frame_port.pack(fill="x", padx=20, pady=4)
        tk.Label(frame_port, text="Порт Arduino:", width=20, anchor="w").pack(side="left")
        if ports:
            tk.OptionMenu(frame_port, port_var, *ports).pack(side="left", padx=4)
        else:
            tk.Entry(frame_port, textvariable=port_var, width=10).pack(side="left", padx=4)

        def refresh_ports():
            new_ports = get_available_ports()
            port_var.set(new_ports[0] if new_ports else "")
            messagebox.showinfo("Порты", f"Найдено: {', '.join(new_ports) if new_ports else 'ничего'}")
        tk.Button(frame_port, text="🔄", command=refresh_ports).pack(side="left")

        result = {}
        def on_save():
            if not port_var.get().strip():
                messagebox.showwarning("Внимание", "Укажи порт Arduino")
                return
            result["config_dir"] = folder_var.get()
            result["port"] = port_var.get().strip()
            root.destroy()
        def on_skip():
            result["config_dir"] = folder_var.get()
            result["port"] = port_var.get().strip() or "COM5"
            root.destroy()

        frame_btns = tk.Frame(root)
        frame_btns.pack(pady=16)
        tk.Button(frame_btns, text="Сохранить и запустить", command=on_save,
                  bg="#4466cc", fg="white", padx=10).pack(side="left", padx=6)
        tk.Button(frame_btns, text="Пропустить", command=on_skip).pack(side="left", padx=6)

        root.mainloop()
        return result

    def get_or_create_settings():
        settings = load_settings()
        if "config_dir" not in settings or "port" not in settings:
            result = setup_wizard()
            if result:
                settings.update(result)
                save_settings(settings)
        return settings

    # ── Трей ──
    def create_tray_icon():
        img = Image.new("RGB", (64, 64), color=(70, 70, 200))
        ImageDraw.Draw(img).rectangle([10, 10, 54, 54], fill=(255, 255, 255))
        
        def open_settings(icon, item):
            import subprocess
            subprocess.Popen([sys.executable, __file__, "--gui"])

        def on_quit(icon, item):
            icon.stop(); os._exit(0)
            
        menu = pystray.Menu(
            pystray.MenuItem("Настройки", open_settings),
            pystray.MenuItem("Выход", on_quit)
        )
        icon = pystray.Icon("ConsoleDeck", img, "ConsoleDeck", menu)
        threading.Thread(target=icon.run, daemon=True).start()

    def switch_desktop(direction):
        pyautogui.hotkey("ctrl", "win", "left" if direction == "left" else "right")

    def press_hotkey(keys_str):
        keys = [k.strip().lower() for k in keys_str.split("+") if k.strip()]
        if keys: pyautogui.hotkey(*keys)

    def init_pygame():
        nonlocal FONT, FONT_SMALL, FONT_TINY, FONT_BOLD, SCREEN
        pygame.init()
        FONT       = pygame.font.SysFont("segoeui", 15)
        FONT_SMALL = pygame.font.SysFont("segoeui", 13)
        FONT_TINY  = pygame.font.SysFont("segoeui", 11)
        FONT_BOLD  = pygame.font.SysFont("segoeui", 14, bold=True)
        SCREEN = pygame.display.set_mode((480, 540))
        pygame.display.set_caption("ConsoleDeck v1")

    def get_config_path(settings):
        return os.path.join(settings["config_dir"], "config.json")

    def load_config(settings):
        path = get_config_path(settings)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        config = {f"BUTTON_{i}": {"type": "none", "value": ""} for i in range(1, 10)}
        return config

    def save_config(config, settings):
        with open(get_config_path(settings), "w") as f:
            json.dump(config, f, indent=2)

    def esegui_azione(azione):
        t   = azione.get("type", "none")
        v   = azione.get("value", "")
        key = azione.get("_key", "default")
        if t == "link" and v:
            webbrowser.open(v)
        elif t == "exe" and v:
            try:
                subprocess.Popen(f'"{v}"', shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print("Ошибка запуска:", e)
        elif t == "hotkey" and v:
            try: press_hotkey(v)
            except Exception as e: print("Ошибка хоткея:", e)
        elif t == "desktop_switch":
            state = _desktop_toggle_state.get(key, 0)
            switch_desktop("right" if state == 0 else "left")
            _desktop_toggle_state[key] = 1 - state

    def config_pulsante(button_key, config):
        root = tk.Tk()
        apply_ru_shortcuts(root)
        root.title(f"Настройка {button_key}")
        root.resizable(False, False)
        scelta_var = tk.StringVar(root, value=config[button_key]["type"])
        valore_var = tk.StringVar(root, value=config[button_key].get("value", ""))
        frame_value = tk.Frame(root)
        frame_value.pack(pady=4)

        def rebuild(tipo=None):
            if tipo is None: tipo = scelta_var.get()
            for w in frame_value.winfo_children(): w.destroy()
            if tipo == "link":
                tk.Label(frame_value, text="URL:").pack()
                tk.Entry(frame_value, width=50, textvariable=valore_var).pack()
                tk.Button(frame_value, text="Тест", command=lambda: webbrowser.open(valore_var.get())).pack(pady=2)
                tk.Button(frame_value, text="Сохранить", command=salva).pack(pady=2)
            elif tipo == "exe":
                def pick():
                    p = filedialog.askopenfilename(title="Выбери .exe")
                    if p: valore_var.set(p)
                tk.Button(frame_value, text="Выбрать .exe", command=pick).pack()
                tk.Label(frame_value, textvariable=valore_var, wraplength=380).pack()
                tk.Button(frame_value, text="Тест",
                          command=lambda: esegui_azione({"type":"exe","value":valore_var.get(),"_key":button_key})).pack(pady=2)
                tk.Button(frame_value, text="Сохранить", command=salva).pack(pady=2)
            elif tipo == "hotkey":
                tk.Label(frame_value, text="Сочетание клавиш:").pack()
                tk.Entry(frame_value, width=40, textvariable=valore_var).pack()
                
                # ── НАДЕЖНЫЙ МЕХАНИЗМ ЗАПИСИ (СТАРТ / СТОП) ──
                rec_btn = tk.Button(frame_value, text="🔴 Записать нажатие", bg="#eedddd")
                rec_btn.pack(pady=2)
                
                recording = [False]
                recorded_combo = set()
                
                KEY_MAP = {
                    "control_l": "ctrl", "control_r": "ctrl",
                    "alt_l": "alt", "alt_r": "alt",
                    "shift_l": "shift", "shift_r": "shift",
                    "win_l": "win", "win_r": "win", "super_l": "win", "super_r": "win",
                    "return": "enter", "escape": "esc", "prior": "pageup", "next": "pagedown",
                    "delete": "del", "insert": "ins", "menu": "apps", "space": "space"
                }

                def toggle_capture():
                    if not recording[0]:
                        # Включаем запись
                        recording[0] = True
                        recorded_combo.clear()
                        valore_var.set("")
                        rec_btn.config(text="⏹ Остановить (кликните мышкой)", bg="#ddeedd")
                        root.bind("<KeyPress>", on_press)
                    else:
                        # Выключаем запись вручную
                        recording[0] = False
                        root.unbind("<KeyPress>")
                        rec_btn.config(text="🔴 Перезаписать", bg="#eedddd")
                
                def on_press(event):
                    if not recording[0]: return
                    raw_key = event.keysym.lower()
                    key = KEY_MAP.get(raw_key, raw_key)
                    
                    if key not in recorded_combo:
                        recorded_combo.add(key)
                        
                    mods_order = ["ctrl", "shift", "alt", "win"]
                    ordered = [m for m in mods_order if m in recorded_combo] + \
                              [k for k in recorded_combo if k not in mods_order]
                    
                    valore_var.set("+".join(ordered))

                rec_btn.config(command=toggle_capture)
                tk.Button(frame_value, text="Тест", command=lambda: press_hotkey(valore_var.get())).pack(pady=2)
                tk.Button(frame_value, text="Сохранить", command=salva).pack(pady=2)
            elif tipo == "desktop_switch":
                tk.Label(frame_value, text="Переключает между рабочим столом 1 ↔ 2").pack(pady=6)
                tk.Button(frame_value, text="Сохранить", command=salva).pack(pady=2)
            else:
                tk.Label(frame_value, text="Нет действия").pack()
                tk.Button(frame_value, text="Сохранить", command=salva).pack(pady=2)

        def salva():
            config[button_key] = {"type": scelta_var.get(), "value": valore_var.get()}
            if scelta_var.get() in ("none", "desktop_switch"):
                config[button_key]["value"] = ""
            root.destroy()

        tk.Label(root, text="Тип действия:").pack()
        tk.OptionMenu(root, scelta_var, "link", "exe", "hotkey", "desktop_switch", "none",
                      command=rebuild).pack()
        rebuild()
        root.mainloop()

    BTN_W, BTN_H = 130, 130
    BTN_PAD_X, BTN_PAD_Y, GRID_GAP = 15, 50, 10

    def btn_rect(i):
        return pygame.Rect(
            BTN_PAD_X + (i % 3) * (BTN_W + GRID_GAP),
            BTN_PAD_Y + (i // 3) * (BTN_H + GRID_GAP),
            BTN_W, BTN_H
        )

    def wrap_text(text, font, max_width):
        words, lines, current = text.split(), [], ""
        for word in words:
            test = (current + " " + word).strip()
            if font.size(test)[0] <= max_width: current = test
            else:
                if current: lines.append(current)
                current = word
        if current: lines.append(current)
        return lines

    def carica_icone(config):
        icons = {}
        for key in config:
            path = f"icons/{key}.png"
            if os.path.exists(path):
                img = pygame.image.load(path)
                icons[key] = pygame.transform.scale(img, (50, 50))
            else:
                icons[key] = None
        return icons

    def nome_file(p):
        return os.path.basename(p) if p else ""

    def disegna_pulsanti(config, icons, hover_idx):
        SCREEN.fill(BG)
        title = FONT_BOLD.render("ConsoleDeck", True, TEXT_WHITE)
        SCREEN.blit(title, (BTN_PAD_X, 10))
        SCREEN.blit(FONT_TINY.render("v1", True, TEXT_DIM), (BTN_PAD_X + title.get_width() + 6, 14))

        for i in range(9):
            key  = f"BUTTON_{i+1}"
            act  = config[key]
            t, v = act.get("type","none"), act.get("value","")
            rect = btn_rect(i)

            sh = pygame.Surface((BTN_W, BTN_H), pygame.SRCALPHA)
            pygame.draw.rect(sh, (0,0,0,60), (0,0,BTN_W,BTN_H), border_radius=14)
            SCREEN.blit(sh, rect.move(0,3))

            pygame.draw.rect(SCREEN, TYPE_COLORS.get(t, BTN_NONE), rect, border_radius=14)

            if hover_idx == i:
                hs = pygame.Surface((BTN_W,BTN_H), pygame.SRCALPHA)
                pygame.draw.rect(hs, (255,255,255,25), (0,0,BTN_W,BTN_H), border_radius=14)
                SCREEN.blit(hs, rect.topleft)

            bs = pygame.Surface((BTN_W,BTN_H), pygame.SRCALPHA)
            pygame.draw.rect(bs, (255,255,255,40 if hover_idx==i else 15),
                             (0,0,BTN_W,BTN_H), border_radius=14, width=1)
            SCREEN.blit(bs, rect.topleft)

            SCREEN.blit(FONT_SMALL.render(TYPE_ICONS.get(t,"+"), True, TEXT_WHITE), (rect.x+8, rect.y+7))
            ns = FONT_TINY.render(str(i+1), True, TEXT_DIM)
            SCREEN.blit(ns, (rect.right - ns.get_width() - 8, rect.y+8))

            if t == "none":
                plus = pygame.font.SysFont("segoeui", 36).render("+", True, (80,80,100))
                SCREEN.blit(plus, (rect.centerx - plus.get_width()//2,
                                    rect.centery - plus.get_height()//2))
            else:
                if icons.get(key):
                    SCREEN.blit(icons[key], (rect.centerx-25, rect.y+28))
                tl = FONT_BOLD.render(t.upper().replace("_"," "), True, TEXT_WHITE)
                SCREEN.blit(tl, (rect.x+(BTN_W-tl.get_width())//2, rect.y+32))
                dv = nome_file(v) if t=="exe" else \
                     v.replace("https://","").replace("http://","") if t=="link" else v
                for li, line in enumerate(wrap_text(dv, FONT_TINY, BTN_W-14)[:3]):
                    ls = FONT_TINY.render(line, True, (220,220,220))
                    SCREEN.blit(ls, (rect.x+(BTN_W-ls.get_width())//2, rect.y+52+li*15))

            es = FONT_TINY.render("изменить", True, TEXT_GREEN)
            SCREEN.blit(es, (rect.x+(BTN_W-es.get_width())//2, rect.bottom-18))

        pygame.display.flip()

    def find_hover(mx, my):
        for i in range(9):
            if btn_rect(i).collidepoint(mx, my): return i
        return -1

    def ascolta_seriale(settings, port):
        config = load_config(settings)
        config_path = get_config_path(settings)
        last_mtime = os.path.getmtime(config_path) if os.path.exists(config_path) else 0

        while True:
            try:
                with serial.Serial(port, BAUDRATE, timeout=1) as ser:
                    print(f"Подключено к {port}")
                    while True:
                        if os.path.exists(config_path):
                            current_mtime = os.path.getmtime(config_path)
                            if current_mtime > last_mtime:
                                config = load_config(settings)
                                last_mtime = current_mtime

                        linea = ser.readline().decode('utf-8').strip()
                        if linea and linea in config:
                            a = dict(config[linea]); a["_key"] = linea
                            esegui_azione(a)
            except Exception as e:
                print(f"Ошибка порта: {e}")
                time.sleep(5)

    # ── Main ──
    create_tray_icon()
    settings = get_or_create_settings()
    config   = load_config(settings)
    port     = settings.get("port", "COM5")

    parser = argparse.ArgumentParser()
    parser.add_argument('--gui', action='store_true')
    args = parser.parse_args()

    if args.gui:
        init_pygame()
        icons   = carica_icone(config)
        clock   = pygame.time.Clock()
        running = True
        while running:
            hover = find_hover(*pygame.mouse.get_pos())
            disegna_pulsanti(config, icons, hover)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    idx = find_hover(*pygame.mouse.get_pos())
                    if idx >= 0:
                        key = f"BUTTON_{idx+1}"
                        config_pulsante(key, config)
                        icons = carica_icone(config)
                        save_config(config, settings)
            clock.tick(60)
        pygame.quit()
    else:
        ascolta_seriale(settings, port)


# ─── Точка входа ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import subprocess
    import os

    ok = show_library_check_window()
    if ok:
        run_app()
    else:
        run_app()