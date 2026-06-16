def decrypt_rc4(hex_text, secret_key):
    # Превращаем Hex-строку обратно в массив байт
    ciphertext = bytes.fromhex(hex_text)
    
    # Преобразуем ключ в байты (поддерживает UTF-8)
    key_bytes = secret_key.encode('utf-8')
    
    # Инициализация S-блока (KSA - Key Scheduling Algorithm)
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key_bytes[i % len(key_bytes)]) % 256
        s[i], s[j] = s[j], s[i]
        
    # Генерация потока и XOR (PRGA - Pseudo-Random Generation Algorithm)
    i = 0
    j = 0
    decrypted_bytes = bytearray()
    
    for byte in ciphertext:
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        
        # Операция XOR для расшифровки байта
        decrypted_byte = byte ^ s[(s[i] + s[j]) % 256]
        decrypted_bytes.append(decrypted_byte)
        
    # Декодируем байты обратно в строку UTF-8
    return decrypted_bytes.decode('utf-8')