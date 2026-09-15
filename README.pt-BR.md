<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.es.md">Español</a> ·
  <strong>Português (Brasil)</strong>
</p>

<p align="center">
  <img src="docs/assets/cyberdeck.svg" alt="Cyberdeck Edge 30 Ultra — Droidian e Plasma Mobile 6. Ilustração do conceito." width="100%">
</p>

# Cyberdeck Edge 30 Ultra

**De celular a estação de trabalho de bolso.** Um port de **Droidian + Plasma Mobile 6**
para o Motorola Edge 30 Ultra (`eqs`): Linux nativo, terminal, aplicativos de
desktop e ferramentas de desenvolvimento em um dispositivo de bolso.

<p align="center">
  <a href="#estado">Estado</a> ·
  <a href="#arquitetura">Arquitetura</a> ·
  <a href="#compilar-e-instalar">Compilar e instalar</a> ·
  <a href="#documentação">Documentação</a> ·
  <a href="#como-contribuir">Como contribuir</a>
</p>

> [!IMPORTANT]
> **O celular já inicializa e executa o Plasma. O port continua experimental.**
> A validação corresponde a uma unidade **XT2241-2 RETAR de 256 GB**.
> Não é uma ROM oficial nem uma imagem universal pronta para instalar:
> há recursos pendentes, a compilação exige artefatos binários locais e
> a instalação limpa ainda precisa de validação física.

## Por que ele existe

- **Terminal e redes:** SSH, tmux, Git, edição e diagnóstico de sistemas.
- **Desenvolvimento de bolso:** shell personalizada, editores, ferramentas CLI
  e ambientes científicos ARM64.
- **Desktop sensível ao toque:** Plasma Mobile com rotação bloqueável na horizontal,
  janelas maximizadas e controle manual do teclado na tela.

A tela interna é o único monitor. O USB-C fica reservado para periféricos,
dados e alimentação; monitores externos e Motorola Ready For estão fora do escopo.

## Estado

**Base documentada: 11 de setembro de 2026.**
Kernel **H29**, Plasma Mobile **6.3.3 +eqs5**, Wayfire/HWC, libhybris, Maliit e
XWayland. Firmware base Android 14: `U1SQS34.52-21-1-16`. O bootloader permanece desbloqueado.

**15 de setembro — desktop Plasma 6.7.5 em execução:** Mobile/Workspace
adaptados, Qt 6.10.2 GLES e Frameworks 6.28 passaram nas verificações nativas
dos pacotes, preservando H29 e Wayfire/HWC. Após corrigir o QScreen, uma nova
inicialização e uma captura desbloqueada confirmam o desktop horizontal, escala
200% e data em espanhol. A ocultação dos painéis está ativada: Eduardo confirmou
que as barras se ocultam, reaparecem ao deslizar pelas bordas e Início/Recentes
funcionam. Falta completar a matriz de uso; a receita da imagem continua em
**6.3.3 +eqs5**.
[Evidências e pendências](port/plasma-mobile-wf/UPGRADE-6.7.md).

| Área | Evidências e limitações |
| :--- | :--- |
| 🟢 Inicialização nativa | Droidian, systemd como PID 1 e raiz UFS/LVM verificados; conjunto de inicialização H29 recuperável. |
| 🟢 Plasma e navegação | Início, Recentes, Fechar e gestos adaptados ao Wayfire; melhoria de uso confirmada. |
| 🟢 Desktop | Escala de 200%, quatro áreas de trabalho, maximização genérica e prazo de redimensionamento de 1000 ms para Ghostty e outros clientes lentos. |
| 🟢 Rotação e bloqueio | Preserva a horizontal em 90°/270°; o fundo da tela de bloqueio acompanha o desktop. Datas e textos de bloqueio localizados com `+eqs5`. |
| 🟢 Wi-Fi e SSH | Acesso nativo utilizado para instalar e verificar o sistema. Isso não equivale a um teste de autonomia de oito horas. |
| 🟢 Armazenamento | `/` e `/home` compartilham um sistema ext4 de **224,52 GiB**; expansão e reinicialização verificadas sem alterar GPT/PV/LV. |
| 🟡 Tela de toque substituída | Calibração libinput 2× confirmada **somente para a tela de reposição desta unidade**; não aplicar a todos os `eqs`. |
| 🟡 Teclado na tela | O botão **Teclado táctil** e `osk on/off` funcionam; o controle é manual, sem detecção automática do teclado USB. |
| 🟡 Áudio e câmeras | Módulos/política stock corrigidos; câmera principal e frontal geram prévias. Correção horizontal instalada; confirmação visual, fotos salvas, câmeras auxiliares e qualidade máxima continuam pendentes. |
| 🟡 Bluetooth | Inicialização e busca após reiniciar verificadas; os perfis não foram validados exaustivamente. |
| 🟡 Hub USB-C | Hub e receptor RF funcionam com PD. **Uma nova conexão sem alimentação externa ainda falha**; uma troca de função permitiu manter uma conexão já estabelecida. |
| 🟡 GPU nos aplicativos | Wayfire usa a Adreno 730. As configurações habituais de Ghostty/Zed usam renderização por software; o teste isolado do Zed acelerado ainda não foi integrado. |
| 🔴 Imagem diária criptografada | Pendente. A preview não tem LUKS e não deve ser tratada como um dispositivo de trabalho com segurança reforçada. |

