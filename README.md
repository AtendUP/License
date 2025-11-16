# 🔐 License Server API

Sistema de validação e gerenciamento de licenças de software com Python Flask + PostgreSQL (Neon).

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/AtendUP/License)

---

## 📋 Índice

- [Sobre](#sobre)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Deploy](#deploy)
- [Endpoints da API](#endpoints-da-api)
- [Exemplos de Uso](#exemplos-de-uso)
- [Estrutura do Banco de Dados](#estrutura-do-banco-de-dados)
- [Variáveis de Ambiente](#variáveis-de-ambiente)

---

## 🎯 Sobre

API RESTful para gerenciar licenças de software, permitindo:
- ✅ Validação de licenças por chave única
- 🔒 Controle de ativações por hardware (UUID + Disk Serial)
- ⏰ Gerenciamento de datas de expiração
- 📊 Limite configurável de ativações simultâneas
- 🗑️ Desativação de licenças por hardware

---

## ⚡ Funcionalidades

- **Validação de Licenças**: Verifica se uma licença é válida para um hardware específico
- **Controle de Ativações**: Limita quantos dispositivos podem usar a mesma licença
- **Gestão de Expiração**: Suporte a licenças temporárias ou vitalícias
- **CRUD Completo**: Criar, consultar, desativar licenças
- **Health Check**: Monitoramento do status da API e banco de dados

---

## 🛠️ Tecnologias

- **Python 3.8+**
- **Flask 3.0** - Framework web
- **PostgreSQL** (Neon) - Banco de dados serverless
- **psycopg2** - Driver PostgreSQL
- **Vercel** - Hospedagem serverless

---

## 🚀 Deploy

### 1. Fork este repositório

### 2. Criar banco de dados Neon
1. Acesse [Neon](https://neon.tech)
2. Crie uma conta gratuita
3. Crie um novo projeto
4. Copie a **Connection String**

### 3. Deploy na Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/AtendUP/License)

1. Clique no botão acima
2. Conecte seu GitHub
3. Configure a variável de ambiente:
   - `POSTGRES_URL`: Cole a connection string do Neon

### 4. Inicializar banco de dados

Após o deploy, acesse:
```
https://seu-projeto.vercel.app/setup
```

Isso criará as tabelas e inserirá dados de exemplo.

---

## 📡 Endpoints da API

### **GET** `/`
Informações da API

**Resposta:**
```json
{
  "service": "License Server API",
  "version": "1.0.0",
  "status": "online",
  "endpoints": { ... }
}
```

---

### **GET** `/health`
Health check do servidor e banco de dados

**Resposta:**
```json
{
  "status": "healthy",
  "service": "License Server",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-11-16T00:00:00"
}
```

---

### **GET** `/setup`
⚠️ **Executar apenas uma vez** - Cria tabelas e dados de exemplo

**Resposta:**
```json
{
  "success": true,
  "message": "Banco de dados configurado com sucesso!"
}
```

---

### **GET** `/api/licenca`
Validar e ativar licença

**Parâmetros Query:**
- `key` (obrigatório): Chave da licença
- `uuid` (obrigatório): UUID único do hardware
- `disk` (obrigatório): Serial do disco

**Exemplo:**
```
GET /api/licenca?key=DEMO-1234-5678-ABCD&uuid=550e8400-e29b&disk=WD-12345
```

**Resposta (Sucesso):**
```json
{
  "valid": true,
  "message": "Licença ativada com sucesso!",
  "owner": "Cliente Teste",
  "expires": "2025-12-31",
  "activations_used": 1,
  "activations_max": 1
}
```

**Resposta (Erro - Expirada):**
```json
{
  "valid": false,
  "message": "Licença expirada em 2020-01-01"
}
```

---

### **POST** `/api/licenca/add`
Adicionar nova licença

**Body JSON:**
```json
{
  "license_key": "NOVA-2025-LICENCA-XYZ",
  "owner": "João Silva",
  "email": "joao@empresa.com",
  "expires_on": "2026-12-31",
  "max_activations": 5,
  "is_active": true
}
```

**Campos:**
- ✅ **Obrigatórios**: `license_key`, `owner`, `email`
- ⚙️ **Opcionais**: `expires_on`, `max_activations` (padrão: 1), `is_active` (padrão: true)

**Resposta:**
```json
{
  "success": true,
  "message": "Licença criada com sucesso!",
  "license": {
    "id": 4,
    "license_key": "NOVA-2025-LICENCA-XYZ",
    "owner": "João Silva",
    "email": "joao@empresa.com",
    "expires_on": "2026-12-31",
    "max_activations": 5,
    "is_active": true,
    "created_at": "2025-11-16T00:00:00"
  }
}
```

---

### **GET** `/api/licenca/info`
Obter informações detalhadas de uma licença

**Parâmetros Query:**
- `key` (obrigatório): Chave da licença

**Exemplo:**
```
GET /api/licenca/info?key=DEMO-1234-5678-ABCD
```

**Resposta:**
```json
{
  "found": true,
  "active": true,
  "owner": "Cliente Teste",
  "email": "teste@email.com",
  "expires": "2025-12-31",
  "activations_used": 1,
  "activations_max": 1,
  "created_at": "2025-11-16T00:00:00"
}
```

---

### **POST** `/api/licenca/deactivate`
Desativar licença de um hardware específico

**Body JSON:**
```json
{
  "key": "DEMO-1234-5678-ABCD",
  "uuid": "550e8400-e29b-41d4-a716",
  "disk": "WD-WCAV12345678"
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Licença desativada deste hardware"
}
```

---

## 💡 Exemplos de Uso

### cURL

**Validar licença:**
```bash
curl "https://seu-projeto.vercel.app/api/licenca?key=DEMO-1234-5678-ABCD&uuid=test-uuid&disk=test-disk"
```

**Adicionar licença:**
```bash
curl -X POST https://seu-projeto.vercel.app/api/licenca/add \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "NOVA-LICENCA-2025",
    "owner": "Cliente Novo",
    "email": "cliente@email.com",
    "max_activations": 3
  }'
```

**Desativar licença:**
```bash
curl -X POST https://seu-projeto.vercel.app/api/licenca/deactivate \
  -H "Content-Type: application/json" \
  -d '{
    "key": "DEMO-1234-5678-ABCD",
    "uuid": "test-uuid",
    "disk": "test-disk"
  }'
```

### Python

```python
import requests

# Validar licença
response = requests.get(
    "https://seu-projeto.vercel.app/api/licenca",
    params={
        "key": "DEMO-1234-5678-ABCD",
        "uuid": "hardware-uuid-123",
        "disk": "disk-serial-456"
    }
)
print(response.json())

# Adicionar licença
response = requests.post(
    "https://seu-projeto.vercel.app/api/licenca/add",
    json={
        "license_key": "NOVA-LICENCA",
        "owner": "João Silva",
        "email": "joao@email.com",
        "max_activations": 5
    }
)
print(response.json())
```

---

## 🗄️ Estrutura do Banco de Dados

### Tabela: `licenses`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | SERIAL | ID único (auto-incremento) |
| `license_key` | VARCHAR(255) | Chave da licença (única) |
| `owner` | VARCHAR(255) | Nome do proprietário |
| `email` | VARCHAR(255) | Email do proprietário |
| `expires_on` | DATE | Data de expiração (NULL = vitalícia) |
| `max_activations` | INTEGER | Máximo de ativações simultâneas |
| `is_active` | BOOLEAN | Status ativo/inativo |
| `created_at` | TIMESTAMP | Data de criação |

### Tabela: `activations`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | SERIAL | ID único (auto-incremento) |
| `license_id` | INTEGER | FK para `licenses.id` |
| `hardware_signature` | VARCHAR(255) | Assinatura do hardware (uuid_disk) |
| `activated_at` | TIMESTAMP | Data da ativação |

**Constraint**: `UNIQUE (license_id, hardware_signature)` - Evita duplicatas

---

## 🔐 Variáveis de Ambiente

Configure na Vercel (Settings > Environment Variables):

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `POSTGRES_URL` | Connection string do PostgreSQL | `postgresql://user:pass@host/db?sslmode=require` |

---

## 📦 Estrutura do Projeto

```
License/
├── api/
│   └── index.py          # Código principal da API
├── requirements.txt      # Dependências Python
├── vercel.json          # Configuração Vercel
└── README.md            # Este arquivo
```

---

## 🧪 Dados de Teste

Após executar `/setup`, estarão disponíveis:

| Chave | Owner | Expiração | Max Ativações |
|-------|-------|-----------|---------------|
| `DEMO-1234-5678-ABCD` | Cliente Teste | 2025-12-31 | 1 |
| `PROD-9876-5432-ZYXW` | Cliente Premium | 2026-12-31 | 3 |
| `EXPIRED-LITE-LICENSE` | Cliente Expirado | 2020-01-01 | 1 |

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👤 Autor

**AtendUP**
- GitHub: [@AtendUP](https://github.com/AtendUP)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma issue ou enviar um pull request.

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📞 Suporte

Se você tiver alguma dúvida ou problema, abra uma [issue](https://github.com/AtendUP/License/issues).

---

<div align="center">

**⭐ Se este projeto foi útil, deixe uma estrela!**

Feito com ❤️ por [AtendUP](https://github.com/AtendUP)

</div>
