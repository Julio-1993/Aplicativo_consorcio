import re
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
import pymysql
from datetime import date
from datetime import datetime

class DateInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        # Permitir apenas números
        pat = re.compile('[^0-9]')
        substring = re.sub(pat, '', substring)

        # Adicionar barras automaticamente
        text = self.text
        if len(text) == 2 or len(text) == 5:
            substring = '/' + substring

        # Limitar o comprimento a 10 caracteres (dd/mm/aaaa)
        if len(text) + len(substring) > 10:
            return

        super().insert_text(substring, from_undo=from_undo)
    
class MovimentacaoApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)
        
        # Adicionando fundo cinza claro
        with self.canvas.before:
            Color(0.94, 0.94, 0.94, 1)  # Cinza claro
            self.rect = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=self.update_rect, pos=self.update_rect)

        # CIIC input
        self.add_widget(Label(text='CIIC:', color=(0,0,0,1)))
        self.ciic_input = TextInput(multiline=False)
        self.ciic_input.bind(text=self.buscar_nome)
        self.ciic_input.bind(text=self.converter)
        self.add_widget(self.ciic_input)

        # Nome do Animal e Data lado a lado
        nome_data_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)

        # Nome do Animal
        nome_data_layout.add_widget(Label(text='Nome do Animal:', color=(0, 0, 0, 1)))
        self.nome_input = TextInput(multiline=False, readonly=True)
        nome_data_layout.add_widget(self.nome_input)

        # Tipo de Movimentação
        self.add_widget(Label(text='Tipo de Movimentação:', color=(0,0,0,1)))
        tipos_movimentacao = ['Adoção','Alta','Atendimento assistencialista','Consulta','Desistência de adoção',
                              'Eutanásia','Evento de adoção','Fuga - Adoção','Internação','Óbito', 'Óbito - Adoção',
                               'Resgate','Reintegração','Retorno para atendimento','Saída de atendimento','Transferência de instalação']
        self.tipo_movimentacao = Spinner(text='Selecione', values=tipos_movimentacao)
        self.add_widget(self.tipo_movimentacao)

        # Data
        nome_data_layout.add_widget(Label(text='Data:', color=(0, 0, 0, 1)))
        self.data_input = DateInput(text=date.today().strftime("%d/%m/%Y"), multiline=False)
        nome_data_layout.add_widget(self.data_input)    

        # Adicionando ao layout principal
        self.add_widget(nome_data_layout)

        # Local de Saída
        self.add_widget(Label(text='Local de Saída:', color=(0,0,0,1)))
        self.locais_codigos = {
            "CAATA Batatal": 16, "Clínicas terceiras": 2, "Hotel Matilha Rural - Moeda": 6,
            "Lupug - Cocais": 8, "Lupug - Monlevade": 4, "Maternau - Sabará": 9,
            "Maternau - Vespasiano": 10, "UFMG": 13, "Jurisdição do tutor": 7,
            "Propriedade do adotante": 12, "CAATA Bom Retiro": 17, "Obras": 49
        }
        self.local_saida = Spinner(text='Selecione', values=list(self.locais_codigos.keys()))
        self.add_widget(self.local_saida)

        # Local de Chegada
        self.add_widget(Label(text='Local de Chegada:', color=(0,0,0,1)))
        self.local_chegada = Spinner(text='Selecione', values=list(self.locais_codigos.keys()))
        self.add_widget(self.local_chegada)

        # Observações
        self.add_widget(Label(text='Observações:', color=(0,0,0,1)))
        self.obs_input = TextInput(size_hint_y=None, height=100, multiline=True)
        scroll = ScrollView(size_hint=(1, None), size=(400, 100))
        scroll.add_widget(self.obs_input)
        self.add_widget(scroll)

        # Botão Salvar
        self.salvar_button = Button(text='Salvar', background_color=(0.11, 0.15, 0.57, 1))
        self.salvar_button.bind(on_press=self.salvar_dados)
        self.add_widget(self.salvar_button)

    def update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos

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
            self.mostrar_popup("Erro", f"Erro ao conectar ao banco: {erro}")
            return None

    def buscar_nome(self, instance, value):
        if value:
            nome = self.consultar_nome_banco(value)
            self.nome_input.text = nome if nome else ""

    def consultar_nome_banco(self, ciic):
        conexao = self.conectar_banco()
        if conexao:
            try:
                with conexao.cursor() as cursor:
                    cursor.execute("SELECT nome FROM f_animal WHERE ciic = %s", (ciic,))
                    resultado = cursor.fetchone()
                    return resultado["nome"] if resultado else None
            except pymysql.MySQLError as erro:
                self.mostrar_popup("Erro", f"Erro ao buscar o nome: {erro}")
            finally:
                conexao.close()
        return None
    
    def salvar_dados(self, instance):
        ciic = self.ciic_input.text.strip()
        tipo = self.tipo_movimentacao.text
        data = self.data_input.text
        local_saida = self.local_saida.text
        local_chegada = self.local_chegada.text
        obs = self.obs_input.text.strip()

        if not all([ciic, tipo != 'Selecione', data, local_saida != 'Selecione', local_chegada != 'Selecione', obs]):
            self.mostrar_popup("Atenção", "Todos os campos devem ser preenchidos!")
            return

        # Converter a data para o formato yyyy/mm/dd
        try:
            data_obj = datetime.strptime(data, "%d/%m/%Y")
            data = data_obj.strftime("%Y/%m/%d")
        except ValueError:
            self.mostrar_popup("Erro", "Formato de data inválido. Use dd/mm/aaaa.")
            return
    
        local_saida_codigo = self.locais_codigos.get(local_saida)
        local_chegada_codigo = self.locais_codigos.get(local_chegada)

        conexao = self.conectar_banco()
        if conexao:
            try:
                with conexao.cursor() as cursor:
                    sql = """
                        INSERT INTO d_movimentacao (CIIC, Tipo, Local_Saida, Local_Chegada, Data, obs_mov)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    valores = (ciic, tipo, local_saida_codigo, local_chegada_codigo, data, obs)
                    cursor.execute(sql, valores)
                    conexao.commit()
                self.mostrar_popup("Sucesso", "Movimentação registrada com sucesso!")
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
        self.tipo_movimentacao.text = "Selecione"
        self.data_input.text = date.today().strftime("%d/%m/%Y")
        self.local_saida.text = "Selecione"
        self.local_chegada.text = "Selecione"
        self.obs_input.text = ""

    def converter(self, instance, value):
        self.ciic_input.text = value.upper()
    
class MovimentacaoAppKivy(App):
    def build(self):
        return MovimentacaoApp()

if __name__ == "__main__":
    MovimentacaoAppKivy().run()