🟢 Verificado na unidade de teste · 🟡 Parcial ou condicionado · 🔴 Pendente

## Arquitetura

**Droidian inicializa nativamente; não é um chroot nem um desktop remoto.**
A integração gráfica reutiliza os serviços e drivers Android do dispositivo:

```text
               Plasma Mobile 6
                      │
                 Wayfire / HWC
                      │
        Halium · libhybris · Android em LXC
                      │
       Kernel eqs H29 + firmware Motorola
                      │
         Snapdragon 8+ Gen 1 · Adreno 730
```

KWin não atua como compositor, e Phosh não faz parte da experiência desejada.
Waydroid é uma adição **opcional para aplicativos Android**, separada
do contêiner usado pelo Halium na integração do hardware.

## Compilar e instalar

### Primeiro: código, celular e imagem são coisas diferentes

| Artefato | Situação |
| :--- | :--- |
| Celular de desenvolvimento | H29 + Plasma `+eqs5`, correções instaladas e evidências nativas documentadas. |
| Receita deste repositório | Fixa o pacote `+eqs5`; exige **22 artefatos locais de entrada** com hashes SHA-256. |
| ZIP gerado em 10 de setembro | Preview de 1,76 GiB com `+eqs4`; inspecionada no host, **não validada como instalação limpa no celular**. |
| Novo ZIP com `+eqs5` | **Ainda não foi gerado.** Este repositório não oferece download público de binários. |

A imagem é construída a partir de uma **base limpa**, nunca exportando a raiz em uso,
`/home`, contas ou credenciais do celular. O ZIP de 1º de setembro é
histórico e **não representa o port atual**.

```sh
git clone https://github.com/eduardojvieira/cyberdeck-edge-30.git
cd cyberdeck-edge-30

# Somente depois de preparar Docker, binfmt ARM64 e os artefatos locais.
# O caminho de saída não deve existir. Este comando não faz flash no celular.
port/build-eqs-rootfs.sh --consolidated "$PWD/.work/eqs-image-new" stock
```

- **Tela original:** perfil `stock`. **Tela de reposição calibrada da unidade
  de desenvolvimento:** `replacement`. O nome Goodix não permite diferenciá-las.
- A geometria atual corresponde à unidade de **256 GB**, não a um layout menor.
- O builder preserva o **binário H29 testado**; recompilar outro kernel
  com o mesmo `uname -r` não demonstra equivalência.
- Builders/flashers históricos não reproduzem o sistema atual. Não usar
  `--historical` como atalho de instalação.

**Leia antes de começar:** [artefatos e compilação](port/image/README.md) ·
[release, hashes e evidências](docs/RELEASE-20260910.md) ·
[instalação e recuperação](port/image/INSTALL.md).

> [!WARNING]
> A instalação limpa **destrói `userdata`**. Prepare uma recuperação testada,
> confira a variante e o firmware e use um cabo direto: **nunca faça flash por
> um hub USB-C nem bloqueie novamente o bootloader com uma imagem modificada**.
> O slot B não é um backup. Uma falha gráfica não se diagnostica apagando dados.
> A preview usa um PIN padrão: troque-o antes de conectar a qualquer rede.

## Software instalado no celular

| Categoria | Ferramentas e documentação |
|---|---|
| Terminal | Fish/Starship, fzf, zoxide, Neovim, Ghostty 1.3.1 e Hollywood/tmux isolado. [Shell](port/shell/README.md). |
| Desenvolvimento | Homebrew ARM64, mise, uv, GitHub CLI, Brew Browser como única GUI do Brew; GitUI, Lazygit, Yazi, ncdu, Mosh e Restic. |
| Editores/agentes | VS Code, Antigravity/CLI, Zed, Herdr, Codex e Pi com configuração portátil; sem copiar armazenamentos de credenciais, logins remotos pendentes. |
| Ciência | Octave 11.3, wxMaxima 26.08/Maxima 5.50, Python científico, SageMath, Spyder, JupyterLab e Scilab **2026.1** ARM64. O Scilab 2024 do APT foi removido e o 2026 revalidado. [Ciência](port/shell/SCIENCE.md). |
| Escritório | ONLYOFFICE 9.4 ARM64 com o repositório oficial limitado a esse aplicativo. [Escritório](port/shell/OFFICE.md). |
| Android (11–12 de setembro) | Waydroid + Android 13 GAPPS/Google Play instalados sem flash; inicialização do Android, rede e abertura pelo KDE verificadas. Atalho da Play Store habilitado no Plasma; login do usuário pendente. Integração experimental, não incluída no ZIP limpo. [Uso, ajustes e limitações](port/waydroid/README.md). |

