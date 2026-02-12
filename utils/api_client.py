import requests
import os
import json
import time

def generate_voice_clone(text, ref_audio_path, api_url, speed=1.0):
    """
    Gera voz clonada usando a API especificada. Suporta tanto a API do Qwen (porta 9000) quanto a do Mira (porta 7000).
    """
    MAX_RETRIES = 3
    
    if not os.path.exists(ref_audio_path):
        print(f"   [API Error] Reference audio not found: {ref_audio_path}")
        return None

    # configuração da porta
    is_port_9000 = ":9000" in api_url
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # reabre o arquivo a cada tentativa para garantir que o ponteiro de leitura está no início
            with open(ref_audio_path, 'rb') as f:
                data = {'text': text}
                files = {}
                
                if is_port_9000:
                    # porta 9000: Qwen (file + speed)
                    files = {'file': ('ref.wav', f, 'audio/wav')}
                    data['speed'] = float(speed)
                else:
                    # porta 7000: Mira (audio)
                    files = {'audio': ('ref.wav', f, 'audio/wav')}

                # timeout de 5 minutos (300s) para evitar quedas em áudios longos
                response = requests.post(api_url, files=files, data=data, timeout=300)

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                is_json = 'application/json' in content_type or response.content.strip().startswith(b'{') or response.content.strip().startswith(b'[')

                if is_json:
                    try:
                        resp_json = response.json()
                        audio_url = None
                        
                        # logica para extrair URL de áudio do JSON, considerando os formatos das APIs
                        # caso 1: Lista [{"url": "..."}] ou [{"download_url": "..."}]
                        if isinstance(resp_json, list) and len(resp_json) > 0:
                            item = resp_json[0]
                            if isinstance(item, dict):
                                audio_url = item.get('url') or item.get('download_url')

                        # caso 2: Dicionário {"url": "..."} ou {"download_url": "..."}
                        elif isinstance(resp_json, dict):
                            audio_url = resp_json.get('url') or resp_json.get('download_url')
                            
                        if audio_url:
                            try:
                                audio_resp = requests.get(audio_url, timeout=60)
                                if audio_resp.status_code == 200:
                                    return audio_resp.content
                                else:
                                    print(f"   [API Error] Failed to download audio URL ({audio_resp.status_code})")
                            except Exception as dl_err:
                                print(f"   [API Error] Exception downloading audio URL: {dl_err}")
                        else:
                            print(f"   [API Warning] JSON received but no 'url' or 'download_url' key found: {str(resp_json)[:100]}")
                            
                    except Exception as e:
                        print(f"   [API Error] JSON parsing failed despite seeming like JSON: {e}")
                

                if response.content.startswith(b'RIFF') or len(response.content) > 1000:
                    return response.content
                
                print(f"   [API Warning] Content not recognized as audio/url. First 50 bytes: {response.content[:50]}")
            
            else:
                print(f"   [API Error] Status {response.status_code}: {response.text[:200]}")
            

            if response.status_code in [500, 502, 503, 504, 429]:
                print(f"   [API] Server issues (Attempt {attempt}/{MAX_RETRIES}). Retrying in 5 seconds...")
                time.sleep(5)
                continue 
            else:
                break 

        except requests.exceptions.Timeout:
            print(f"   [API Error] Timeout on attempt {attempt}. Server took too long.")
            time.sleep(2)
        except requests.exceptions.ConnectionError:
            print(f"   [API Error] Connection Error on attempt {attempt}. Check if API is online.")
            time.sleep(2)
        except Exception as e:
            print(f"   [API Exception] Critical error: {str(e)}")
            break

    print("   [API] All attempts failed.")
    return None