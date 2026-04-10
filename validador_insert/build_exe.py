"""
Script auxiliar para gerar o executável .exe usando PyInstaller.
Execute: python build_exe.py
"""
import subprocess
import sys
import os

def main():
    print("=" * 60)
    print("  SQL Insert Validator — Gerador de Executável")
    print("=" * 60)

    # 1. Instala PyInstaller se necessário
    print("\n[1/3] Verificando PyInstaller...")
    try:
        import PyInstaller
        print("      PyInstaller já instalado.")
    except ImportError:
        print("      Instalando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("      PyInstaller instalado com sucesso.")

    # 1.5 Instala dependências do projeto
    print("\n[1.5/3] Verificando dependências (customtkinter)...")
    try:
        import customtkinter
        print("      customtkinter já instalado.")
    except ImportError:
        print("      Instalando customtkinter...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
        print("      customtkinter instalado com sucesso.")

    # 2. Gera o executável
    print("\n[2/3] Gerando executável...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    validator  = os.path.join(script_dir, "validator.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                        # Único arquivo .exe
        "--console",                        # Mantém janela de console
        "--name", "sql_insert_validator",   # Nome do executável
        "--clean",                          # Limpa cache anterior
        validator
    ]

    resultado = subprocess.run(cmd, cwd=script_dir)

    if resultado.returncode == 0:
        exe_path = os.path.join(script_dir, "dist", "sql_insert_validator.exe")
        print(f"\n[3/3] ✅ Executável gerado com sucesso!")
        print(f"      Localização: {exe_path}")
        print("\n  Como usar:")
        print("    sql_insert_validator.exe")
        print("    sql_insert_validator.exe \"INSERT INTO T (A) VALUES (1);\"")
    else:
        print("\n  ❌ Falha ao gerar executável. Verifique os logs acima.")

if __name__ == "__main__":
    main()
