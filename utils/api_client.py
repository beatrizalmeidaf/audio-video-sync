import requests
import os
import json

def generate_voice_clone(text, ref_audio_path, api_url, speed=1.0):
    """
    Envia requisição para a API, detecta se a resposta é um link S3 e baixa o áudio final.
    """
    try:
        if not os.path.exists(ref_audio_path):
            print(f"   [API Error] Reference audio not found: {ref_audio_path}")
            return None

        is_port_9000 = ":9000" in api_url
        is_port_7000 = ":7000" in api_url

        data = {'text': text}
        files = {}
        
        # abre o arquivo para envio
        with open(ref_audio_path, 'rb') as f:
            if is_port_9000:
                files = {'file': ('ref.wav', f, 'audio/wav')}
                data['speed'] = float(speed)
            else:
                files = {'audio': ('ref.wav', f, 'audio/wav')}

            # timeout alto pois clonagem demora
            response = requests.post(api_url, files=files, data=data, timeout=120)

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            
            # API retorna JSON com URL (caso da porta 7000)
            if 'application/json' in content_type or response.content.strip().startswith(b'['):
                try:
                    resp_json = response.json()
                    # formato: [{"url": "https://..."}]
                    if isinstance(resp_json, list) and len(resp_json) > 0 and 'url' in resp_json[0]:
                        audio_url = resp_json[0]['url']
                        print(f"   [API] Downloading audio from: {audio_url[:30]}...")
                        
                        # baixa o áudio real da URL do S3
                        audio_response = requests.get(audio_url)
                        return audio_response.content
                    
                    elif isinstance(resp_json, dict) and 'url' in resp_json:
                        audio_response = requests.get(resp_json['url'])
                        return audio_response.content
                        
                except Exception as e:
                    print(f"   [API Error] Failed to parse JSON or download URL: {e}")
                    return None

            # API retorna o áudio binário direto 
            return response.content
            
        else:
            print(f"   [API Error] {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"   [API Exception] {str(e)}")
        return None