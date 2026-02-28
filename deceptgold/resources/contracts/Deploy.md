### 1. **Configuração Inicial no Remix**
- Acesse o [Remix IDE](https://remix.ethereum.org/).
- Crie dois arquivos:
  - `DeceptGoldToken.sol` (cole o código do primeiro contrato).
  - `ValidatorContract.sol` (cole o código do segundo contrato).
- Certifique-se de que o Remix está configurado para a versão correta do compilador Solidity (selecione `^0.8.20` no menu "Compiler").

### 2. **Compilar os Contratos**
- No menu lateral, vá para a aba **Solidity Compiler**.
- Clique em **Compile DeceptGoldToken.sol**. Isso também compilará automaticamente o `ValidatorContract.sol`, já que ele importa o primeiro contrato.
- Verifique se não há erros de compilação.

### 3. **Deploy do Contrato `DeceptGoldToken`**
- Vá para a aba **Deploy & Run Transactions** no Remix.
- Escolha o ambiente (ex.: **Injected Provider - MetaMask** para conectar à sua carteira, como MetaMask, ou use **Remix VM** para testes).
- No campo **Contract**, selecione `DeceptGoldToken`.
- No campo `Constructor`, insira o endereço do **initialOwner** (geralmente o endereço da sua carteira, ex.: `0xYourAddress`).
- Clique em **Deploy** e confirme a transação na MetaMask (se estiver usando).
- Após o deploy, copie o endereço do contrato `DeceptGoldToken` que aparece na seção "Deployed Contracts".

### 4. **Configurar o `ValidatorContract` no `DeceptGoldToken`**
- No Remix, na seção "Deployed Contracts", localize o contrato `DeceptGoldToken` que você acabou de implantar.
- Chame a função `setValidatorContract`:
  - Insira o endereço do contrato `ValidatorContract` (você ainda não o implantou, então faremos isso no próximo passo).
  - Por enquanto, anote que você precisará chamar essa função após o deploy do `ValidatorContract`.

### 5. **Deploy do Contrato `ValidatorContract`**
- Na aba **Deploy & Run Transactions**, selecione `ValidatorContract` no campo **Contract**.
- No campo `Constructor`, insira o endereço do contrato `DeceptGoldToken` (copiado no passo 3).
- Clique em **Deploy** e confirme a transação na MetaMask.
- Após o deploy, copie o endereço do contrato `ValidatorContract` que aparece na seção "Deployed Contracts".

### 6. **Associar o `ValidatorContract` ao `DeceptGoldToken`**
- Volte ao contrato `DeceptGoldToken` na seção "Deployed Contracts".
- Chame a função `setValidatorContract`:
  - Insira o endereço do `ValidatorContract` (copiado no passo 5).
  - Confirme a transação na MetaMask.

### 7. **Testar a Função `claimToken`**
- No contrato `ValidatorContract`, na seção "Deployed Contracts", chame a função `claimToken`:
  - **jsonHash**: Insira o hash (ex.: `0xYourHash`).
  - **signature**: Insira a assinatura gerada off-chain (deve ser compatível com o `EXPECTED_SIGNER`).
  - **recipient**: Insira o endereço que receberá o token (ex.: `0xRecipientAddress`).
- Confirme a transação. O contrato verificará a assinatura e, se válida, chamará `mint` no `DeceptGoldToken` para criar 1 token.

### Dicas Finais
- **Teste na Rede de Testes**: Antes de implantar em uma rede principal (como Ethereum Mainnet), teste em uma rede de teste (ex.: Sepolia ou Goerli) para evitar custos altos.
- **Assinatura**: A assinatura deve ser gerada off-chain usando a chave privada associada ao `EXPECTED_SIGNER` (0xfA6a145a7e1eF7367888A39CBf68269625C489D2). Use ferramentas como `ethers.js` ou `web3.js` para criar e verificar a assinatura.
- **MetaMask**: Certifique-se de que sua MetaMask está conectada à rede correta e tem saldo suficiente para pagar as taxas de gás.
- **Ordem de Deploy**: Sempre implante `DeceptGoldToken` primeiro, pois `ValidatorContract` depende dele.