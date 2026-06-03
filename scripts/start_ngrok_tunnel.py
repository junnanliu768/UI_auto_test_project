from pyngrok import ngrok
import sys

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
public_url = ngrok.connect(port, "http").public_url
print(public_url)
# keep process alive
input()
