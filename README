# Sistema Cliente-Servidor UART — STM32

Projeto da disciplina de **Sistemas Embarcados**, utilizando comunicação UART entre duas placas STM32 e um terminal serial Python.

## Grupo
- Luca de Roldão
- Weslley Mattheus
- Pedro Henrique Bezerra

## Hardware utilizado

- **NUCLEO-L476RG:** Cliente
- **STM32F407 Discovery:** Servidor
- Cabos jumper para comunicação UART
- Cabo USB para programação e comunicação com o PC

## Conexões entre as placas

A comunicação utiliza **USART1 na Nucleo** e **USART2 na Discovery**.

| NUCLEO-L476RG (Cliente) | Discovery F407 (Servidor) |
|---|---|
| PA9 (TX) | PA3 (RX) |
| PA10 (RX) | PA2 (TX) |
| GND | GND |

**Importante:** TX deve ser conectado ao RX da outra placa, e ambas precisam compartilhar GND.

### Alimentação

- Conectar a Nucleo ao PC via USB para programação, alimentação e comunicação serial.
- A Discovery pode ser programada separadamente usando o mesmo cabo USB.
- Para alimentar as duas placas simultaneamente usando apenas um USB, é possível utilizar uma alimentação externa de 5 V na Discovery proveniente da Nucleo, **desde que sejam verificadas a configuração dos jumpers e a capacidade de corrente das placas**. Não fazer essa conexão sem essa verificação.

## Configuração STM32CubeMX

### Cliente — NUCLEO-L476RG

| Periférico | Configuração |
|---|---|
| USART1 | Comunicação com servidor (PA9/PA10) |
| USART2 | Comunicação serial com PC (PA2/PA3) |
| PC13 | Botão B1 com interrupção EXTI |
| PA5 | LED LD2 como GPIO Output |
| DMA | RX e TX nas USARTs |
| NVIC | Interrupções USART e EXTI habilitadas |

### Servidor — Discovery F407

| Periférico | Configuração |
|---|---|
| USART2 | Comunicação com cliente (PA2/PA3) |
| PA0 | Botão USER com interrupção EXTI |
| DMA | RX e TX da USART2 |
| NVIC | Interrupções USART e EXTI habilitadas |

**Configuração UART para ambas:** 115200 baud, 8 bits, sem paridade, 1 stop bit (8N1), modo assíncrono.

## Funcionamento

1. O botão da Discovery incrementa um contador.
2. Ao pressionar o botão da Nucleo, o cliente envia `0x5A` ao servidor por interrupção.
3. O servidor responde com o contador por interrupção.
4. O cliente envia `0xA5` para confirmar que está pronto para receber a tabela.
5. O servidor transmite a tabela de integrantes por DMA e zera o contador após concluir a transmissão.
6. A Nucleo pisca o LED a 1 Hz pela quantidade de vezes recebida, bloqueando novos comandos durante a operação.
7. Ao finalizar, envia o número de eventos por interrupção e a tabela por DMA ao computador.

## Terminal serial Python

O projeto utiliza o arquivo `terminal_serial.py` fornecido pelo professor para visualizar os dados enviados pela USART2 da Nucleo.

**Instalação:**

```bash
python -m pip install pyserial
```

**Execução:**

```bash
python terminal_serial.py
```

Na interface gráfica:

1. Selecionar a porta COM da Nucleo (ST-LINK Virtual COM Port).
2. Configurar **115200 baud**.
3. Clicar em **Conectar**.
4. Manter a opção `Exibir em HEX` desmarcada para visualizar texto.

**Exemplo de saída:**

```text
Numero de eventos = 003
TABELA DE MEMBROS
Nome1 - Matricula1
Nome2 - Matricula2
Nome3 - Matricula3
```

## Compilação e gravação

1. Abrir os projetos no STM32CubeIDE.
2. Compilar cada projeto com `Ctrl+B`.
3. Conectar a placa correspondente ao PC via USB.
4. Gravar o firmware usando `Run` ou `Debug`.
5. Conectar as duas placas conforme a tabela de ligações.
6. Iniciar o terminal Python e testar os botões.

**Tecnologias:** C, STM32 HAL, STM32CubeMX, STM32CubeIDE, UART, EXTI, NVIC, DMA e Python/PySerial.