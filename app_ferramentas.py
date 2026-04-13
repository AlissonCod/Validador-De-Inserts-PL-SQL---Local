import re
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# ==============================================================================
# BACKEND - FORMATADOR DE QUERY
# ==============================================================================
def formatar_valor(valor):
    if valor is None or valor == '':
        return 'NULL'
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, str):
        if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', valor):
            return f"TO_DATE('{valor}', 'YYYY-MM-DD HH24:MI:SS')"
        if re.match(r'\d{4}-\d{2}-\d{2}', valor):
            return f"TO_DATE('{valor[:10]}', 'YYYY-MM-DD')"
        return f"'{valor}'"
    return str(valor)

def aplicar_params_na_query(query, params):
    resultado = query
    for idx in sorted(params.keys()):
        resultado = resultado.replace('?', formatar_valor(params[idx]), 1)
    return resultado

def organizar_query(query):
    if not query: return ""
    query = re.sub(r'\s+', ' ', query).strip()
    token_pattern = re.compile(r"('([^']|'')*'|\"([^\"]|\"\")*\"|[(),]|\s+|[^\s(),]+)")
    tokens = [m.group() for m in token_pattern.finditer(query) if m.group().strip()]
    
    formatted = []
    indent_level = 0
    indent_str = "\t"
    
    keywords_newline = {
        "SELECT", "FROM", "WHERE", "HAVING", "GROUP BY", "ORDER BY", 
        "UNION", "UNION ALL", "EXCEPT", "INTERSECT",
        "UPDATE", "SET", "INSERT INTO", "VALUES", "DELETE FROM"
    }
    keywords_join = {
        "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "OUTER JOIN", 
        "FULL JOIN", "CROSS JOIN"
    }
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        upper_token = token.upper()
        next_token = tokens[i+1].upper() if i+1 < len(tokens) else ""
        two_words = f"{upper_token} {next_token}"
        
        if two_words in keywords_newline or two_words in keywords_join:
            token = f"{token} {tokens[i+1]}"
            upper_token = two_words
            i += 1
            
        if upper_token in keywords_newline:
            if formatted: formatted.append("\n")
            formatted.append(indent_str * indent_level + token)
        elif upper_token in keywords_join:
            if formatted: formatted.append("\n")
            formatted.append(indent_str * indent_level + token)
        elif upper_token in ("AND", "OR"):
            if formatted: formatted.append("\n")
            formatted.append(indent_str * (indent_level + 1) + token)
        elif token == "(":
            formatted.append(" " + token)
            indent_level += 1
            formatted.append("\n" + indent_str * indent_level)
        elif token == ")":
            indent_level = max(0, indent_level - 1)
            formatted.append("\n" + indent_str * indent_level + token)
        elif token == ",":
            formatted.append("\n" + indent_str * indent_level + token)
        else:
            if not formatted:
                formatted.append(token)
            else:
                last = formatted[-1]
                if last.endswith("\t") or last.endswith("\n"):
                    formatted.append(token)
                elif last == ",":
                    formatted.append(token)
                else:
                    formatted.append(" " + token)
        i += 1
    return "".join(formatted)

# ==============================================================================
# BACKEND - VALIDADOR DE INSERT
# ==============================================================================
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

    try:
        partes_tabela = re.search(r'INSERT\s+INTO\s+([\w\.]+)', sql_clean, re.I)
        res.tabela = partes_tabela.group(1)
        
        cols, pos_fim_cols, _ = _extrair_lista_parenteses(sql_clean, partes_tabela.end())
        res.colunas = [c.strip().replace('"', '') for c in cols if c.strip()]
        
        val_match = re.search(r'VALUES\s*\(', sql_clean, re.I)
        if val_match:
            vals, _, _ = _extrair_lista_parenteses(sql_clean, val_match.start())
            res.valores = vals
            
        if len(res.colunas) != len(res.valores):
            res.status = StatusValidacao.ERRO
            res.erros.append(f"Divergência: {len(res.colunas)} colunas vs {len(res.valores)} valores.")
        else:
            res.status = StatusValidacao.OK
    except Exception as e:
        res.status = StatusValidacao.ERRO
        res.erros.append(f"Erro no processamento: {str(e)}")
        
    return res

