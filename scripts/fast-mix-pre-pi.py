import time
import struct
import requests
from datetime import datetime, timezone

def decimalDecoder(instance):
	if not instance.isError():
		regs = instance.registers
		raw = struct.pack('>HH', regs[1], regs[0])
		value = struct.unpack('>f', raw)[0]
		return float('{0:.2f}'.format(value))
	else:
		print("Erro: registradores não disponíveis.")
		return None

def read_decimal(client, address, qtd):
	if client.connect():
		request = client.read_holding_registers(address, count=qtd, device_id=UNIT_ID)
		value = decimalDecoder(request)
		time.sleep(1)
		return value
	else:
		return read_decimal(client, address, qtd)

def read_dword(client, address):
	if client.connect():
		request = client.read_holding_registers(address, count=2, device_id=UNIT_ID)
		if not request.isError():
			return (request.registers[1] << 16) | request.registers[0]  # DWORD = inteiro 32 bits sem sinal (low word first)
		else:
			print("Erro: registrador DWORD não disponível.")
			return None
	else:
		return read_dword(client, address)

def read_word(client, address):
	if client.connect():
		request = client.read_holding_registers(address, count=1, device_id=UNIT_ID)
		if not request.isError():
			return request.registers[0]  # Word = inteiro 16 bits sem sinal (0-65535)
		else:
			print("Erro: registrador não disponível.")
			return None
	else:
		return read_word(client, address)

def read_string(client, address, num_words):
	if client.connect():
		request = client.read_holding_registers(address, count=num_words, device_id=UNIT_ID)
		if not request.isError():
			chars = []
			for reg in request.registers:
				high_byte = (reg >> 8) & 0xFF
				low_byte = reg & 0xFF
				chars.append(chr(low_byte) if low_byte != 0 else '')
				chars.append(chr(high_byte) if high_byte != 0 else '')
			return ''.join(chars).strip()
		else:
			print("Erro: registrador string não disponível.")
			return None
	else:
		return read_string(client, address, num_words)

def read_bit(client, address, bit_position):
	if client.connect():
		request = client.read_holding_registers(address, count=1, device_id=UNIT_ID)
		if not request.isError():
			return (request.registers[0] >> bit_position) & 1
		else:
			print(f"Erro: registrador do bit não disponível. Endereço: {address}, Resposta: {request}")
			return None
	else:
		return read_bit(client, address, bit_position)

def clear_bit(client, address, bit_position):
	if client.connect():
		request = client.read_holding_registers(address, count=1, device_id=UNIT_ID)
		if not request.isError():
			new_value = request.registers[0] & ~(1 << bit_position)
			client.write_register(address, new_value, device_id=UNIT_ID)
			print(f"Bit {bit_position} do registrador {address} zerado.")
		else:
			print("Erro ao ler registrador para zerar bit.")
	else:
		clear_bit(client, address, bit_position)

from pymodbus.client import ModbusTcpClient

IP = "192.168.2.200"
PORT = 502
UNIT_ID = 1
RECEITA_REGISTRADOR = 28310
LOTE_REGISTRADOR = 9078
SEQUENCIA_REGISTRADOR = 9080
PRODUTO_REGISTRADOR = 9081
PESO_REGISTRADOR = 9102

BIT_TRIGGER_REGISTRADOR = 9011
BIT_TRIGGER_POSICAO = 15

API_URL = "http://localhost:8080/api/pre-mix/data"
POLL_INTERVAL = 1  # segundos entre cada verificação do bit


def ler_e_gravar(client):
	print("Bit de disparo ativo. Lendo registradores...")

	lote = read_dword(client, LOTE_REGISTRADOR)
	receita = read_string(client, RECEITA_REGISTRADOR, 20)
	sequencia = read_word(client, SEQUENCIA_REGISTRADOR)
	produto = read_string(client, PRODUTO_REGISTRADOR, 20)
	peso = read_decimal(client, PESO_REGISTRADOR, 2)

	clear_bit(client, BIT_TRIGGER_REGISTRADOR, BIT_TRIGGER_POSICAO)

	payload = {
		"lote": lote,
		"receita": receita,
		"sequencia": sequencia,
		"produto": produto,
		"peso": peso,
		"timestamp": datetime.now(timezone.utc).isoformat(),
	}
	print(payload)

	print("Enviando dados para o backend...")
	try:
		response = requests.post(API_URL, json=payload, timeout=5)
		if response.status_code == 201:
			print("Dados gravados com sucesso!")
		else:
			print(f"Erro ao gravar: HTTP {response.status_code} - {response.text}")
	except requests.exceptions.RequestException as e:
		print(f"Erro de conexão com o backend: {e}")


def main():
	print(f"Conectando ao CLP em {IP}:{PORT} (ID {UNIT_ID})...")
	client = ModbusTcpClient(IP, port=PORT)
	if not client.connect():
		print("Falha ao conectar ao CLP.")
		return
	print(f"Conectado. Monitorando bit {BIT_TRIGGER_POSICAO} do registrador {BIT_TRIGGER_REGISTRADOR}...")

	try:
		while True:
			print("Verificando bit de disparo...")
			bit = read_bit(client, BIT_TRIGGER_REGISTRADOR, BIT_TRIGGER_POSICAO)
			if bit == 1:
				print("Bit de disparo detectado!")
				ler_e_gravar(client)
			time.sleep(POLL_INTERVAL)
	except KeyboardInterrupt:
		print("\nEncerrando monitoramento.")
	finally:
		client.close()


if __name__ == "__main__":
	main()