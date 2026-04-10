import re
import customtkinter as ctk
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# --- LÓGICA DO BACKEND (Adaptada) ---

class TipoValor(Enum):
    STRING = "STRING"
    NUMERO = "NÚMERO"
    DATA = "DATA"
    NULO = "NULL"
    BOOLEANO = "BOOLEANO"
    EXPRESSAO = "EXPRESSÃO/FUNÇÃO"
    DESCONHECIDO = "?"

class StatusValidacao(Enum):
    OK = "✅ VÁLIDO"
    ERRO = "❌ INVÁLIDO"
    AVISO = "⚠️ ATENÇÃO"

@dataclass
class MapColVal:
    coluna: str
    valor: str
    tipo: TipoValor = TipoValor.DESCONHECIDO

@dataclass
class ResultadoValidacao:
    sql_original: str
    tabela: str = ""
    colunas: list[str] = field(default_factory=list)
    valores: list[str] = field(default_factory=list)
    mapeamento: list[MapColVal] = field(default_factory=list)
    status: StatusValidacao = StatusValidacao.OK
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    sugestao: Optional[str] = None
    tem_colunas_explicitas: bool = True

def inferir_tipo(valor: str) -> TipoValor:
    v = valor.strip()
    if v.upper() == "NULL": return TipoValor.NULO
    if v.upper() in ("TRUE", "FALSE"): return TipoValor.BOOLEANO
    if v.startswith("'") and v.endswith("'"): return TipoValor.STRING
    if re.fullmatch(r"-?\d+(\.\d+)?", v): return TipoValor.NUMERO
    if "(" in v or "SYSDATE" in v.upper(): return TipoValor.EXPRESSAO
    return TipoValor.DESCONHECIDO

def _extrair_lista_parenteses(texto: str, pos_inicial: int):
    i = pos_inicial
    while i < len(texto) and texto[i] != '(': i += 1
    if i >= len(texto): return [], i, "Parêntese '(' não encontrado."
    
    i += 1
    nivel, em_string, buf, item_buf = 1, False, [], []
    while i < len(texto) and nivel > 0:
        c = texto[i]
        if c == "'": em_string = not em_string
        elif not em_string:
            if c == '(': nivel += 1
            elif c == ')': nivel -= 1
            elif c == ',' and nivel == 1:
                buf.append(''.join(item_buf).strip())
                item_buf = []
                i += 1; continue
        if nivel > 0: item_buf.append(c)
        i += 1
    buf.append(''.join(item_buf).strip())
    return buf, i, ""

def parse_e_validar(sql: str) -> ResultadoValidacao:
    sql_clean = re.sub(r'--.*', '', sql).strip()
    res = ResultadoValidacao(sql_original=sql)
    
    if not re.match(r'^INSERT\s+INTO', sql_clean, re.I):
        res.status = StatusValidacao.ERRO
        res.erros.append("Não inicia com INSERT INTO")
        return res

    # Extração simples de tabela e partes
    try:
        partes_tabela = re.search(r'INSERT\s+INTO\s+([\w\.]+)', sql_clean, re.I)
        res.tabela = partes_tabela.group(1)
        
        # Colunas e Valores
        cols, pos_fim_cols, _ = _extrair_lista_parenteses(sql_clean, partes_tabela.end())
        res.colunas = [c.strip().replace('"', '') for c in cols if c.strip()]
        
        val_match = re.search(r'VALUES\s*\(', sql_clean, re.I)
        if val_match:
            vals, _, _ = _extrair_lista_parenteses(sql_clean, val_match.start())
            res.valores = vals
            
        # Validação de consistência
        if len(res.colunas) != len(res.valores):
            res.status = StatusValidacao.ERRO
            res.erros.append(f"Divergência: {len(res.colunas)} colunas vs {len(res.valores)} valores.")
        else:
            res.status = StatusValidacao.OK
    except Exception as e:
        res.status = StatusValidacao.ERRO
        res.erros.append(f"Erro no processamento: {str(e)}")
        
    return res

# --- INTERFACE GRÁFICA ---

class AppSQL(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SQL Insert Validador - Para Analista PL/SQL - By: Alisson")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")

        # Configuração de Grid
        self.grid_rowconfigure(1, weight=0) # O status no topo terá altura fixa
        self.grid_rowconfigure(3, weight=1) # Os campos de texto (meio) vão expandir
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Status (Superior, ocupando as duas colunas)
        self.label_status = ctk.CTkLabel(self, text="Status da Validação:", font=("Arial", 14, "bold"))
        self.label_status.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="w")

        self.txt_status = ctk.CTkTextbox(self, font=("Consolas", 12), height=100, state="disabled", fg_color="#1e1e1e")
        self.txt_status.grid(row=1, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="ew")

        # 2. Entrada de Texto (Esquerda)
        self.label_input = ctk.CTkLabel(self, text="Cole seu INSERT SQL abaixo:", font=("Arial", 14, "bold"))
        self.label_input.grid(row=2, column=0, padx=(20, 10), pady=(10, 0), sticky="w")
        
        self.txt_input = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.txt_input.grid(row=3, column=0, padx=(20, 10), pady=10, sticky="nsew")

        # 3. Saída de Resultado (Direita)
        self.label_output = ctk.CTkLabel(self, text="Resultado da Análise:", font=("Arial", 14, "bold"))
        self.label_output.grid(row=2, column=1, padx=(10, 20), pady=(10, 0), sticky="w")

        self.txt_output = ctk.CTkTextbox(self, font=("Consolas", 12), state="disabled", fg_color="#1e1e1e")
        self.txt_output.grid(row=3, column=1, padx=(10, 20), pady=10, sticky="nsew")

        # 4. Botão de Ação (Inferior, ocupando as duas colunas)
        self.btn_validar = ctk.CTkButton(self, text="VALIDAR SQL", command=self.executar_validacao, 
                                         fg_color="#f3a805", hover_color="#14375e", height=40)
        self.btn_validar.grid(row=4, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="ew")

    def executar_validacao(self):
        # Pegar texto da interface
        sql_input = self.txt_input.get("1.0", "end-1c")
        
        if not sql_input.strip():
            return

        # Rodar Backend
        resultado = parse_e_validar(sql_input)

        # Exibir STATUS na interface
        self.txt_status.configure(state="normal")
        self.txt_status.delete("1.0", "end")
        
        status_texto = f"STATUS: {resultado.status.value}\n"
        status_texto += f"TABELA: {resultado.tabela}\n"
        status_texto += "-"*50 + "\n"
        
        if resultado.erros:
            status_texto += "ERROS ENCONTRADOS:\n"
            for err in resultado.erros:
                status_texto += f" -> {err}\n"
        else:
            status_texto += "✅ Nenhuma divergência de estrutura encontrada.\n"
            
        self.txt_status.insert("1.0", status_texto)
        self.txt_status.configure(state="disabled")

        # Exibir MAPEAMENTO na interface (Caixa da direita)
        self.txt_output.configure(state="normal")
        self.txt_output.delete("1.0", "end")
            
        res_texto = "MAPEAMENTO IDENTIFICADO:\n\n"
        for i in range(max(len(resultado.colunas), len(resultado.valores))):
            col = resultado.colunas[i] if i < len(resultado.colunas) else "???"
            val = resultado.valores[i] if i < len(resultado.valores) else "???"
            res_texto += f"[{i+1}] {col}  -->  {val}\n"

        self.txt_output.insert("1.0", res_texto)
        self.txt_output.configure(state="disabled")

if __name__ == "__main__":
    app = AppSQL()
    app.mainloop()
