from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
import pymysql

class AptidaoApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)
        
        # Cor de fundo
        with self.canvas.before:
            Color(0.5, 0.55, 0.5, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=self.update_rect, pos=self.update_rect)

        # CIIC input
        self.add_widget(Label(text='CIIC:', color=(0,0,0,1)))
        self.ciic_input = TextInput(multiline=False)
        self.ciic_input.bind(text=self.buscar_nome)
        self.ciic_input.bind(text=self.converter)
        self.add_widget(self.ciic_input)

        # Nome do Animal
        self.add_widget(Label(text='Nome do Animal:', color=(0,0,0,1)))
        self.nome_input = TextInput(multiline=False, readonly=True)
        self.add_widget(self.nome_input)

        # Tutor
        self.add_widget(Label(text='Tutor:', color=(0,0,0,1)))
        self.tutor_input = TextInput(multiline=False, readonly=True)
        self.add_widget(self.tutor_input)
        
        # Status de Aptidão
        self.add_widget(Label(text='Status de Aptidão:', color=(0,0,0,1)))
        self.status_layout = BoxLayout(orientation='horizontal', spacing=5)
        self.status_layout.add_widget(self.criar_checkbox("Apto", "status_apto"))
        self.status_layout.add_widget(self.criar_checkbox("Inapto", "status_inapto"))
        self.status_layout.add_widget(self.criar_checkbox("Apto-Especial", "status_apto_especial"))
        self.status_layout.add_widget(self.criar_checkbox("Controle de Espécie", "status_controle"))
        self.add_widget(self.status_layout)

        # Motivos Aptidão
        self.add_widget(Label(text='Motivos Aptidão:', color=(0,0,0,1)))
        self.motivos_input = TextInput(size_hint_y=None, height=150, multiline=True)
        scroll = ScrollView(size_hint=(1, None), size=(400, 150))
        scroll.add_widget(self.motivos_input)
        self.add_widget(scroll)

        # Botão Salvar
        self.salvar_button = Button(text='Salvar')
        self.salvar_button.bind(on_press=self.salvar_dados)
        self.add_widget(self.salvar_button)

    def update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos
    
    def criar_checkbox(self, texto, atributo):
        layout = BoxLayout(size_hint_y=None, height=30)
        checkbox = CheckBox(size_hint=(None, None), size=(25, 25))
        setattr(self, atributo, checkbox)
        checkbox.bind(active=self.deselecionar_outros)
        label = Label(text=texto, color=(0, 0, 0, 1), size_hint_x=None, width=150, halign="left", valign="middle")
        label.bind(size=label.setter('text_size'))
        layout.add_widget(checkbox)
        layout.add_widget(label)
        return layout

    def deselecionar_outros(self, instance, value):
        if value:
            for attr in ['status_apto', 'status_inapto', 'status_apto_especial', 'status_controle']:
                if getattr(self, attr) != instance:
                    getattr(self, attr).active = False

    def conectar_banco(self):
        try:
            return pymysql.connect(
                host="186.202.152.111",
                user="consorciofauna",
                password="cgF@1234",
                database="consorciofauna",
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.MySQLError as erro:
            self.mostrar_popup("Erro", f"Erro ao conectar ao banco:\n{erro}")
            return None
    
    def buscar_nome(self, instance, value):
        if value:
            nome, tutor = self.consultar_nome_tutor_banco(value)
            self.nome_input.text = nome if nome else ""
            self.tutor_input.text = tutor if tutor else ""
    
    def consultar_nome_tutor_banco(self, ciic):
        conexao = self.conectar_banco()
        if conexao:
            try:
                with conexao.cursor() as cursor:
                    sql = """
                    SELECT f_animal.nome AS nome_animal, f_tutor.Nome_Tutor AS nome_tutor
                    FROM f_animal
                    INNER JOIN f_tutor ON f_animal.ID_tutor = f_tutor.ID_tutor
                    WHERE f_animal.ciic = %s
                    """
                    cursor.execute(sql, (ciic,))
                    resultado = cursor.fetchone()
                    if resultado:
                        return resultado["nome_animal"], resultado["nome_tutor"]
            except pymysql.MySQLError as erro:
                self.mostrar_popup("Erro", f"Erro ao buscar nome e tutor: {erro}")
            finally:
                conexao.close()
        return None, None

    def salvar_dados(self, instance):
        ciic_animal = self.ciic_input.text
        nome_animal = self.nome_input.text
        
        status = next((s for s in ['Apto', 'Inapto', 'Apto-Especial', 'Controle de Espécie'] 
                       if getattr(self, f'status_{s.lower().replace("-", "_").replace(" ", "_")}').active), None)
        
        motivos = self.motivos_input.text
        if not all([ciic_animal, nome_animal, status, motivos]):
            self.mostrar_popup("Atenção", "Todos os campos devem ser preenchidos!")
            return
        
        conexao = self.conectar_banco()
        if conexao:
            try:
                with conexao.cursor() as cursor:
                    sql = """
                        INSERT INTO aptidao_animais (ciic, nome, status_aptidao, motivos)
                        VALUES (%s, %s, %s, %s)
                    """
                    valores = (ciic_animal, nome_animal, status, motivos)
                    cursor.execute(sql, valores)
                    conexao.commit()
                self.mostrar_popup("Sucesso", "Dados salvos com sucesso!")
                self.limpar_campos()
            except pymysql.MySQLError as erro:
                self.mostrar_popup("Erro", f"Erro ao salvar os dados: {erro}")
            finally:
                conexao.close()
    
    def mostrar_popup(self, titulo, mensagem):
        popup = Popup(title=titulo, content=Label(text=mensagem), size_hint=(None, None), size=(400, 200))
        popup.open()
    
    def limpar_campos(self):
        self.ciic_input.text = ""
        self.nome_input.text = ""
        self.tutor_input.text = ""
        for attr in ['status_apto', 'status_inapto', 'status_apto_especial', 'status_controle']:
            getattr(self, attr).active = False
        self.motivos_input.text = ""

    def converter(self, instance, value):
        self.ciic_input.text = value.upper()

class AptidaoAppKivy(App):
    def build(self):
        return AptidaoApp()

if __name__ == "__main__":
    AptidaoAppKivy().run()
