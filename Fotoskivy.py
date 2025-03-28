from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
import ftplib
import pymysql


class FotosApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)

        # Credenciais do FTP
        self.ftp_host = "ftp.guiraguira.com.br"
        self.ftp_user = "guiraguira1"
        self.ftp_pass = "Guiraguira1@10203040"
        self.ftp_base_dir = "/web/cgf/Testes_julio"
        self.ftp_url = "https://guiraguira.com.br/admcgf/Testes_julio/"

        # Credenciais do Banco de Dados
        self.db_host = "186.202.152.111"
        self.db_user = "consorciofauna"
        self.db_password = "cgF@1234"
        self.db_name = "consorciofauna"

        self.selected_files = []

        # Categoria da foto
        self.add_widget(Label(text='Categoria da foto:'))
        categorias = ['Adoção', 'Atendimento', 'Banho e tosa', 'Boas práticas', 'Casqueamento', 'Doma e montaria',
                      'Enriquecimento', 'Evento de adoção', 'Internação', 'Pós-adoção', 'Práticas integrativas',
                      'Reintegração', 'Soltura', 'Transferência']
        self.categoria_spinner = Spinner(text='Selecione', values=categorias)
        self.add_widget(self.categoria_spinner)

        # Grupo animal
        self.add_widget(Label(text='Grupo Animal:'))
        grupos_animais = ['Aves domésticas áquaticas', 'Aves domésticas terrestres', 'Bovídeos', 'Canídeos',
                          'Equídeos', 'Felídeos', 'Leporídeos']
        self.grupo_spinner = Spinner(text='Selecione', values=grupos_animais)
        self.add_widget(self.grupo_spinner)

        # Campo de entrada para CIIC
        self.add_widget(Label(text='CIIC do Animal: (Opcional)'))
        self.ciic_input = TextInput(multiline=False)
        self.ciic_input.bind(text=self.converter_ciic_maiusculo)
        self.add_widget(self.ciic_input)

        # Botão para anexo de fotos
        self.anexar_btn = Button(text='Anexar Fotos')
        self.anexar_btn.bind(on_press=self.abrir_dialogo_arquivos)
        self.add_widget(self.anexar_btn)

        # Lista de arquivos selecionados
        self.arquivos_list = TextInput(readonly=True, multiline=True)
        self.add_widget(self.arquivos_list)

        # Legenda da foto
        self.add_widget(Label(text='Legenda da Foto:'))
        self.legenda_input = TextInput(multiline=True)
        self.add_widget(self.legenda_input)

        # Botão de Envio
        self.enviar_btn = Button(text='Enviar Fotos')
        self.enviar_btn.bind(on_press=self.enviar_fotos_ftp)
        self.add_widget(self.enviar_btn)

    def converter_ciic_maiusculo(self, instance, value):
        """Converte o texto do campo CIIC para letras maiúsculas."""
        self.ciic_input.text = value.upper()

    def abrir_dialogo_arquivos(self, instance):
        """Abre o diálogo para selecionar múltiplos arquivos."""
        content = BoxLayout(orientation='vertical')
        
        file_chooser = FileChooserListView(filters=['*.png', '*.jpg', '*.jpeg'])
        
        content.add_widget(file_chooser)
        
        select_button = Button(text="Selecionar", size_hint_y=None, height=50)
        
        def selecionar_e_fechar():
            """Seleciona os arquivos e fecha o popup."""
            if file_chooser.selection:
                self.selected_files.extend(file_chooser.selection)
                self.arquivos_list.text += "\n".join(file_chooser.selection) + "\n"
            popup.dismiss()
        
        select_button.bind(on_press=lambda x: selecionar_e_fechar())
        
        content.add_widget(select_button)
        
        popup = Popup(title="Selecionar Fotos", content=content, size_hint=(0.9, 0.9))
        
        popup.open()

    def enviar_fotos_ftp(self, instance):
        """Envia as fotos para o servidor FTP e salva as informações no banco de dados."""
        
        if not self.selected_files:
            return self.mostrar_popup("Aviso", "Por favor, selecione um ou mais arquivos primeiro.")

        categoria = self.categoria_spinner.text
        legenda = self.legenda_input.text.strip()
        Grupo_Animal = self.grupo_spinner.text
        ciic = self.ciic_input.text.strip()

        # Determinar o subdiretório
        category_to_folder = {
            'Adoção': 'Adocao',
            'Atendimento': 'Atendimento',
            'Banho e tosa': 'Banho_tosa',
            'Boas práticas': 'Boas_praticas',
            'Casqueamento': 'Casqueamento',
            'Doma e montaria': 'Doma_montaria',
            'Enriquecimento': 'Enriquecimento',
            'Evento de adoção': 'Evento_adocao',
            'Internação': 'Internacao',
            'Pós-adoção': 'Pos_adocao',
            'Práticas integrativas': 'Pratica_integrativa',
            'Reintegração': 'Reintegracao',
            'Soltura': 'Soltura',
            'Transferência': 'Transferencia'
        }

        if categoria in category_to_folder:
            sub_dir = category_to_folder[categoria]
        else:
            self.mostrar_popup("Aviso", "Categoria inválida.")
            return

        # Acessar o FTP
        ftp_dir = f"{self.ftp_base_dir}/{sub_dir}"

        try:
            # Conecta ao servidor FTP
            ftp = ftplib.FTP(self.ftp_host, self.ftp_user, self.ftp_pass)
            ftp.encoding = "utf-8"
            ftp.set_pasv(True)

            # Conecta ao banco de dados (usando pymysql)
            mydb = pymysql.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            try:
                with mydb.cursor() as mycursor:
                    # Tente acessar o diretório
                    try:
                        ftp.cwd(ftp_dir)
                    except ftplib.error_perm as e:
                        if str(e).startswith("550"):
                            # Cria um diretório caso não exista
                            ftp.mkd(sub_dir)
                            ftp.cwd(sub_dir)
                        else:
                            raise Exception(f"Erro ao acessar o diretório: {str(e)}")
                    # Envia cada arquivo selecionado e salva as informações no banco de dados
                    for file_path in self.selected_files:
                        nome_arquivo_ftp = file_path.split('/')[-1]
                        nome_arquivo_ftp = nome_arquivo_ftp.replace(':', '_').replace('\\', '_')
                        try:
                            with open(file_path, "rb") as file:
                                ftp.storbinary(f"STOR {nome_arquivo_ftp}", file)
                            # Construir o caminho completo no servidor FTP
                            ftp_file_path = f"{self.ftp_url}/{sub_dir}/{nome_arquivo_ftp}"
                            # Salva as informações no banco de dados (usando pymysql)
                            sql = "INSERT INTO ficha_obito_imagens (ciic, Grupo_Animal, caminho, categoria, legenda) VALUES (%s, %s, %s, %s, %s)"
                            val = (ciic or None, Grupo_Animal, ftp_file_path, categoria, legenda)
                            mycursor.execute(sql, val)
                            mydb.commit()

                            print(f"Arquivo {nome_arquivo_ftp} enviado e informações salvas no banco de dados com sucesso.")
                        except Exception as e:
                            self.mostrar_popup("Aviso", f"Erro ao enviar/salvar {nome_arquivo_ftp}: {str(e)}")

            finally:
                mydb.close()
            ftp.quit()

            self.mostrar_popup("Sucesso", "Fotos enviadas e informações salvas no banco de dados com sucesso!")

        except Exception as e:
            self.mostrar_popup("Erro", f"Erro ao enviar as fotos ou salvar no banco de dados: {str(e)}")

    def mostrar_popup(self, titulo, mensagem):
        popup = Popup(title=titulo, content=Label(text=mensagem), size_hint=(None, None), size=(400, 200))
        popup.open()

class FotosAppKivy(App):
    def build(self):
        return FotosApp()

if __name__ == "__main__":
    FotosAppKivy().run()