# ==============================================================================
# FRONTEND - FORMATADOR DE QUERY (Migrado para CustomTkinter)
# ==============================================================================
class AppFormatador(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Sankhya -- Formatador de Query - Criado por Alisson Junior")
        self.geometry("650x750")
        
        # Faz com que a janela puxe o foco assim que for aberta
        self.focus()

        ctk.CTkLabel(self, text="Cole a sua QUERY do monitor de consultas aqui:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.entrada = ctk.CTkTextbox(self, height=150, font=("Consolas", 12))
        self.entrada.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para organizar os botões lado a lado
        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(pady=10)

        ctk.CTkButton(frame_botoes, text="Formatar Query", fg_color="#019916", hover_color="#0b5ed7", font=("Segoe UI", 12, "bold"), command=self.processar_texto).pack(side="left", padx=5)
        ctk.CTkButton(frame_botoes, text="Organizar Query", fg_color="#17a2b8", hover_color="#138496", font=("Segoe UI", 12, "bold"), command=self.acao_organizar).pack(side="left", padx=5)
        ctk.CTkButton(frame_botoes, text="Limpar Tudo", fg_color="#dc3545", hover_color="#e9091f", font=("Segoe UI", 12, "bold"), command=self.limpar_tudo).pack(side="left", padx=5)

        ctk.CTkLabel(self, text="Resultado final da query - Copie e cole no Dbexplorer:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.saida = ctk.CTkTextbox(self, height=150, font=("Consolas", 12))
        self.saida.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(self, text="Parâmetros identificados:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.saida_params = ctk.CTkTextbox(self, height=100, font=("Consolas", 12))
        self.saida_params.pack(fill="both", expand=True, padx=10, pady=5)

    def acao_organizar(self):
        texto = self.saida.get("1.0", "end").strip()
        if not texto:
            messagebox.showwarning("Aviso", "Não há query formatada para organizar. Clique em 'Formatar Query' primeiro.")
            return
        query_organizada = organizar_query(texto)
        self.saida.delete("1.0", "end")
        self.saida.insert("end", query_organizada)

    def limpar_tudo(self):
        self.entrada.delete("1.0", "end")
        self.saida.delete("1.0", "end")
        self.saida_params.delete("1.0", "end")

    def processar_texto(self):
        texto = self.entrada.get("1.0", "end")
        try:
            partes = texto.split("Params:")
            query = partes[0].strip()
            params = {}
            if len(partes) > 1:
                linhas_params = partes[1].splitlines()
                for linha in linhas_params:
                    match = re.match(r'\s*(\d+)\s*=\s*(.*)', linha)
                    if match:
                        idx = int(match.group(1))
                        valor = match.group(2).strip()
                        if valor == '': params[idx] = None
                        elif valor.isdigit(): params[idx] = int(valor)
                        else:
                            try: params[idx] = float(valor)
                            except ValueError: params[idx] = valor

            lista_params_formatada = []
            segmentos = query.split('?')
            for idx in sorted(params.keys()):
                valor_fmt = formatar_valor(params[idx])
                coluna = "Desconhecida"
                if 0 <= idx - 1 < len(segmentos):
                    segmento = segmentos[idx - 1]
                    limpo = re.sub(r'(?i)\s*(=|!=|<>|>=|<=|>|<|LIKE|IN|IS)\s*\(?\s*$', '', segmento)
                    match_col = re.search(r'([\w.]+)\s*$', limpo)
                    if match_col:
                        coluna = match_col.group(1)
                lista_params_formatada.append(f"Parametro {idx} ({coluna}) = {valor_fmt}")

            sql_final = aplicar_params_na_query(query, params)
            self.saida.delete("1.0", "end")
            self.saida.insert("end", sql_final)
            self.saida_params.delete("1.0", "end")
            self.saida_params.insert("end", "\n".join(lista_params_formatada))
        except Exception as e:
            messagebox.showerror("Erro", str(e))


# ==============================================================================
# FRONTEND - VALIDADOR DE INSERT
# ==============================================================================
class AppValidador(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("SQL Insert Validador - Para Analista PL/SQL - By: Alisson")
        self.geometry("900x700")
        
        self.focus()

        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.label_status = ctk.CTkLabel(self, text="Status da Validação:", font=("Arial", 14, "bold"))
        self.label_status.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="w")

        self.txt_status = ctk.CTkTextbox(self, font=("Consolas", 12), height=100, state="disabled", fg_color="#1e1e1e")
        self.txt_status.grid(row=1, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="ew")

        self.label_input = ctk.CTkLabel(self, text="Cole seu INSERT SQL abaixo:", font=("Arial", 14, "bold"))
        self.label_input.grid(row=2, column=0, padx=(20, 10), pady=(10, 0), sticky="w")
        
        self.txt_input = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.txt_input.grid(row=3, column=0, padx=(20, 10), pady=10, sticky="nsew")

        self.label_output = ctk.CTkLabel(self, text="Resultado da Análise:", font=("Arial", 14, "bold"))
        self.label_output.grid(row=2, column=1, padx=(10, 20), pady=(10, 0), sticky="w")

        self.txt_output = ctk.CTkTextbox(self, font=("Consolas", 12), state="disabled", fg_color="#1e1e1e")
        self.txt_output.grid(row=3, column=1, padx=(10, 20), pady=10, sticky="nsew")

        self.btn_validar = ctk.CTkButton(self, text="VALIDAR SQL", command=self.executar_validacao, fg_color="#f3a805", hover_color="#14375e", height=40)
        self.btn_validar.grid(row=4, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="ew")

    def executar_validacao(self):
        sql_input = self.txt_input.get("1.0", "end-1c")
        if not sql_input.strip(): return
        
        resultado = parse_e_validar(sql_input)

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

        self.txt_output.configure(state="normal")
        self.txt_output.delete("1.0", "end")
            
        res_texto = "MAPEAMENTO IDENTIFICADO:\n\n"
        for i in range(max(len(resultado.colunas), len(resultado.valores))):
            col = resultado.colunas[i] if i < len(resultado.colunas) else "???"
            val = resultado.valores[i] if i < len(resultado.valores) else "???"
            res_texto += f"[{i+1}] {col}  -->  {val}\n"

        self.txt_output.insert("1.0", res_texto)
        self.txt_output.configure(state="disabled")


# ==============================================================================
# MENU PRINCIPAL (Launcher)
# ==============================================================================
class MenuPrincipal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Executavel PL/SQL - By Alisson Junior")
        self.geometry("450x300")
        ctk.set_appearance_mode("dark")
        
        # Centralizar na tela
        self.eval('tk::PlaceWindow . center')

        # Título do Menu
        self.lbl_titulo = ctk.CTkLabel(self, text="🛠️ Ferramentas de Banco de Dados", font=("Arial", 20, "bold"))
        self.lbl_titulo.pack(pady=(40, 30))

        # Botão: Formatador
        self.btn_formatador = ctk.CTkButton(self, text="1.Formatador de Query-Monitor de consultas", font=("Segoe UI", 14, "bold"), height=45, fg_color="#019916", hover_color="#0b5ed7", command=self.abrir_formatador)
        self.btn_formatador.pack(fill="x", padx=60, pady=10)

        # Botão: Validador
        self.btn_validador = ctk.CTkButton(self, text="2.Validador de Insert", font=("Segoe UI", 14, "bold"), height=45, fg_color="#17a2b8", hover_color="#138496", command=self.abrir_validador)
        self.btn_validador.pack(fill="x", padx=60, pady=10)

    def abrir_formatador(self):
        AppFormatador(self)

    def abrir_validador(self):
        AppValidador(self)

if __name__ == "__main__":
    app = MenuPrincipal()
    app.mainloop()