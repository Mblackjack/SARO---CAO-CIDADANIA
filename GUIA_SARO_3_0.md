# 📘 Guia de Configuração - SARO 3.0 (MPRJ)

O **SARO 3.0** agora integra a inteligência da **OpenAI** com a atualização automática de planilhas no **SharePoint**. Para que o sistema funcione corretamente, você precisa configurar as credenciais no painel do Streamlit Cloud.

---

## 1. Configuração dos Secrets (Streamlit Cloud)

No painel do seu aplicativo no Streamlit Cloud, vá em **Settings > Secrets** e cole o seguinte modelo, preenchendo com seus dados:

```toml
# Chave da OpenAI
OPENAI_API_KEY = "sua-chave-sk-..."

# Credenciais Institucionais do MPRJ (Para o SharePoint)
SHAREPOINT_USER = "seu-email@mprj.mp.br"
SHAREPOINT_PASSWORD = "sua-senha-ou-senha-de-app"
```

---

## 2. Atenção: Autenticação de Dois Fatores (MFA)

Se o MPRJ exige que você confirme o login pelo celular (Microsoft Authenticator), você **não deve** usar sua senha normal no campo `SHAREPOINT_PASSWORD`. 

**Siga estes passos para gerar uma "Senha de Aplicativo":**
1. Acesse [mysignins.microsoft.com/security-info](https://mysignins.microsoft.com/security-info).
2. Clique em **+ Adicionar método** e escolha **Senha de aplicativo**.
3. Dê o nome de "SARO" e copie a senha gerada.
4. Use essa senha gerada no campo `SHAREPOINT_PASSWORD` dos Secrets.

---

## 3. Estrutura da Planilha
O sistema espera encontrar a planilha no seguinte caminho:
`CAO Consumidor Equipe > Documentos > General > Tabela_SARO.xlsx`

Se o nome do arquivo ou a pasta for diferente, me avise para que eu possa ajustar o código!

---

## 4. Dependências
Certifique-se de que o arquivo `requirements.txt` contenha:
```text
streamlit
openai
pandas
openpyxl
Office365-REST-Python-Client
xlsxwriter
```
