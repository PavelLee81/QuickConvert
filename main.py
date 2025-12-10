import flet as ft
import requests
import urllib3

# Отключаем ошибки
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main(page: ft.Page):
    # --- НАСТРОЙКИ ИКОНКИ (ДЛЯ КОРНЕВОЙ ПАПКИ) ---
    # Точка означает "текущая папка" (где лежит main.py)
    page.assets_dir = "assets" 
    page.window_icon = "icon.png"
    # ---------------------------------------------

    # --- 1. ШРИФТЫ ---
    page.fonts = {
        "Audiowide": "https://github.com/google/fonts/raw/main/ofl/audiowide/Audiowide-Regular.ttf",
        "RussoOne": "https://github.com/google/fonts/raw/main/ofl/russoone/RussoOne-Regular.ttf",
        "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
        "Lobster": "https://github.com/google/fonts/raw/main/ofl/lobster/Lobster-Regular.ttf",
        "Monospace": "monospace"
    }

    # --- 2. НАСТРОЙКИ СТРАНИЦЫ ---
    page.title = "QuickConvert App"
    page.theme_mode = ft.ThemeMode.DARK 
    page.padding = 0 
    page.window_width = 400 
    page.window_height = 850
    page.theme = ft.Theme(font_family="RussoOne")

    # --- 3. НАСТРОЙКИ (STATE) ---
    DEFAULT_STYLE = {
        "bg_colors": ["#093028", "#237A57"], 
        "card_color": "#1C1C1E",             
        "field_color": "transparent",        
        "text_font": "RussoOne",             
        "num_font": "Audiowide",             
        "curr_color": "white",               
        "num_color": "white"                 
    }
    
    style_state = DEFAULT_STYLE.copy()

    # --- 4. ВАРИАНТЫ ДЛЯ ВЫБОРА ---
    THEMES_BG = {
        "Forest": ["#093028", "#237A57"],
        "Lumina": ["#240b36", "#c31432"],
        "Ocean": ["#0f2027", "#2c5364"],
        "Cyber": ["#000000", "#434343"],
        "Sunny": ["#FF4E50", "#F9D423"],
        "Rose": ["#DA22FF", "#9733EE"],
        "Sky": ["#00c6ff", "#0072ff"]
    }

    CARD_COLORS = {
        "Dark": "#1C1C1E",
        "Black": "#000000",
        "White": "#FFFFFF",
        "Glass": "#20FFFFFF",
        "Light Grey": "#F5F5F5"
    }

    FIELD_COLORS = {
        "None": "transparent",
        "Dark": "#30000000",
        "Light": "#30FFFFFF"
    }

    TEXT_COLORS = {
        "White": "white", "Black": "black", "Gold": "#FFD700", 
        "Green": "#4CAF50", "Red": "#E53935", "Blue": "#2196F3"
    }

    # --- 5. ДАННЫЕ ВАЛЮТ ---
    rates_db = {"UZS": 1.0}
    SELL_MARGINS = {"USD": 1.005, "EUR": 1.01, "RUB": 1.04, "default": 1.01}
    
    # Полный список стран (ОТОБРАЖАЕТСЯ ТОЛЬКО В МЕНЮ ВЫБОРА)
    CUSTOM_NAMES = {
        "UZS": "Узбекистан / Сум", "USD": "США / Доллар", "EUR": "Евросоюз / Евро",
        "RUB": "Россия / Рубль", "CNY": "Китай / Юань", "KZT": "Казахстан / Тенге",
        "GBP": "Британия / Фунт", "JPY": "Япония / Йена", "TRY": "Турция / Лира",
        "KRW": "Корея / Вона", "AED": "ОАЭ / Дирхам", "CHF": "Швейцария / Франк",
        "CAD": "Канада / Доллар", "AUD": "Австралия / Доллар", "INR": "Индия / Рупия",
        "BYN": "Беларусь / Рубль", "UAH": "Украина / Гривна"
    }
    full_names_db = CUSTOM_NAMES.copy()
    rows_data = [] 
    current_active_row = None 

    # --- 6. ФУНКЦИИ ---
    def get_flag_url(currency_code):
        if currency_code == "EUR": return "https://cdn-icons-png.flaticon.com/512/197/197615.png"
        mapping = {"USD": "us", "RUB": "ru", "UZS": "uz", "KZT": "kz", "GBP": "gb", "JPY": "jp", "CNY": "cn", "TRY": "tr", "AED": "ae", "KRW": "kr", "CHF": "ch"}
        code = mapping.get(currency_code, currency_code[:2].lower())
        return f"https://flagcdn.com/w80/{code}.png"

    def fetch_data():
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get("https://cbu.uz/oz/arkhiv-kursov-valyut/json/", headers=headers, verify=False, timeout=5)
            data = response.json()
            rates_db.clear()
            rates_db["UZS"] = 1.0
            for item in data:
                code = item['Ccy']
                base_rate = float(item['Rate'])
                margin = SELL_MARGINS.get(code, SELL_MARGINS["default"])
                rates_db[code] = base_rate * margin
                if code not in CUSTOM_NAMES: full_names_db[code] = f"{item['CcyNm_RU']}"
            page.update()
        except: page.update()

    def recalc(e):
        sender_field = e.control
        if not sender_field: return
        raw_val = sender_field.value.replace(" ", "")
        if not raw_val:
            for row in rows_data:
                if row['txt'] != sender_field: row['txt'].value = ""
            page.update()
            return
        try: amount = float(raw_val)
        except: return
        if "." not in raw_val:
            formatted_input = f"{int(amount):,}".replace(",", " ")
            if sender_field.value != formatted_input: sender_field.value = formatted_input
        sender_code = "UZS"
        for row in rows_data:
            if row['txt'] == sender_field: sender_code = row['code_txt'].value; break
        base_rate = rates_db.get(sender_code, 1.0)
        amount_in_uzs = amount * base_rate
        for row in rows_data:
            target_field = row['txt']
            target_code = row['code_txt'].value
            if target_field != sender_field:
                target_rate = rates_db.get(target_code, 1.0)
                if target_rate > 0:
                    res = amount_in_uzs / target_rate
                    if res > 100: target_field.value = f"{res:,.0f}".replace(",", " ")
                    else: target_field.value = f"{res:,.2f}".replace(",", " ")
        page.update()

    def select_currency(e):
        new_code = e.control.data
        if current_active_row:
            old_code = current_active_row['code_txt'].value
            if old_code == new_code: page.close(dialog); return
            duplicate_row = None
            for row in rows_data:
                if row['code_txt'].value == new_code: duplicate_row = row; break
            
            # SWAP Logic (Только код и флаг, имя на главном не нужно)
            if duplicate_row:
                duplicate_row['code_txt'].value = old_code
                duplicate_row['img'].src = get_flag_url(old_code)
                duplicate_row['code_txt'].update()
                duplicate_row['img'].update()
            
            # Update Current Row
            current_active_row['code_txt'].value = new_code
            current_active_row['img'].src = get_flag_url(new_code)
            current_active_row['code_txt'].update()
            current_active_row['img'].update()
            
            page.close(dialog)
            txt_field = current_active_row['txt']
            recalc(ft.ControlEvent(target="", name="change", data="", control=txt_field, page=page))

    # --- 7. КОНТЕЙНЕР ФОНА ---
    gradient_container = ft.Container(
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left, 
            end=ft.alignment.bottom_right, 
            colors=style_state["bg_colors"]
        ),
        expand=True,
        content=None 
    )

    # --- 8. ЛОГИКА ОБНОВЛЕНИЯ СТИЛЯ ---
    def update_app_style():
        gradient_container.gradient.colors = style_state["bg_colors"]
        
        for row in rows_data:
            # Цвета блоков
            row['card_container'].bgcolor = style_state["card_color"]
            row['txt'].bgcolor = style_state["field_color"]
            
            # ТЕКСТ (Код валюты)
            row['code_txt'].font_family = style_state["text_font"]
            row['code_txt'].color = style_state["curr_color"]
            
            # ЦИФРЫ
            row['txt'].text_style.font_family = style_state["num_font"]
            row['txt'].text_style.color = style_state["num_color"]
            row['txt'].cursor_color = style_state["num_color"]
            
            # Обновляем
            row['card_container'].update()
            row['txt'].update()
            row['code_txt'].update()
            
        gradient_container.update()

    # --- 9. МЕНЮ НАСТРОЕК ---
    
    def set_bg(e): style_state["bg_colors"] = THEMES_BG[e.control.data]; update_app_style()
    def set_card(e): style_state["card_color"] = CARD_COLORS[e.control.data]; update_app_style()
    def set_field(e): style_state["field_color"] = FIELD_COLORS[e.control.data]; update_app_style()
    def set_curr_color(e): style_state["curr_color"] = TEXT_COLORS[e.control.data]; update_app_style()
    def set_num_color(e): style_state["num_color"] = TEXT_COLORS[e.control.data]; update_app_style()
    def set_text_font(e): style_state["text_font"] = e.control.data; update_app_style()
    def set_num_font(e): style_state["num_font"] = e.control.data; update_app_style()

    def reset_settings(e):
        style_state.update(DEFAULT_STYLE)
        update_app_style()
        page.close_bottom_sheet()

    def build_settings_ui():
        def color_preview_btn(name, color_val, func):
            if isinstance(color_val, list): bg, grad = None, ft.LinearGradient(colors=color_val)
            else: bg, grad = color_val, None
            return ft.Container(content=ft.Container(width=40, height=40, border_radius=20, gradient=grad, bgcolor=bg, border=ft.border.all(2, "white")), on_click=func, data=name, tooltip=name)

        def font_btn(font_name, func, is_num=False):
            txt = "123" if is_num else "Abc"
            return ft.Container(content=ft.Text(txt, font_family=font_name, size=14, color="black"), padding=8, bgcolor="#EEEEEE", border_radius=8, on_click=func, data=font_name)

        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("Настройки", size=22, weight="bold", color="black"), ft.ElevatedButton("СБРОС", bgcolor="#FFEBEE", color="red", on_click=reset_settings)], alignment="spaceBetween"),
                ft.Divider(),
                ft.Text("1. Фон приложения", color="grey", size=12),
                ft.Row([color_preview_btn(n, c, set_bg) for n, c in THEMES_BG.items()], scroll="auto"),
                ft.Text("2. Цвет карточек", color="grey", size=12),
                ft.Row([color_preview_btn(n, c, set_card) for n, c in CARD_COLORS.items()], scroll="auto"),
                ft.Text("3. Цвет Текста (Валюта)", color="grey", size=12),
                ft.Row([color_preview_btn(n, c, set_curr_color) for n, c in TEXT_COLORS.items()], scroll="auto"),
                ft.Text("4. Цвет Цифр", color="grey", size=12),
                ft.Row([color_preview_btn(n, c, set_num_color) for n, c in TEXT_COLORS.items()], scroll="auto"),
                ft.Text("5. Поле ввода", color="grey", size=12),
                ft.Row([color_preview_btn(n, c, set_field) for n, c in FIELD_COLORS.items()], scroll="auto"),
                ft.Divider(),
                ft.Text("6. Шрифт Текста", color="grey", size=12),
                ft.Row([font_btn(f, set_text_font) for f in ["RussoOne", "Roboto", "Lobster"]], wrap=True),
                ft.Text("7. Шрифт Цифр", color="grey", size=12),
                ft.Row([font_btn(f, set_num_font, True) for f in ["Audiowide", "RussoOne", "Monospace"]], wrap=True),
                ft.Container(height=20)
            ], tight=True, scroll="auto"), padding=20, bgcolor="white", border_radius=ft.border_radius.only(top_left=20, top_right=20), height=600
        )

    settings_sheet = ft.BottomSheet(build_settings_ui())
    def open_settings(e): page.overlay.append(settings_sheet); settings_sheet.open = True; page.update()

    # --- 10. ДИАЛОГ ---
    search_field = ft.TextField(hint_text="Поиск...", autofocus=True, prefix_icon=ft.Icons.SEARCH, bgcolor="white", border_radius=12, color="black", content_padding=15)
    currency_list_view = ft.ListView(expand=1, spacing=5, padding=0)

    def filter_currencies(e):
        query = search_field.value.lower()
        currency_list_view.controls.clear()
        all_codes = list(rates_db.keys())
        priority = ["UZS", "USD", "EUR", "RUB", "CNY", "KZT"]
        all_codes.sort(key=lambda x: priority.index(x) if x in priority else 999)
        for code in all_codes:
            name = full_names_db.get(code, code)
            if query in code.lower() or query in name.lower():
                tile = ft.Container(
                    content=ft.Row([
                        ft.Image(src=get_flag_url(code), width=35, height=35, border_radius=17, fit=ft.ImageFit.COVER),
                        ft.Column([ft.Text(code, weight="bold", size=18, color="black"), ft.Text(name, size=14, color="#666666")], spacing=2),
                    ]),
                    padding=15, border_radius=10, on_click=select_currency, data=code, ink=True, border=ft.border.only(bottom=ft.border.BorderSide(1, "#EEEEEE"))
                )
                currency_list_view.controls.append(tile)
        page.update()

    def close_dialog(e): page.close(dialog)

    dialog_content = ft.Container(bgcolor="#F5F5F5", content=ft.Column([
        ft.Container(content=ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, icon_color="black", on_click=close_dialog), ft.Text("Выберите валюту", size=20, weight="bold", color="black"), ft.Container(width=48)], alignment="spaceBetween"), padding=10, bgcolor="white", shadow=ft.BoxShadow(blur_radius=5, color="#20000000")),
        ft.Container(content=ft.Column([search_field, ft.Container(height=10), ft.Container(currency_list_view, expand=True)]), padding=20, expand=True)
    ], spacing=0))

    dialog = ft.AlertDialog(modal=True, inset_padding=0, content_padding=0, shape=ft.RoundedRectangleBorder(radius=0), bgcolor="#F5F5F5", content=dialog_content)

    def open_currency_picker(e):
        nonlocal current_active_row
        clicked_btn = e.control
        for row in rows_data:
            if row['btn'] == clicked_btn: current_active_row = row; break
        search_field.value = ""; search_field.on_change = filter_currencies; filter_currencies(None)
        if page.height: dialog_content.height = page.height; dialog_content.width = page.width
        else: dialog_content.height = 850; dialog_content.width = 400
        page.open(dialog)

    # --- 11. СБОРКА СЛОТОВ ---
    fetch_data()
    slots_column = ft.Column(spacing=20)

    def add_slot(default_curr):
        img = ft.Image(src=get_flag_url(default_curr), width=24, height=24, border_radius=12, fit=ft.ImageFit.COVER)
        
        # ТЕКСТ ВАЛЮТЫ (Только код, без названия страны)
        code_txt = ft.Text(default_curr, size=16, weight="bold", 
                           color=style_state["curr_color"], 
                           font_family=style_state["text_font"])
        
        btn = ft.Container(
            content=ft.Row([img, code_txt], alignment="center", spacing=10),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=12, bgcolor="transparent",
            on_click=open_currency_picker, ink=True, width=100
        )
        separator = ft.Container(width=1, height=30, bgcolor="#444444", margin=ft.margin.symmetric(horizontal=5))
        
        txt = ft.TextField(
            hint_text="0", expand=True, text_align=ft.TextAlign.RIGHT,
            keyboard_type=ft.KeyboardType.NUMBER, text_size=28,
            text_style=ft.TextStyle(color=style_state["num_color"], font_family=style_state["num_font"]),
            border_color="transparent", bgcolor=style_state["field_color"],
            content_padding=ft.padding.only(left=10, bottom=5),
            on_change=recalc, cursor_color=style_state["num_color"]
        )

        card = ft.Container(
            content=ft.Row([btn, separator, txt], alignment="start", vertical_alignment="center"),
            bgcolor=style_state["card_color"],
            border_radius=20, padding=ft.padding.symmetric(horizontal=15, vertical=10),
            shadow=ft.BoxShadow(blur_radius=10, color="#80000000", offset=ft.Offset(0, 5))
        )
        rows_data.append({"btn": btn, "code_txt": code_txt, "img": img, "txt": txt, "card_container": card})
        slots_column.controls.append(card)

    defaults = ["USD", "UZS", "EUR", "RUB", "KZT", "CNY"]
    for c in defaults: add_slot(c)

    # --- 12. ОСНОВНОЙ ЭКРАН ---
    gradient_container.content = ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text("QuickConvert", size=24, weight="bold", color="white", font_family="RussoOne"),
                ft.IconButton(ft.Icons.SETTINGS, icon_color="white", on_click=open_settings)
            ], alignment="spaceBetween"),
            padding=ft.padding.only(left=20, right=10, top=40, bottom=20)
        ),
        ft.Container(content=slots_column, padding=ft.padding.symmetric(horizontal=20), expand=True)
    ])
    page.add(gradient_container)

ft.app(target=main)
