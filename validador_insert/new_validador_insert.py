import re
import sys

def separar_valores(valores_str):
    """
    Separa os valores por vírgula, mas ignora as vírgulas que estão dentro de aspas simples.
    Ex: 'São Paulo, SP', 10 -> ['São Paulo, SP', '10']
    """
    padrao = re.compile(r"""(?:'[^']*'|[^,]+)""")
    return [match.strip() for match in padrao.findall(valores_str) if match.strip()]

def analisar_insert(sql):
    """Analisa a string SQL e extrai tabela, colunas e valores."""
    # Remove quebras de linha para facilitar a análise
    sql = sql.replace('\n', ' ').strip()
    
    # Expressão Regular para capturar os blocos do INSERT
    regex = r"(?i)INSERT\s+INTO\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*VALUES\s*\((.*?)\);?$"
    match = re.search(regex, sql)
    
    if not match:
        return None, None, None, "Erro de sintaxe: O comando não segue o padrão 'INSERT INTO tabela (colunas) VALUES (valores);' ou possui parênteses mal fechados."

    tabela = match.group(1)
    colunas_str = match.group(2)
    valores_str = match.group(3)
    
    colunas = [c.strip() for c in colunas_str.split(',')]
    valores = separar_valores(valores_str)
    
    return tabela, colunas, valores, None

def validar_e_exibir(sql):
    """Realiza as validações e imprime os resultados formatados na tela."""
    print("\n" + "="*50)
    print("🔍 ANALISANDO COMANDO SQL...")
    print("="*50)
    
    tabela, colunas, valores, erro_sintaxe = analisar_insert(sql)
    
    if erro_sintaxe:
        print(f"❌ STATUS: REPROVADO\nMotivo: {erro_sintaxe}")
        return

    qtd_colunas = len(colunas)
    qtd_valores = len(valores)
    
    print(f"Tabela alvo : {tabela}")
    print(f"Qtd Colunas : {qtd_colunas}")
    print(f"Qtd Valores : {qtd_valores}\n")
    
    # Mapeamento e Validação de Quantidade
    print("📌 MAPEAMENTO:")
    max_len = max(qtd_colunas, qtd_valores)
    
    for i in range(max_len):
        col = colunas[i] if i < qtd_colunas else "[!] FALTANDO COLUNA"
        val = valores[i] if i < qtd_valores else "[!] FALTANDO VALOR"
        print(f"   {col}  -->  {val}")
        
    print("\n" + "-"*50)
    
    # Análise de Inconsistências
    if qtd_colunas == qtd_valores:
        print("✅ STATUS: APROVADO")
        print("Nenhuma divergência encontrada. O comando parece estruturalmente correto.")
    else:
        print("❌ STATUS: REPROVADO")
        if qtd_colunas > qtd_valores:
            diff = qtd_colunas - qtd_valores
            print(f"Motivo: Há mais COLUNAS do que VALORES. Estão sobrando {diff} coluna(s).")
            
            # Sugestão de correção
            valores_corrigidos = valores + ["'???'"] * diff
            sugestao = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({', '.join(valores_corrigidos)});"
            print("\n💡 SUGESTÃO DE CORREÇÃO (Preenchendo valores faltantes):")
            print(sugestao)
            
        elif qtd_valores > qtd_colunas:
            diff = qtd_valores - qtd_colunas
            print(f"Motivo: Há mais VALORES do que COLUNAS. Estão sobrando {diff} valor(es).")
            
            # Sugestão de correção
            colunas_corrigidas = colunas + ["NOVA_COLUNA"] * diff
            sugestao = f"INSERT INTO {tabela} ({', '.join(colunas_corrigidas)}) VALUES ({', '.join(valores)});"
            print("\n💡 SUGESTÃO DE CORREÇÃO (Adicionando colunas faltantes):")
            print(sugestao)

    print("="*50 + "\n")

def menu_interativo():
    """Interface de Linha de Comando (CLI)."""
    print("="*60)
    print("   VALIDADOR DE INSERT SQL - v1.0   ".center(60))
    print("="*60)
    print("Instruções:")
    print("- Cole seu comando INSERT INTO completo e aperte ENTER.")
    print("- Para sair, digite 'sair' ou 'exit'.")
    print("="*60 + "\n")

    while True:
        try:
            sql_input = input("SQL> ")
            if sql_input.strip().lower() in ['sair', 'exit', 'quit']:
                print("\nEncerrando o programa. Até logo!")
                sys.exit(0)
            
            if not sql_input.strip():
                continue
                
            validar_e_exibir(sql_input)
            
        except KeyboardInterrupt:
            print("\nEncerrando o programa...")
            sys.exit(0)

if __name__ == "__main__":
    menu_interativo()