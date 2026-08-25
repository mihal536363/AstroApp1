from kivy.uix.spinner import Spinner
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.slider import MDSlider
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle, Ellipse
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.modalview import ModalView
from kivy.uix.scatterlayout import ScatterLayout
# НОВІ ІМПОРТИ ДЛЯ ФАЙЛОВОГО МЕНЕДЖЕРА
from kivymd.uix.list import MDList, TwoLineIconListItem, IconLeftWidget

# =========================================================
# КАСТОМНИЙ ВІДЖЕТ: ЗОРЯНА КАРТА (Атлас)
# =========================================================
class StarMapCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.02, 0.02, 0.08, 1) 
            Rectangle(pos=self.pos, size=self.size)
            Color(1, 1, 1, 0.8)
            Ellipse(pos=(self.x + 50, self.y + 100), size=(3, 3))
            Ellipse(pos=(self.x + 200, self.y + 300), size=(4, 4))
            Ellipse(pos=(self.x + 300, self.y + 150), size=(2, 2))
            Color(0.8, 0.1, 0.1, 1)
            cx, cy = self.center_x, self.center_y
            size = 40
            Line(points=[cx - size, cy, cx + size, cy], width=1.2)
            Line(points=[cx, cy - size, cx, cy + size], width=1.2)
            Line(circle=(cx, cy, size/2), width=1.2)

class ClickablePreview(ButtonBehavior, MDBoxLayout):
    pass

class AstroApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.stacked_frames = 0 

        screen = MDScreen()
        bottom_nav = MDBottomNavigation()

        # =========================================================
        # ВКЛАДКА 1: ПРОФІЛЬ
        # =========================================================
        tab_profile = MDBottomNavigationItem(name='tab_profile', text='Профіль', icon='telescope')
        scroll_prof = MDScrollView()
        layout_profile = MDBoxLayout(orientation='vertical', padding="20dp", spacing="20dp", size_hint_y=None)
        layout_profile.bind(minimum_height=layout_profile.setter('height'))
        
        self.status_label = MDLabel(text="🔴 Профіль зупинено", halign="center", font_style="H5", size_hint_y=None, height="40dp")
        layout_profile.add_widget(self.status_label)
        self.ip_input = MDTextField(text="10.42.0.1", hint_text="IP-адреса Astroberry", size_hint_y=None, height="40dp")
        layout_profile.add_widget(self.ip_input)
        
        btn_sync = MDRaisedButton(text="🔄 ЗАВАНТАЖИТИ БАЗУ", pos_hint={"center_x": 0.5}, md_bg_color=(0.1, 0.5, 0.8, 1), on_release=self.sync_equipment)
        layout_profile.add_widget(btn_sync)
        
        self.spinner_mount = Spinner(text='Порожньо', values=('Порожньо',), size_hint_y=None, height="48dp", background_color=(0.4, 0.1, 0.6, 1))
        layout_profile.add_widget(self.spinner_mount)
        self.spinner_camera = Spinner(text='Порожньо', values=('Порожньо',), size_hint_y=None, height="48dp", background_color=(0.4, 0.1, 0.6, 1))
        layout_profile.add_widget(self.spinner_camera)
        
        btn_start_profile = MDRaisedButton(text="ЗАПУСТИТИ EKOS ПРОФІЛЬ", pos_hint={"center_x": 0.5}, on_release=self.start_ekos_profile)
        layout_profile.add_widget(MDLabel(size_hint_y=None, height="20dp"))
        layout_profile.add_widget(btn_start_profile)
        
        scroll_prof.add_widget(layout_profile)
        tab_profile.add_widget(scroll_prof)
        bottom_nav.add_widget(tab_profile)

        # =========================================================
        # ВКЛАДКА 2: АТЛАС НЕБА
        # =========================================================
        tab_atlas = MDBottomNavigationItem(name='tab_atlas', text='Атлас', icon='star-circle-outline')
        layout_atlas = MDBoxLayout(orientation='vertical')
        self.coord_box = MDBoxLayout(size_hint_y=0.1, md_bg_color=(0.1, 0.1, 0.1, 1))
        self.coord_label = MDLabel(text="RA: 12h 30m 00s  |  DEC: +45° 00' 00\"", halign="center", theme_text_color="Custom", text_color=(0.8, 0.8, 1, 1))
        self.coord_box.add_widget(self.coord_label)
        layout_atlas.add_widget(self.coord_box)
        self.star_map = StarMapCanvas(size_hint_y=0.75)
        layout_atlas.add_widget(self.star_map)
        panel_mount_controls = MDBoxLayout(orientation='horizontal', size_hint_y=0.15, padding="10dp", spacing="10dp")
        panel_mount_controls.add_widget(MDRaisedButton(text="GOTO (Навестися)", size_hint_x=0.5, md_bg_color=(0.1, 0.6, 0.1, 1)))
        panel_mount_controls.add_widget(MDRaisedButton(text="SYNC (Синхр.)", size_hint_x=0.5, md_bg_color=(0.7, 0.5, 0.1, 1)))
        layout_atlas.add_widget(panel_mount_controls)
        tab_atlas.add_widget(layout_atlas)
        bottom_nav.add_widget(tab_atlas)

        # =========================================================
        # ВКЛАДКА 3: КАМЕРА
        # =========================================================
        tab_capture = MDBottomNavigationItem(name='tab_capture', text='Камера', icon='camera-iris')
        scroll_cap = MDScrollView()
        layout_capture = MDBoxLayout(orientation='vertical', padding="20dp", spacing="15dp", size_hint_y=None)
        layout_capture.bind(minimum_height=layout_capture.setter('height'))

        self.preview_box = MDBoxLayout(size_hint_y=None, height="200dp", md_bg_color=(0.15, 0.15, 0.15, 1))
        self.preview_label = MDLabel(text="[ Прев'ю кадру ]", halign="center")
        self.preview_box.add_widget(self.preview_label)
        layout_capture.add_widget(self.preview_box)

        self.exp_input = MDTextField(text="10", hint_text="Витримка (сек/мс)", size_hint_y=None, height="40dp")
        layout_capture.add_widget(self.exp_input)
        self.count_input = MDTextField(text="100", hint_text="Кількість кадрів", size_hint_y=None, height="40dp")
        layout_capture.add_widget(self.count_input)
        self.gain_slider = MDSlider(min=0, max=300, value=120, hint=True)
        layout_capture.add_widget(self.gain_slider)
        
        buttons_single = MDBoxLayout(orientation='horizontal', size_hint_y=None, height="50dp", spacing="10dp")
        buttons_single.add_widget(MDRaisedButton(text="📷 1 КАДР", size_hint_x=0.5, md_bg_color=(0.3, 0.3, 0.3, 1), on_release=self.take_photo))
        buttons_single.add_widget(MDRaisedButton(text="🎥 ВІДЕО", size_hint_x=0.5, md_bg_color=(0.2, 0.5, 0.8, 1), on_release=self.record_video))
        layout_capture.add_widget(buttons_single)

        buttons_sequence = MDBoxLayout(orientation='horizontal', size_hint_y=None, height="50dp", spacing="10dp")
        buttons_sequence.add_widget(MDRaisedButton(text="▶ СТАРТ СЕРІЇ", size_hint_x=0.5, md_bg_color=(0.1, 0.6, 0.1, 1), on_release=self.start_sequence))
        buttons_sequence.add_widget(MDRaisedButton(text="⏹ СТОП", size_hint_x=0.5, md_bg_color=(0.8, 0.1, 0.1, 1), on_release=self.stop_sequence))
        layout_capture.add_widget(buttons_sequence)

        scroll_cap.add_widget(layout_capture)
        tab_capture.add_widget(scroll_cap)
        bottom_nav.add_widget(tab_capture)

        # =========================================================
        # ВКЛАДКА 4: ЖИВИЙ СТЕК 
        # =========================================================
        tab_stack = MDBottomNavigationItem(name='tab_stack', text='Стек', icon='layers')
        scroll_stack = MDScrollView()
        layout_stack = MDBoxLayout(orientation='vertical', padding="20dp", spacing="15dp", size_hint_y=None)
        layout_stack.bind(minimum_height=layout_stack.setter('height'))

        self.stack_preview_box = ClickablePreview(size_hint_y=None, height="300dp", md_bg_color=(0.05, 0.05, 0.1, 1))
        self.stack_preview_box.bind(on_release=self.open_fullscreen)
        self.stack_preview_label = MDLabel(text="[ Зображення Live Stack ]\n(Тапніть для розгортання)", halign="center", theme_text_color="Custom", text_color=(0.7, 0.7, 0.8, 1))
        self.stack_preview_box.add_widget(self.stack_preview_label)
        layout_stack.add_widget(self.stack_preview_box)

        self.stack_info = MDLabel(text="Кадрів у стеку: 0 | Загальна витримка: 0с", halign="center", size_hint_y=None, height="30dp", theme_text_color="Custom", text_color=(1, 0.8, 0, 1))
        layout_stack.add_widget(self.stack_info)

        stack_btns = MDBoxLayout(orientation='horizontal', size_hint_y=None, height="40dp", spacing="10dp")
        stack_btns.add_widget(MDRaisedButton(text="▶ СТАРТ СТЕКУ", size_hint_x=0.5, md_bg_color=(0.2, 0.6, 0.2, 1), on_release=self.start_live_stack))
        stack_btns.add_widget(MDRaisedButton(text="🔄 СКИДАННЯ", size_hint_x=0.5, md_bg_color=(0.6, 0.2, 0.2, 1), on_release=self.reset_live_stack))
        layout_stack.add_widget(stack_btns)

        layout_stack.add_widget(MDRaisedButton(text="💾 ЗБЕРЕГТИ В ТЕЛЕФОН", pos_hint={"center_x": 0.5}, md_bg_color=(0.1, 0.5, 0.8, 1), on_release=self.save_stacked_image))
        layout_stack.add_widget(MDLabel(size_hint_y=None, height="10dp"))

        # ПОВЗУНКИ (сховані)
        self.slider_stretch = MDSlider(min=0, max=100, value=50, hint=True)
        self.label_stretch = MDLabel(text="☀️ Яскравість (Stretch)", size_hint_y=None, height="20dp", halign="center")
        self.slider_contrast = MDSlider(min=0, max=100, value=50, hint=True)
        self.label_contrast = MDLabel(text="🌗 Контраст", size_hint_y=None, height="20dp", halign="center")
        self.slider_blackpoint = MDSlider(min=0, max=100, value=10, hint=True)
        self.label_blackpoint = MDLabel(text="⚫ Точка чорного (Black Point)", size_hint_y=None, height="20dp", halign="center")
        self.slider_saturation = MDSlider(min=0, max=100, value=50, hint=True)
        self.label_saturation = MDLabel(text="🌈 Насиченість", size_hint_y=None, height="20dp", halign="center")
        self.slider_sharpen = MDSlider(min=0, max=100, value=10, hint=True)
        self.label_sharpen = MDLabel(text="📐 Різкість (Sharpen)", size_hint_y=None, height="20dp", halign="center")
        self.slider_clarity = MDSlider(min=0, max=100, value=15, hint=True)
        self.label_clarity = MDLabel(text="👁️ Чіткість (Clarity)", size_hint_y=None, height="20dp", halign="center")
        self.slider_denoise = MDSlider(min=0, max=100, value=20, hint=True)
        self.label_denoise = MDLabel(text="🌑 Шумозаглушення", size_hint_y=None, height="20dp", halign="center")

        self.active_tool_box = MDBoxLayout(orientation='vertical', size_hint_y=None, height="70dp")
        layout_stack.add_widget(self.active_tool_box)

        # ГОРИЗОНТАЛЬНЕ МЕНЮ
        tools_scroll = MDScrollView(do_scroll_x=True, do_scroll_y=False, size_hint_y=None, height="50dp")
        tools_menu = MDBoxLayout(orientation='horizontal', size_hint_x=None, spacing="10dp", padding="5dp")
        tools_menu.bind(minimum_width=tools_menu.setter('width')) 
        
        tools_menu.add_widget(MDRaisedButton(text="☀️ Яскравість", md_bg_color=(0.3, 0.3, 0.3, 1), on_release=lambda x: self.show_tool('stretch')))
        tools_menu.add_widget(MDRaisedButton(text="🌗 Контраст", md_bg_color=(0.3, 0.3, 0.3, 1), on_release=lambda x: self.show_tool('contrast')))
        tools_menu.add_widget(MDRaisedButton(text="⚫ Точка чорного", md_bg_color=(0.3, 0.3, 0.3, 1), on_release=lambda x: self.show_tool('blackpoint')))
        tools_menu.add_widget(MDRaisedButton(text="🌈 Насиченість", md_bg_color=(0.3, 0.3, 0.3, 1), on_release=lambda x: self.show_tool('saturation')))
        tools_menu.add_widget(MDRaisedButton(text="📐 Різкість", md_bg_color=(0.3, 0.3, 0.3, 1), on_release=lambda x: self.show_tool('sharpen')))
        tools_menu.add_widget(MDRaisedButton(text="👁️ Чіткість", md_bg_color=(0.3, 0.3, 0.3, 1), on_release=lambda x: self.show_tool('clarity')))
        tools_menu.add_widget(MDRaisedButton(text="🌑 Шум", md_bg_color=(0.3, 0.3, 0.3, 1), on_release=lambda x: self.show_tool('denoise')))
        
        tools_scroll.add_widget(tools_menu)
        layout_stack.add_widget(tools_scroll)
        self.show_tool('stretch')

        scroll_stack.add_widget(layout_stack)
        tab_stack.add_widget(scroll_stack)
        bottom_nav.add_widget(tab_stack)

        # =========================================================
        # ВКЛАДКА 5: ФАЙЛИ (ФАЙЛОВИЙ МЕНЕДЖЕР)
        # =========================================================
        tab_files = MDBottomNavigationItem(name='tab_files', text='Файли', icon='folder-image')
        layout_files = MDBoxLayout(orientation='vertical', padding="10dp", spacing="10dp")

        # Кнопка оновлення списку зверху
        files_header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height="50dp")
        btn_refresh_files = MDRaisedButton(
            text="🔄 ОНОВИТИ СПИСОК ФАЙЛІВ", 
            size_hint_x=1, 
            md_bg_color=(0.1, 0.5, 0.8, 1), 
            on_release=self.refresh_file_list
        )
        files_header.add_widget(btn_refresh_files)
        layout_files.add_widget(files_header)

        # Прокручуваний список
        scroll_files = MDScrollView()
        self.files_list = MDList()
        scroll_files.add_widget(self.files_list)
        layout_files.add_widget(scroll_files)

        tab_files.add_widget(layout_files)
        bottom_nav.add_widget(tab_files)

        screen.add_widget(bottom_nav)

        # Одразу заповнюємо файли при старті
        self.refresh_file_list(None)

        return screen

    # --- ЛОГІКА ФАЙЛОВОГО МЕНЕДЖЕРА ---
    def refresh_file_list(self, instance):
        self.files_list.clear_widgets()
        # Імітація списку файлів, що зберігаються на малинці
        dummy_files = [
            ("M31_Andromeda_Light_10s_001.fits", "15.4 MB  |  Сьогодні, 23:45"),
            ("M31_Andromeda_Light_10s_002.fits", "15.4 MB  |  Сьогодні, 23:46"),
            ("M31_Andromeda_Light_10s_003.fits", "15.4 MB  |  Сьогодні, 23:46"),
            ("Jupiter_Capture.ser", "450.2 MB  |  Вчора, 01:12"),
            ("LiveStack_Orion.jpg", "2.1 MB  |  Вчора, 02:30"),
            ("Dark_10s_001.fits", "15.4 MB  |  10 Серпня, 03:00"),
            ("Flat_001.fits", "15.4 MB  |  10 Серпня, 19:20")
        ]
        
        for name, size_date in dummy_files:
            # Визначаємо іконку залежно від розширення файлу
            if ".jpg" in name or ".png" in name:
                icon_name = "file-image"
            elif ".ser" in name or ".avi" in name:
                icon_name = "file-video"
            else:
                icon_name = "file-document-outline" # Для FITS файлів

            item = TwoLineIconListItem(text=name, secondary_text=size_date)
            icon = IconLeftWidget(icon=icon_name)
            item.add_widget(icon)
            
            # При кліку на файл можна буде його завантажити/видалити (зараз імітація)
            item.bind(on_release=lambda x, n=name: print(f"Клік по файлу: {n}"))
            
            self.files_list.add_widget(item)

    # --- ІНША ЛОГІКА ---
    def open_fullscreen(self, instance):
        modal = ModalView(size_hint=(1, 1), background_color=[0, 0, 0, 1])
        scatter = ScatterLayout(do_rotation=False, scale_min=1.0, scale_max=1.35)
        img_box = MDBoxLayout(md_bg_color=self.stack_preview_box.md_bg_color)
        lbl = MDLabel(text=self.stack_preview_label.text + "\n\n(Збільшення до 35%)", halign="center", theme_text_color="Custom", text_color=(1, 1, 1, 1))
        img_box.add_widget(lbl)
        scatter.add_widget(img_box)
        modal.add_widget(scatter)
        btn_close = MDRaisedButton(text="✖ ЗАКРИТИ", pos_hint={'right': 0.95, 'top': 0.95}, md_bg_color=(0.8, 0.1, 0.1, 1), on_release=modal.dismiss)
        modal.add_widget(btn_close)
        modal.open()

    def show_tool(self, tool_name):
        self.active_tool_box.clear_widgets()
        tools = {
            'stretch': (self.label_stretch, self.slider_stretch),
            'contrast': (self.label_contrast, self.slider_contrast),
            'blackpoint': (self.label_blackpoint, self.slider_blackpoint),
            'saturation': (self.label_saturation, self.slider_saturation),
            'sharpen': (self.label_sharpen, self.slider_sharpen),
            'clarity': (self.label_clarity, self.slider_clarity),
            'denoise': (self.label_denoise, self.slider_denoise)
        }
        lbl, sld = tools[tool_name]
        self.active_tool_box.add_widget(lbl)
        self.active_tool_box.add_widget(sld)

    def start_live_stack(self, instance):
        self.stacked_frames = 0
        if hasattr(self, 'stack_event'): self.stack_event.cancel()
        self.stack_event = Clock.schedule_interval(self.update_stack, 2)
    def update_stack(self, dt):
        self.stacked_frames += 1
        self.stack_info.text = f"Кадрів у стеку: {self.stacked_frames}"
        self.stack_preview_label.text = "[ Накладання кадрів... ]"
        self.stack_preview_box.md_bg_color = (0.1, 0.15, 0.1, 1)
    def reset_live_stack(self, instance):
        if hasattr(self, 'stack_event'): self.stack_event.cancel()
        self.stacked_frames = 0
        self.stack_preview_label.text = "Скинуто."
    def save_stacked_image(self, instance):
        self.stack_preview_box.md_bg_color = (0.1, 0.4, 0.1, 1) 
    def sync_equipment(self, instance):
        Clock.schedule_once(self.fill_equipment_lists, 1)
    def fill_equipment_lists(self, dt):
        self.spinner_mount.text = 'PMC-Eight'
        self.spinner_camera.text = 'INDI pylibcamera'
    def start_ekos_profile(self, instance): pass
    def take_photo(self, instance): pass
    def record_video(self, instance): pass
    def start_sequence(self, instance): pass
    def stop_sequence(self, instance): pass

if __name__ == '__main__':
    AstroApp().run()
