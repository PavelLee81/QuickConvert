import flet as ft
import requests
import urllib3

# Отключаем ошибки
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main(page: ft.Page):
    # --- 1. ШРИФТЫ ---
    page.fonts = {
        "Audiowide": "https://github.com/google/fonts/raw/main/ofl/audiowide/Audiowide-Regular.ttf",
        "RussoOne": "https://github.com/google/fonts/raw/main/ofl/russoone/RussoOne-Regular.ttf"
    }

    # --- 2. НАСТРОЙКИ ---
    page.title = "QuickConvert FullScreen Fix"
    page.theme_mode = ft.ThemeMode.DARK 
    page.padding = 0 
    # Это для ПК, на телефоне оно само подстроится
    page.window.width = 400 
    page.window.height = 850
    
    page.theme = ft.Theme(font_family="RussoOne")

    # --- 3. ДАННЫЕ ---
    rates_db = {"UZS": 1.0}
    SELL_MARGINS = {"USD": 1.005, "EUR": 1.01, "RUB": 1.04, "GBP": 1.01, "default": 1.01}
    
    CUSTOM_NAMES = {
        "UZS": "Узбекский сум", "USD": "Доллар США", "EUR": "Евро",
        "RUB": "Российский рубль", "CNY": "Китайский юань", "KZT": "Тенге",
        "GBP": "Фунт стерлингов", "JPY": "Иена", "TRY": "Лира",
        "KRW": "Вона", "AED": "Дирхам", "CHF": "Франк"
    }
    full_names_db = CUSTOM_NAMES.copy()
    rows_data = [] 
    current_active_row = None 
    status_indicator = ft.Container(width=8, height=8, border_radius=4, bgcolor="#4CAF50")

    # --- 4. КАРТИНКИ ---
    def get_flag_url(currency_code):
        if currency_code == "EUR": return "https://cdn-icons-png.flaticon.com/512/197/197615.png"
        if currency_code == "XDR": return "https://cdn-icons-png.flaticon.com/512/921/921490.png"
        mapping = {"USD": "us", "RUB": "ru", "UZS": "uz", "KZT": "kz", "GBP": "gb", "JPY": "jp", "CNY": "cn", "TRY": "tr", "AED": "ae", "KRW": "kr", "CHF": "ch", "CAD": "ca", "AUD": "au", "INR": "in", "UAH": "ua", "GEL": "ge"}
        code = mapping.get(currency_code, currency_code[:2].lower())
        return f"https://flagcdn.com/w80/{code}.png"

    # --- 5. ЛОГИКА ---
    def fetch_data():
        try:
            status_indicator.bgcolor = "orange"
            page.update()
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
                if code not in CUSTOM_NAMES:
                    full_names_db[code] = item['CcyNm_RU']
            status_indicator.bgcolor = "#00C853"
            page.update()
        except:
            status_indicator.bgcolor = "red"
            page.update()

    def recalc(e):
        sender_field = e.control
        if not sender_field: return
        raw_val = sender_field.value.replace(" ", "")
        
        if not raw_val:
            for row in rows_data:
                if row['txt'] != sender_field: row['txt'].value = ""
            page.update()
            return

        try:
            amount = float(raw_val)
        except:
            return

        if "." not in raw_val:
            formatted_input = f"{int(amount):,}".replace(",", " ")
            if sender_field.value != formatted_input: sender_field.value = formatted_input

        sender_code = "UZS"
        for row in rows_data:
            if row['txt'] == sender_field:
                sender_code = row['code_txt'].value
                break
        
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
            if old_code == new_code:
                page.close(dialog)
                return
            
            duplicate_row = None
            for row in rows_data:
                if row['code_txt'].value == new_code:
                    duplicate_row = row
                    break
            
            if duplicate_row:
                duplicate_row['code_txt'].value = old_code
                duplicate_row['img'].src = get_flag_url(old_code)
                duplicate_row['code_txt'].update()
                duplicate_row['img'].update()
            
            current_active_row['code_txt'].value = new_code
            current_active_row['img'].src = get_flag_url(new_code)
            current_active_row['code_txt'].update()
            current_active_row['img'].update()
            
            page.close(dialog)
            txt_field = current_active_row['txt']
            recalc(ft.ControlEvent(target="", name="change", data="", control=txt_field, page=page))

    # --- 6. ДИАЛОГ (ИСПРАВЛЕНО: ФОН И РАЗМЕР) ---
    
    search_field = ft.TextField(
        hint_text="Поиск...", autofocus=True, prefix_icon=ft.Icons.SEARCH, 
        bgcolor="white", border_radius=12, border_color="#DDDDDD", 
        color="black", hint_style=ft.TextStyle(color="grey"),
        content_padding=15, text_size=18
    )
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
                        ft.Column([
                            ft.Text(code, weight="bold", size=18, color="black"), 
                            ft.Text(name, size=14, color="#666666") 
                        ], spacing=2),
                    ]),
                    padding=15, border_radius=10,
                    on_click=select_currency, data=code, ink=True,
                    border=ft.border.only(bottom=ft.border.BorderSide(1, "#EEEEEE"))
                )
                currency_list_view.controls.append(tile)
        page.update()

    def close_dialog(e):
        page.close(dialog)

    # Контейнер содержимого (Вынесен, чтобы менять высоту)
    dialog_content = ft.Container(
        # Важно: задаем фон контейнеру
        bgcolor="#F5F5F5", 
        content=ft.Column([
            # Шапка окна
            ft.Container(
                content=ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, icon_color="black", on_click=close_dialog, icon_size=24),
                    ft.Text("Выберите валюту", size=20, weight="bold", color="black"),
                    ft.Container(width=48)
                ], alignment="spaceBetween"),
                padding=ft.padding.only(top=10, left=5, right=5, bottom=10),
                bgcolor="white",
                shadow=ft.BoxShadow(blur_radius=5, color="#20000000")
            ),
            # Поиск и список
            ft.Container(
                content=ft.Column([
                    search_field,
                    ft.Container(height=10),
                    ft.Container(currency_list_view, expand=True)
                ]),
                padding=20,
                expand=True
            )
        ], spacing=0)
    )

    dialog = ft.AlertDialog(
        modal=True,
        # Убираем все отступы, чтобы прилипало к краям
        inset_padding=ft.padding.all(0),
        content_padding=ft.padding.all(0),
        shape=ft.RoundedRectangleBorder(radius=0),
        
        # ВАЖНО: Задаем фон самому окну диалога, чтобы перекрыть черный фон страницы
        bgcolor="#F5F5F5", 
        
        content=dialog_content
    )

    def open_currency_picker(e):
        nonlocal current_active_row
        clicked_btn = e.control
        for row in rows_data:
            if row['btn'] == clicked_btn:
                current_active_row = row
                break
        
        search_field.value = ""
        search_field.on_change = filter_currencies
        filter_currencies(None)
        
        # --- ФИКС ВЫСОТЫ ---
        # Растягиваем контейнер на всю высоту текущего экрана
        if page.height:
            dialog_content.height = page.height
            dialog_content.width = page.width
        else:
            # Резерв на случай, если высота не определилась сразу (для телефонов)
            dialog_content.height = 850
            dialog_content.width = 400
            
        page.open(dialog)

    # --- 7. СБОРКА СЛОТОВ ---
    fetch_data()
    slots_column = ft.Column(spacing=20)

    def add_slot(default_curr):
        img = ft.Image(src=get_flag_url(default_curr), width=24, height=24, border_radius=12, fit=ft.ImageFit.COVER)
        code_txt = ft.Text(default_curr, size=16, weight="bold", color="black")
        
        btn = ft.Container(
            content=ft.Row([img, code_txt], alignment="center", spacing=8),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=12,
            bgcolor="white",
            on_click=open_currency_picker, 
            ink=True,
            width=100
        )

        separator = ft.Container(width=1, height=30, bgcolor="#444444", margin=ft.margin.symmetric(horizontal=5))

        txt = ft.TextField(
            hint_text="0", expand=True, text_align=ft.TextAlign.RIGHT,
            keyboard_type=ft.KeyboardType.NUMBER, 
            text_size=28, 
            text_style=ft.TextStyle(
                color="white",
                font_family="Audiowide" # Шрифт цифр
            ),
            border_color="transparent", bgcolor="transparent",
            content_padding=ft.padding.only(left=10, bottom=5),
            on_change=recalc, cursor_color="#4CAF50"
        )

        card = ft.Container(
            content=ft.Row([btn, separator, txt], alignment="start", vertical_alignment="center"),
            bgcolor="#1C1C1E",
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            shadow=ft.BoxShadow(blur_radius=10, color="#80000000", offset=ft.Offset(0, 5))
        )
        rows_data.append({"btn": btn, "code_txt": code_txt, "img": img, "txt": txt})
        slots_column.controls.append(card)

    defaults = ["USD", "UZS", "EUR", "RUB", "KZT", "CNY"]
    for c in defaults:
        add_slot(c)

    # --- 8. ГРАДИЕНТ ---
    gradient_container = ft.Container(
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
            # Темно-зеленый -> Изумрудный
            colors=["#093028", "#237A57"] 
        ),
        expand=True,
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("QuickConvert", size=24, weight="bold", color="white"),
                    ft.Container(
                        content=ft.Row([status_indicator, ft.Text("Live", color="#4CAF50", weight="bold")], spacing=6),
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        bgcolor="#33000000", border_radius=12
                    )
                ], alignment="spaceBetween"),
                padding=ft.padding.only(left=20, right=20, top=40, bottom=20)
            ),
            ft.Container(content=slots_column, padding=ft.padding.symmetric(horizontal=20), expand=True)
        ])
    )

    page.add(gradient_container)

print("Запуск Final Fix Background...")
ft.app(target=main)