Essas ferramentas estão no celular; a imagem base não clona Homebrew,
ambientes grandes, contas nem configurações privadas. Launchers, versões,
testes e manutenção estão documentados para reinstalação seletiva.

## Idioma e desempenho

<details>
<summary><strong>Espanhol da Argentina, incluindo a tela de bloqueio</strong></summary>

O sistema e os formatos do Plasma estão configurados em **`es_AR.UTF-8`**, com
`LANGUAGE=es_AR:es`. Foram instalados `chromium-l10n`, `firefox-l10n-es-ar`,
`qt6-translations-l10n`, `qttranslations5-l10n`, `hunspell-es` e o pacote
oficial de espanhol do VS Code. Chromium prioriza `es-AR,es` para os sites.
O layout do teclado não foi alterado e não houve atualização da distribuição.

Waydroid reiniciou com a configuração efetiva `es-rAR`; seus launchers
também foram traduzidos. Novo login SSH e ambiente de ativação do KDE verificados.
Após reiniciar, o Plasma já tinha `es_AR`, mas seus relógios ainda formatavam
datas em inglês e a tela de bloqueio continha textos sem tradução. Instalado
[`+eqs5`](port/plasma-mobile-wf/README.md#date-and-lockscreen-language-september-11):
15 casos nativos passam lendo os recursos compilados, e o catálogo espanhol
contém “Contraseña”, “Cargando” e “Descargando”.
**Ativo após recarregar somente o Plasma com o celular desbloqueado**: verificados
visualmente “viernes, 11 de septiembre de 2026” e “Descargando” na tela de bloqueio.
Wayfire e a sessão de inicialização não mudaram. A barra passa no teste nativo;
a captura após desbloquear continua pendente. Scilab agora tem um
[catálogo espanhol parcial](port/shell/SCIENCE.md#traducción-española-11-de-septiembre).
Esses ajustes estão no **celular**, não no ZIP de 10 de setembro.
Backups privados: `/var/lib/eqs-locale-20260911/` e
`~/.cache/eqs-locale-20260911/` no Edge.
O pacote anterior e o log de instalação do `+eqs5` estão em
`/var/lib/eqs-locale-clock-20260911/`.

</details>

<details>
<summary><strong>Geekbench 7 CPU — resultado público e condições do teste</strong></summary>

**Geekbench 7.0.0 Preview para Linux/AArch64**, executado nativamente no
Droidian H29, concluiu o teste e enviou o
[resultado público 322037](https://browser.geekbench.com/v7/cpu/322037)
com autorização de Eduardo. Saída `0`; tempo total, incluindo o envio:
**6 min 47 s**. Celular carregando, governador `walt`, sem mudanças nas frequências
nem nas proteções térmicas. É uma execução, não uma média nem um teste de GPU.

A enumeração OpenCL pelo libhybris fazia até `--help` falhar; ela foi evitada
somente para esse processo com `OCL_ICD_VENDORS` apontando para uma pasta vazia.
O ICD do sistema não foi alterado. Logs privados em
`~/.cache/eqs-geekbench7-20260911/` no Edge; **não publique o link de claim**.
O visualizador público retornou HTTP 403 às ferramentas de leitura, então
não foram transcritas pontuações sem verificação. Não comparar com Geekbench 6.

</details>

## Atualizações sem regravar a imagem

O celular e a receita consolidada usam `Acquire::Droidian::Version "current";`.
`101.20251130` identifica a base de compilação, não uma exigência permanente.

```sh
sudo apt update
apt-mark showhold
sudo apt -s upgrade
```

Revise assinaturas, downgrades e mudanças de Qt/Plasma/Halium antes de aplicar.
Não misture Sid, não remova holds sem revisão nem automatize `full-upgrade`. O PackageKit
já substituiu o Plasma corrigido pelo upstream por causa da prioridade 1002: o hold importa.
A imagem protege Plasma/kernel e desabilita gravações de boot por triggers
com `FLASH_BOOTIMAGE=no`; isso não garante que toda atualização seja segura.
O launcher da câmera volta ao Qt do sistema se sua versão mudar e exige recompilação.
[Detalhes de manutenção](docs/HISTORY-20260910.md#mantenimiento-apt-de-h29).

## Documentação

O README de referência é [a versão em inglês](README.md). Os guias técnicos
vinculados mantêm seu idioma original; estas traduções cobrem a apresentação do projeto.

| Se você quer… | Comece por… |
| :--- | :--- |
| Entender como chegamos à inicialização nativa | [Plano de bring-up](docs/BRINGUP-PLAN.md) e [histórico do port](docs/HISTORY-20260910.md) |
| Compilar, inspecionar ou recuperar uma imagem | [Builder](port/image/README.md), [instalação](port/image/INSTALL.md), [recuperação](docs/RECOVERY.md) e [release de 10/9](docs/RELEASE-20260910.md) |
| Trabalhar no desktop | [Patches Plasma/Wayfire](port/plasma-mobile-wf/README.md) |
| Investigar um periférico | [Bluetooth](docs/BLUETOOTH.md), [GPU](docs/GPU.md), [áudio/câmera H27–H28](docs/H27-NAVIGATION-AUDIO-CAMERA.md) e [USB/H29](docs/H29-CAMERA-ROTATION-BROWSER.md) |
| Revisar a prévia da câmera | [Override Qt5 isolado](port/qt5-wayland/README.md) |
| Reinstalar ferramentas | [Shell](port/shell/README.md), [ciência](port/shell/SCIENCE.md), [escritório](port/shell/OFFICE.md) e [Waydroid](port/waydroid/README.md) |
| Comparar fontes e dispositivos | [Referências fixadas](reference/README.md) |

## Próximos passos

- [ ] Gerar o ZIP `+eqs5` e validar fisicamente a instalação limpa e sua recuperação.
- [ ] Conectar hub e teclado sem PD do zero, sem comandos manuais.
- [ ] Confirmar prévias na horizontal, fotos salvas e câmeras auxiliares.
- [ ] Integrar GPU nos aplicativos que hoje usam llvmpipe.
- [ ] Completar testes de áudio, perfis Bluetooth, suspensão, hotplug, temperatura e autonomia.
- [ ] Produzir uma imagem diária LUKS com provisionamento seguro e atualizações gráficas testadas.
- [ ] Recompilar todos os artefatos binários de entrada a partir de um clone novo.

## Como contribuir

As contribuições mais úteis são pequenas: **uma falha reproduzível, um log sem
dados sensíveis, um patch focado e um teste que demonstre o que mudou**.

Ao relatar um problema, informe variante, firmware, perfil de tela,
versão Plasma/kernel e última etapa verificada. Sempre separe testes no host de
testes reais no celular. Não anexe IMEI, número de série, chaves, tokens, redes salvas
nem imagens do seu sistema pessoal.

<details>
<summary><strong>Verificações rápidas no PC — sem celular nem sudo</strong></summary>

```sh
python3 port/image/test-image.py
python3 port/kernel/test-eqs-config.py
python3 port/kernel/test-module-inventory.py
python3 port/test-bluetooth-address.py
python3 port/qt5-wayland/test-launcher.py
python3 port/shell/test-osk.py
python3 port/shell/test-hollywood.py
python3 port/shell/test-science.py
git diff --check
```

Os testes de regressão C++/initramfs precisam das fontes fixadas: veja sua documentação.
**Não execute todos os testes indiscriminadamente.** `test-wallpaper-sync.py`
e `port/waydroid/check-prepare.py` são verificações nativas do Edge;
o segundo prepara dispositivos e exige autorização para atuar no celular.

</details>

Traduções para outros idiomas são bem-vindas. Parta de `README.md`, adicione
`README.<idioma>.md` e atualize o seletor em todas as versões. Preserve
os mesmos avisos, versões, comandos e estado de validação.

### Créditos

Este trabalho se apoia em **Droidian, KDE/Plasma Mobile, Wayfire, Halium,
libhybris, LineageOS, AOSP e nos mantenedores do `eqs-development`**. Os ports
do ThinkPhone/Bronco forneceram referências, não binários intercambiáveis com `eqs`.
Fontes e commits de referência: [inventário](reference/README.md).

Port comunitário e independente, sem afiliação oficial com Motorola, Droidian
ou KDE. São preservados os avisos e as licenças de cada componente; não se declara
uma licença única para toda a árvore. Firmware proprietário, binários de compilação,
logs e backups permanecem fora do Git.

---

<p align="center"><strong>Um celular que não se contenta em ser só um celular.</strong></p>
