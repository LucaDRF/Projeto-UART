import sys
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports

class SerialTerminalApp:
    TERMINATORS = {
        "CRLF (\\r\\n)": b"\r\n",
        "LF (\\n)": b"\n",
        "CR (\\r)": b"\r",
        "Nenhum": b""
    }

    def __init__(self, root):
        self.root = root
        # Título da janela principal
        self.root.title("Terminal Serial UART - Sistemas Embarcados | Ecomp Poli/UPE")
        self.root.geometry("800x700")
        self.root.minsize(700, 550)

        # Variáveis de Controle Serial
        self.serial_port = None
        self.is_connected = False
        self.read_thread = None
        self.rx_queue = queue.Queue()

        # Variáveis da Interface
        self.var_hex_rx = tk.BooleanVar(value=False)
        self.var_hex_tx = tk.BooleanVar(value=False)
        self.tx_history = []  # Lista para armazenar o histórico de comandos digitados

        # Construção da Interface
        self._create_widgets()

        # Loop periódico para verificar dados recebidos na fila (Thread-Safe)
        self._check_rx_queue()

        # Evento de fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        # -------------------------------------------------------------
        # CABEÇALHO INSTITUCIONAL / PROJETO
        # -------------------------------------------------------------
        header_frame = ttk.Frame(self.root, padding=(10, 8))
        header_frame.pack(fill="x")

        lbl_project_title = ttk.Label(
            header_frame, 
            text="Terminal Serial UART", 
            font=("Sans", 13, "bold")
        )
        lbl_project_title.pack(anchor="w")

        lbl_course_info = ttk.Label(
            header_frame, 
            text="Disciplina: Sistemas Embarcados — Ecomp Poli/UPE", 
            font=("Sans", 9, "italic")
        )
        lbl_course_info.pack(anchor="w")

        # Linha divisória
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=10, pady=(0, 5))

        # -------------------------------------------------------------
        # PAINEL DE CONFIGURAÇÃO (COM & Baud Rate)
        # -------------------------------------------------------------
        config_frame = ttk.LabelFrame(self.root, text=" Configurações de Conexão ", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        # Rótulo da Porta COM
        ttk.Label(config_frame, text="Porta COM:").grid(row=0, column=0, padx=(5, 2), pady=5, sticky="w")
        
        # Dropdown da Porta COM
        self.combo_ports = ttk.Combobox(config_frame, state="readonly", width=12)
        self.combo_ports.grid(row=0, column=1, padx=(0, 2), pady=5, sticky="w")

        # Botão para atualizar lista de portas
        self.btn_refresh = ttk.Button(config_frame, text="↻", width=3, command=self.refresh_ports)
        self.btn_refresh.grid(row=0, column=2, padx=(0, 15), pady=5)

        # Rótulo e Dropdown de Baud Rate
        ttk.Label(config_frame, text="Baud Rate:").grid(row=0, column=3, padx=(0, 2), pady=5, sticky="w")
        self.combo_baud = ttk.Combobox(config_frame, state="readonly", width=10)
        self.combo_baud['values'] = ('9600', '19200', '38400', '57600', '115200', '230400', '460800', '921600')
        self.combo_baud.current(0)  # Padrão: 9600
        self.combo_baud.grid(row=0, column=4, padx=(0, 15), pady=5)

        # Botão Conectar / Desconectar
        self.btn_connect = ttk.Button(config_frame, text="Conectar", command=self.toggle_connection)
        self.btn_connect.grid(row=0, column=5, padx=5, pady=5)

        # Indicador de Status
        self.lbl_status = ttk.Label(config_frame, text="Status: Desconectado", foreground="red", font=("Sans", 9, "bold"))
        self.lbl_status.grid(row=0, column=6, padx=(15, 5), pady=5, sticky="e")

        config_frame.columnconfigure(6, weight=1)

        # -------------------------------------------------------------
        # PAINEL DE RECEPÇÃO (RX)
        # -------------------------------------------------------------
        rx_frame = ttk.LabelFrame(self.root, text=" Painel de Recepção (RX) ", padding=10)
        rx_frame.pack(fill="both", expand=True, padx=10, pady=5)

        rx_toolbar = ttk.Frame(rx_frame)
        rx_toolbar.pack(fill="x", padx=5, pady=(0, 5))

        chk_hex_rx = ttk.Checkbutton(rx_toolbar, text="Exibir em HEX", variable=self.var_hex_rx)
        chk_hex_rx.pack(side="left")

        btn_clear_rx = ttk.Button(rx_toolbar, text="Limpar Tela RX", command=self.clear_rx)
        btn_clear_rx.pack(side="right")

        self.txt_rx = scrolledtext.ScrolledText(rx_frame, height=10, state="disabled", wrap=tk.WORD, font=("Consolas", 10))
        self.txt_rx.pack(fill="both", expand=True, padx=5, pady=5)

        # -------------------------------------------------------------
        # PAINEL DE TRANSMISSÃO (TX)
        # -------------------------------------------------------------
        tx_frame = ttk.LabelFrame(self.root, text=" Painel de Transmissão (TX) ", padding=10)
        tx_frame.pack(fill="both", expand=True, padx=10, pady=5)

        tx_opts_frame = ttk.Frame(tx_frame)
        tx_opts_frame.pack(fill="x", padx=5, pady=(0, 5))

        ttk.Label(tx_opts_frame, text="Terminador:").pack(side="left", padx=(0, 5))
        self.combo_terminator = ttk.Combobox(tx_opts_frame, state="readonly", width=12)
        self.combo_terminator['values'] = list(self.TERMINATORS.keys())
        self.combo_terminator.current(0)  # Padrão: CRLF (\r\n)
        self.combo_terminator.pack(side="left", padx=(0, 15))

        chk_hex_tx = ttk.Checkbutton(tx_opts_frame, text="Enviar como HEX (ex: 41 42 0D)", variable=self.var_hex_tx)
        chk_hex_tx.pack(side="left")

        input_subframe = ttk.Frame(tx_frame)
        input_subframe.pack(fill="x", padx=5, pady=5)

        self.entry_tx = ttk.Combobox(input_subframe, font=("Consolas", 10))
        self.entry_tx.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_tx.bind("<Return>", lambda event: self.send_data())

        self.btn_send = ttk.Button(input_subframe, text="Enviar", command=self.send_data)
        self.btn_send.pack(side="right")

        ttk.Label(tx_frame, text="Histórico de Mensagens Enviadas:").pack(anchor="w", padx=5, pady=(5, 0))
        self.txt_tx_log = scrolledtext.ScrolledText(tx_frame, height=4, state="disabled", wrap=tk.WORD, font=("Consolas", 9))
        self.txt_tx_log.pack(fill="both", expand=True, padx=5, pady=5)

        # Buscar portas ativas ao iniciar
        self.refresh_ports()

    def refresh_ports(self):
        """Atualiza a lista de portas COM disponíveis no sistema."""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.combo_ports['values'] = port_list
        
        if port_list:
            if self.combo_ports.get() not in port_list:
                self.combo_ports.current(0)
        else:
            self.combo_ports.set('')

    def toggle_connection(self):
        """Alterna entre Conectar e Desconectar."""
        if not self.is_connected:
            self.connect_serial()
        else:
            self.disconnect_serial()

    def connect_serial(self):
        """Abre a conexão com a porta serial selecionada."""
        port = self.combo_ports.get()
        baud = self.combo_baud.get()

        if not port:
            messagebox.showerror("Erro de Conexão", "Nenhuma porta COM selecionada ou disponível.")
            return

        try:
            baud_rate = int(baud)
            self.serial_port = serial.Serial(port=port, baudrate=baud_rate, timeout=1.0)
            self.is_connected = True

            self.combo_ports.config(state="disabled")
            self.combo_baud.config(state="disabled")
            self.btn_refresh.config(state="disabled")

            self.btn_connect.config(text="Desconectar")
            self.lbl_status.config(text=f"Conectado ({port})", foreground="green")

            self.read_thread = threading.Thread(target=self._read_serial_thread, daemon=True)
            self.read_thread.start()

        except serial.SerialException as e:
            messagebox.showerror(
                "Erro na Porta Serial", 
                f"A porta {port} não pôde ser aberta.\n\n"
                f"Verifique se ela está ativa ou sendo usada por outro programa.\n\nDetalhes: {e}"
            )
            self.serial_port = None
            self.is_connected = False
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Falha ao conectar: {e}")

    def disconnect_serial(self):
        """Encerra a conexão serial e restaura os controles."""
        self.is_connected = False
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.serial_port = None

        self.combo_ports.config(state="readonly")
        self.combo_baud.config(state="readonly")
        self.btn_refresh.config(state="normal")
        self.btn_connect.config(text="Conectar")
        self.lbl_status.config(text="Status: Desconectado", foreground="red")

    def _read_serial_thread(self):
        """Thread que lê bytes da porta serial em segundo plano."""
        while self.is_connected and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_bytes = self.serial_port.read(self.serial_port.in_waiting)
                    if raw_bytes:
                        self.rx_queue.put(raw_bytes)
            except (serial.SerialException, OSError) as e:
                if self.is_connected:
                    self.rx_queue.put(('DISCONNECT_ERROR', str(e)))
                break
            except Exception:
                break

    def _check_rx_queue(self):
        """Processa a fila de recepção na thread principal (GUI)."""
        while not self.rx_queue.empty():
            item = self.rx_queue.get()
            if isinstance(item, tuple) and item[0] == 'DISCONNECT_ERROR':
                self.disconnect_serial()
                messagebox.showerror("Conexão Perdida", f"O dispositivo serial foi desconectado repentinamente.\n\n{item[1]}")
            elif isinstance(item, bytes):
                if self.var_hex_rx.get():
                    hex_str = ' '.join(f"{b:02X}" for b in item) + ' '
                    self.append_rx(hex_str)
                else:
                    text_str = item.decode('utf-8', errors='replace')
                    self.append_rx(text_str)

        self.root.after(100, self._check_rx_queue)

    def append_rx(self, content):
        """Insere o conteúdo recebido na área RX."""
        self.txt_rx.config(state="normal")
        self.txt_rx.insert(tk.END, content)
        self.txt_rx.see(tk.END)
        self.txt_rx.config(state="disabled")

    def clear_rx(self):
        """Limpa a caixa de texto de recepção."""
        self.txt_rx.config(state="normal")
        self.txt_rx.delete("1.0", tk.END)
        self.txt_rx.config(state="disabled")

    def send_data(self):
        """Envia os dados do campo TX e atualiza o histórico da lista suspensa."""
        raw_input = self.entry_tx.get()
        if not raw_input and not self.var_hex_tx.get():
            return

        if not self.is_connected or not self.serial_port or not self.serial_port.is_open:
            messagebox.showwarning("Aviso de Conexão", "Você precisa se conectar a uma porta COM antes de enviar dados.")
            return

        try:
            if self.var_hex_tx.get():
                clean_hex = raw_input.replace(" ", "").replace(",", "").replace("0x", "").replace("0X", "")
                if len(clean_hex) % 2 != 0:
                    messagebox.showerror("Erro HEX", "A sequência Hexadecimal deve ter um número par de caracteres.")
                    return
                bytes_to_send = bytes.fromhex(clean_hex)
                log_msg = f"[HEX]: {' '.join(clean_hex[i:i+2].upper() for i in range(0, len(clean_hex), 2))}"
            else:
                terminator_key = self.combo_terminator.get()
                terminator_bytes = self.TERMINATORS.get(terminator_key, b"\r\n")
                bytes_to_send = raw_input.encode('utf-8') + terminator_bytes
                log_msg = f"[TXT]: {raw_input}"

            self.serial_port.write(bytes_to_send)
            self.append_tx_log(log_msg)

            if raw_input in self.tx_history:
                self.tx_history.remove(raw_input)
            self.tx_history.insert(0, raw_input)
            self.entry_tx['values'] = self.tx_history

            self.entry_tx.set('')

        except ValueError:
            messagebox.showerror("Erro HEX", "Sequência Hexadecimal inválida. Use caracteres de 0 a 9 e A a F.")
        except serial.SerialException as e:
            messagebox.showerror("Erro ao Enviar", f"Falha no envio de dados: {e}")
            self.disconnect_serial()

    def append_tx_log(self, text):
        """Registra a mensagem enviada no log TX."""
        self.txt_tx_log.config(state="normal")
        self.txt_tx_log.insert(tk.END, text + "\n")
        self.txt_tx_log.see(tk.END)
        self.txt_tx_log.config(state="disabled")

    def on_closing(self):
        """Garante encerramento seguro da comunicação ao fechar."""
        self.disconnect_serial()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialTerminalApp(root)
    root.mainloop()