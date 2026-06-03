# Breaking-data

![Shiny](https://img.shields.io/badge/Shiny-75AADB?style=for-the-badge)
![Statistics](https://img.shields.io/badge/Statistics-Academic-blue?style=for-the-badge)


## Configurando o ambiente


### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Instalar as dependências

```bash
pip install -r requirements.txt
```

## <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg" width="20"> Colaboração e Desenvolvimento


Após o clone do projeto, crie uma branch a partir da branch principal:

```bash
git checkout -b feature/nome-da-funcionalidade
```

Exemplos:

```bash
git checkout -b feature/dashboard-vendas
git checkout -b feature/analise-generos
git checkout -b feature/graficos-regionais
```

### Salvando alterações

Após concluir uma etapa do desenvolvimento:

```bash
git add .
git commit -m "feat: adiciona análise de vendas por plataforma"
```

### Enviando para o GitHub

```bash
git push -u origin feature/nome-da-funcionalidade
```

### Integração das alterações

1. Atualize sua branch com as alterações mais recentes;
2. Abra um Pull Request;
