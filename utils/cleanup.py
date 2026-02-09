import os
import shutil

def clean_temp_directory(temp_dir):
    """
    Limpa os arquivos temporários
    """
    try:
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
            print("✓ Temporary directory cleaned successfully")
    except Exception as e:
        print(f"Warning: Error cleaning temporary directory: {e}")