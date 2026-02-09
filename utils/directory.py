import os

def create_directory_structure():
    """ 
    Cria os diretórios necessários
    """
    try:
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        directories = {
            'base': os.path.join(script_dir, "tts_workspace"),
            'models': os.path.join(script_dir, "tts_workspace", "models"),
            'temp': os.path.join(script_dir, "tts_workspace", "temp"),
            'videos': os.path.join(script_dir, "videos")
        }
        
        for directory in directories.values():
            os.makedirs(directory, exist_ok=True)
            
        return directories
    except Exception as e:
        raise Exception(f"Error creating directories: {e}")

def create_working_directory():
    try:
        base_dir = os.path.join(os.getcwd(), "tts_workspace")
        models_dir = os.path.join(base_dir, "models")
        temp_dir = os.path.join(base_dir, "temp")
        
        for directory in [base_dir, models_dir, temp_dir]:
            os.makedirs(directory, exist_ok=True)
        
        return base_dir, models_dir, temp_dir
    except Exception as e:
        raise Exception(f"Error creating directories: {e}")
