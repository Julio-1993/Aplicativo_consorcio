from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from Apitidaokivy import AptidaoApp
from Movikivy import MovimentacaoApp
from Fotoskivy import FotosApp


class MainMenuScreen(Screen):
    pass

class AptidaoScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout()
        layout.add_widget(AptidaoApp())
        self.add_widget(layout)

class MovimentacaoScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout()
        layout.add_widget(MovimentacaoApp())
        self.add_widget(layout)

class FotosScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout()
        layout.add_widget(FotosApp())
        self.add_widget(layout)

class MainApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name="main_menu"))
        sm.add_widget(AptidaoScreen(name="aptidao"))
        sm.add_widget(MovimentacaoScreen(name="movimentacao"))
        sm.add_widget(FotosScreen(name="fotos"))
        return sm

if __name__ == "__main__":
    MainApp().run()