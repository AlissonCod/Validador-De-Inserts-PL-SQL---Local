# SQL Insert Validator 🔍

Ferramenta CLI em Python para **validação de comandos `INSERT INTO`** SQL,
com detecção de erros de sintaxe, mapeamento coluna→valor e sugestão de correção.

---

## 📁 Estrutura do Projeto

```
sql_insert_validator/
├── validator.py      # Programa principal (parse, validação, CLI)
├── build_exe.py      # Gerador do executável .exe via PyInstaller
├── tests.py          # Suite de testes automatizados
└── README.md         # Esta documentação
```

---

## ▶️ Como Executar

### Modo interativo (menu)
```bash
python validator.py
```

### SQL via argumento de linha de comando
```bash
python validator.py "INSERT INTO CLIENTES (ID, NOME) VALUES (1, 'Ana');"
```

### Múltiplos INSERTs via argumento
```bash
python validator.py "INSERT INTO A (X) VALUES (1); INSERT INTO B (Y) VALUES ('ok');"
```

---

## 🧪 Testes

```bash
python tests.py
```

---

## 📦 Gerar Executável `.exe` (Windows)

### Pré-requisito
- Python 3.10+ instalado

### Gerar com script automatizado
```bash
python build_exe.py
```

### Ou manualmente com PyInstaller
```bash
pip install pyinstaller
pyinstaller --onefile --console --name sql_insert_validator validator.py
```

O executável será gerado em `dist/sql_insert_validator.exe`.

### Usar o executável
```bash
sql_insert_validator.exe
sql_insert_validator.exe "INSERT INTO T (A) VALUES (1);"
```

---

## ✅ Funcionalidades

| Funcionalidade                         | Status |
|----------------------------------------|--------|
| Parse de INSERT INTO                   | ✅     |
| Validação coluna vs valores            | ✅     |
| Mapeamento coluna → valor              | ✅     |
| Detecção de mais colunas que valores   | ✅     |
| Detecção de mais valores que colunas   | ✅     |
| Detecção de erro de sintaxe (parênt.)  | ✅     |
| Inferência de tipo de valor            | ✅     |
| Sugestão de correção automática        | ✅     |
| Suporte a múltiplos INSERTs            | ✅     |
| Leitura de arquivo .sql                | ✅     |
| CLI interativa com menu                | ✅     |
| Saída colorida no terminal             | ✅     |
| Suite de testes automatizados          | ✅     |
| Geração de .exe via PyInstaller        | ✅     |

---

## 💡 Exemplos de Saída

### INSERT válido
```
═══════════════════════════════════════════════════════════════
  INSERT #1 — ✅ VÁLIDO
═══════════════════════════════════════════════════════════════
  🗄️  TABELA  : CLIENTES
  📋 COLUNAS : 4
  💾 VALORES : 4
  ─────────────────────────────────────────────────────────────
  🔗 MAPEAMENTO COLUNA → VALOR:
  ID           →  101              [NÚMERO]
  NOME         →  'João Silva'     [STRING]
  EMAIL        →  'joao@email.com' [STRING]
  DT_CADASTRO  →  '2024-03-15'    [DATA]
  ─────────────────────────────────────────────────────────────
  ✅ INSERT válido e consistente!
```

### INSERT com erro
```
═══════════════════════════════════════════════════════════════
  INSERT #2 — ❌ INVÁLIDO
═══════════════════════════════════════════════════════════════
  ❌ ERROS ENCONTRADOS:
    [1] Mais colunas (5) do que valores (3). Faltam 2 valor(es)...
  💡 SUGESTÃO DE CORREÇÃO:
  INSERT INTO PEDIDOS
            (ID_PEDIDO, ID_CLIENTE, VALOR, STATUS, DT_PEDIDO)
     VALUES (999, 42, 150.00, NULL, NULL);
```

---

## 📌 Requisitos

- Python 3.10 ou superior  
- Biblioteca `customtkinter` para a interface gráfica (`pip install customtkinter`)
- PyInstaller apenas para geração do `.exe`
