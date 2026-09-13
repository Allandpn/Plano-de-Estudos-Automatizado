# Triagem do Bloco: Infraestrutura, Redes e Cloud + Segurança da Informação (Trilha 3)
### SEFAZ SC 2026 — resultado da triagem de PDFs, complementa mapa-assuntos-edital-sefaz-sc.md e cronograma-detalhado-sessoes-sefaz-sc.md
*Gerado em 12/09/2026, com o índice completo (2639 PDFs). Fecha a Trilha 3 inteira.*

Todos os caminhos abaixo são relativos a `apostilas/`.

## Acervo identificado

**Achado principal: `05-TCE-SC 2026 - Pos Edital`** — o mesmo curso pós-edital de TCE-SC
(Santa Catarina, perfil de auditor de controle externo em TI muito próximo do nosso) já usado
em blocos anteriores (Anomalias, DevOps, DAMA) tem duas subpastas dedicadas inteiras a este
bloco:

1. **`06-Redes e Segurança`** (18 aulas, prof. André Castro) — cobre Equipamentos de
   Rede+OSI+TCP/IP (Aula 01), IPv4 (Aula 04), NAT/PAT+IPv6 (Aula 05), HTTP (Aula 07), DNS
   (Aula 08), Princípios de Segurança+Autenticação (Aula 09), Firewall/Proxy/IDS/IPS/WAF
   (Aula 10), SSL/TLS (Aula 11), Criptografia (Aula 12), Assinatura Digital (Aula 13),
   ISO 27001/27002 — inclui mascaramento/pseudonimização/anonimização (Aula 14), ISO 27005 e
   Gestão de Riscos (Aula 15), Plano de Continuidade de Negócio (Aula 16).
2. **`07-Sistemas Operacionais`** (9 aulas, prof. Evandro Dalla Vecchia) — Virtualização e
   Hypervisor (Aula 04), Computação em Nuvem (Aula 05, inclui Azure AD).

**Complemento pra Docker/Kubernetes** (não encontrados de forma dedicada no curso acima —
lá aparecem só como questão de múltipla escolha, não como teoria própria):
`00-Curso Regular\05-Desenvolvimento de Software para Concursos`, Aula 09 — mesma família já
usada nos blocos Programação/Anomalias/Engenharia de Software, com Docker e Kubernetes como
seções dedicadas (105 pág. de Teoria) além de DevOps (redundante com o já visto no bloco
Engenharia de Software).

**Formato do curso principal**: cada aula é Teoria única e extensa seguida de Questões
Comentadas **separadas por banca** (Cebraspe, FCC, FGV, Cesgranrio) — sem Resumo condensado na
maioria (só a Aula 01 tem um resumo, mas é curto demais pra substituir a Teoria). Volume real
de Teoria por aula varia de ~3 a ~55 páginas — **nada perto do drama de páginas dos bancos de
questões** (que somam centenas de páginas cada aula, não lidos aqui).

## Decisão da Etapa 0 — descartes

- **Sistemas Operacionais, Aulas 00-03 (Windows Server, Linux administração)**: comandos
  específicos de administração de SO não são assunto fino deste edital (que pede só
  "servidores, SOs" em nível conceitual) — não ler em detalhe, usar só como contexto.
- **Sistemas Operacionais, Aulas 06-08 (Computação Forense, Post Mortem Forensics, Engenharia
  Reversa)**: perícia digital não é citada no edital — fora de escopo.
- **Redes e Segurança, Aula 17 (CGI)**: tecnologia web datada, não citada no edital.
- **Redes e Segurança, Aula 01/07 (partes de Correio Eletrônico dentro da Aula 07)**: SMTP/POP/
  IMAP não são citados no edital (só HTTP/HTTPS) — não ler.
- **Curso Desenvolvimento de Software, Aula 09 (Artifactory/Jenkins/OpenShift/Rancher/Puppet)**:
  ferramentas de CI/CD adicionais não citadas no edital (que só pede Git/CI-CD/DevOps
  genericamente, já visto no bloco Engenharia de Software) — só Docker e Kubernetes lidos aqui.
- **Teoria completa de cada sub-tópico não é lida 100%** em vários pontos (ver tabela de
  páginas na Etapa 1) — o volume real de Teoria de alguns tópicos (Modelo OSI, IPv4, DNS, HTTP,
  Autenticação, ISO 27001/27002, ISO 27005) passa de 20-100 páginas cada; **cortado no núcleo
  conceitual** (definições, comparações, tabelas — o que bancas mais cobram), com o restante
  como banco de reserva pra quem quiser aprofundar.

## Gap confirmado

Nenhum ❌. Quatro 🟡 reais — sub-itens específicos dentro de linhas do edital que combinam
muitos conceitos, sem fonte dedicada encontrada pra essa fração específica:

| Assunto (mapa-assuntos) | Status | Observação |
|---|---|---|
| Servidores, SOs, virtualização, armazenamento, contêineres, alta disponibilidade, balanceamento | ✅ | Virtualização/Hypervisor ✅; alta disponibilidade/balanceamento aparecem dentro da própria Teoria de Virtualização |
| Redes: OSI/TCP-IP, IPv4/IPv6, TCP/UDP, DNS/DHCP, HTTP/HTTPS, LAN/WAN/WLAN/VLAN, NAT, VPN, roteamento, switching | 🟡 | OSI/TCP-IP/IPv4/IPv6/NAT/DNS/HTTP ✅ com fonte dedicada; **DHCP, VLAN e roteamento (protocolos) só aparecem como distratores de questão, sem teoria própria** — complementar com IA |
| Cloud: IaaS/PaaS/SaaS, pública/privada/híbrida, elasticidade, serverless, responsabilidade compartilhada; AWS/Azure/GCP | ✅ | Completo (a fonte foca mais em Azure — se sobrar tempo, checar exemplos equivalentes de AWS/GCP via IA) |
| Docker e Kubernetes | ✅ | Completo, fonte diferente da SO (curso Desenvolvimento de Software) |
| CIA, autenticidade, não repúdio; ameaças, vulnerabilidades, riscos, controles | ✅ | Completo (Princípios de Segurança + ISO 27001/27002 + ISO 27005) |
| IAM, MFA, RBAC; segurança de redes/sistemas/BD/APIs/apps/endpoints/pipelines/cloud | ✅ | Completo (Segurança Física/Lógica/Controle de Acesso + Autenticação) |
| Firewalls, IDS/IPS, WAF; hardening, gestão de vulnerabilidades/patches | ✅ | Completo (tudo dentro da mesma aula de Firewall/Proxy) |
| Logs, monitoramento, incidentes, backup, continuidade | 🟡 | Continuidade/backup (RTO/RPO) ✅; **logs e monitoramento de incidentes só encontrados num contexto específico de Linux** (não genérico) — complementar com IA |
| Criptografia simétrica/assimétrica, hashes, certificados, assinaturas, PKI, TLS, gestão de chaves | ✅ | Completo |
| LGPD aplicada a sistemas/analytics/IA; Privacy by Design, anonimização/pseudonimização/mascaramento | 🟡 | Mascaramento/pseudonimização/anonimização técnicos ✅ (dentro da Aula 14); **LGPD como lei aplicada e Privacy by Design não confirmados nesta fonte técnica** — o ângulo jurídico da LGPD já está previsto para ser visto no bloco de Direito/Gerais (ver `cronograma-detalhado-sessoes-sefaz-sc.md`, Dom 11/10) — cruzar os dois quando chegar lá |

## Etapa 1 — cronograma

**Sem mudança de dias** — os 2 dias de Infraestrutura (Seg 26/10, Ter 27/10) e os ~2,5 dias de
Segurança (Qui 29/10, Sex 30/10, parte de Dom 01/11) já orçados comportam o conteúdo, embora
os dois dias de Infraestrutura fiquem densos (~95 pág. cada, no mesmo patamar do dia mais
pesado já aceito no bloco Estatística/CD/ML). Se algum dia atrasar, o buffer de Sáb 31/10
("revisão geral da Fase 3; se atrasado, absorve pendências") já existe pra isso — não precisou
ser reatribuído preventivamente.

| Dia | Fontes | Páginas |
|---|---|---|
| Seg 26/10 | SO Aula 04 (Virtualização) + Redes Aulas 01 (Equip/OSI/TCPIP), 04 (IPv4), 08 (DNS) | ~95 pág. |
| Ter 27/10 | Redes Aulas 05 (NAT/IPv6), 07 (HTTP) + SO Aula 05 (Cloud) + Dev.Software Aula 09 (Docker/K8s) | ~93 pág. |
| Qui 29/10 | Redes Aulas 09 (Princípios/Autenticação), 14 (ISO 27001/27002, núcleo), 15 (ISO 27005) | ~90 pág. |
| Sex 30/10 | Redes Aulas 10 (Firewall/IDS/IPS/WAF), 16 (Continuidade) + SO Aula 03 (trecho de monitoramento/incidentes Linux) | ~74 pág. |
| Dom 01/11 (parte Segurança) | Redes Aulas 11 (SSL/TLS), 12 (Criptografia), 13 (Assinatura Digital), 14 (LGPD/mascaramento, trecho) | ~59 pág. |

## Etapa 2 — roteiro por dia

### Seg 26/10 — Infraestrutura: servidores, virtualização, contêineres, alta disponibilidade; redes — OSI/TCP-IP, IPv4/IPv6, DNS/DHCP
- **Leitura:**
  - `05-TCE-SC 2026 - Pos Edital\07-Sistemas Operacionais`, `aula 04.pdf`, Teoria: pág. 4-18
    (Virtualização — inclui alta disponibilidade/balanceamento) + pág. 88-90 (Tipos de
    Hypervisor).
  - `05-TCE-SC 2026 - Pos Edital\06-Redes e Segurança`, `aula 01.pdf`, Teoria: pág. 4-20
    (Equipamentos de Rede) + pág. 103-120 (Modelo de Referência ISO/OSI, núcleo) + pág. 171-177
    (Arquitetura TCP/IP).
  - Mesma família, `aula 04.pdf`, Teoria: pág. 3-20 (Protocolo IPv4, núcleo).
  - Mesma família, `aula 08.pdf`, Teoria: pág. 4-20 (DNS, núcleo).
- **Complemento via IA (gap 🟡):** DHCP, VLAN e protocolos de roteamento — sem teoria dedicada
  encontrada, só como distratores de questão.
- **Pretest:** 2-3 questões de cada fonte, mesmo chutando (posições variam, ver Questões
  Comentadas logo após cada Teoria).
- **Fixação:** 5-8 questões ao final — dia denso (95 pág.), priorizar Equipamentos de Rede e
  IPv4 (mais cobrados historicamente).
- **Banco de reserva:** Lista de Questões de cada aula, mais o restante da Teoria não lido
  (Modelo OSI pág. 120-125, DNS pág. 20-28, etc.) — volta antes do simulado #1 ou no buffer de
  Sáb 31/10.
- **Observações:** gap 🟡 de DHCP/VLAN/roteamento registrado acima.

### Ter 27/10 — Infraestrutura: cloud — IaaS/PaaS/SaaS, AWS/Azure/GCP; Docker e Kubernetes (fechamento)
- **Leitura:**
  - `05-TCE-SC 2026 - Pos Edital\06-Redes e Segurança`, `aula 05.pdf`, Teoria: pág. 4-16
    (NAT e PAT, inclui transição IPv4/IPv6 dual-stack).
  - Mesma família, `aula 07.pdf`, Teoria: pág. 3-20 (HTTP, núcleo).
  - `05-TCE-SC 2026 - Pos Edital\07-Sistemas Operacionais`, `aula 05.pdf`, Teoria completa:
    pág. 3-12 (Computação em Nuvem SO + Azure AD).
  - `00-Curso Regular\05-Desenvolvimento de Software para Concursos`, `aula 09.pdf`, Teoria:
    pág. 84-110 (Docker, núcleo) + pág. 156-180 (Kubernetes, núcleo).
- **Pretest:** 2-3 questões de cada fonte.
- **Fixação:** 5-8 questões ao final — fecha o sub-bloco de Infraestrutura.
- **Banco de reserva:** restante da Teoria (Docker pág. 110-124, Kubernetes pág. 180-206) +
  Listas de Questões — volta antes do simulado #1.
- **Observações:** a fonte de Cloud foca em Azure — exemplos equivalentes de AWS/GCP podem ser
  complementados via IA se sobrar tempo (conceitos de IaaS/PaaS/SaaS são iguais entre provedores).

### Qui 29/10 — Segurança: CIA, ameaças/vulnerabilidades, riscos, controles; IAM, MFA, RBAC
- **Leitura:** `05-TCE-SC 2026 - Pos Edital\06-Redes e Segurança`:
  - `aula 09.pdf`, Teoria: pág. 3-11 (Princípios de Segurança — CIA, autenticidade, não
    repúdio) + pág. 58-69 (Segurança Física, Lógica e Controle de Acesso) + pág. 93-115
    (Autenticação e seus Mecanismos, núcleo — inclui IAM/MFA/RBAC).
  - `aula 14.pdf`, Teoria: pág. 3-25 (ISO 27001 e 27002, núcleo — estrutura e categorias de
    controles).
  - `aula 15.pdf`, Teoria: pág. 3-25 (ISO 27005:2023 e Gestão de Riscos, núcleo).
- **Pretest:** 2-3 questões de cada fonte.
- **Fixação:** 5-8 questões ao final — dia denso (90 pág.).
- **Banco de reserva:** restante da Teoria de cada aula + Listas de Questões — volta antes do
  simulado #1.
- **Observações:** nenhum gap conhecido.

### Sex 30/10 — Segurança: firewalls, IDS/IPS, WAF, hardening, patches; logs, monitoramento, incidentes, continuidade
- **Leitura:**
  - `05-TCE-SC 2026 - Pos Edital\06-Redes e Segurança`, `aula 10.pdf`, Teoria completa:
    pág. 3-33 (Firewall e Proxy — inclui IDS/IPS/WAF/hardening).
  - Mesma família, `aula 16.pdf`, Teoria: pág. 3-30 (Plano de Continuidade de Negócio — inclui
    RTO/RPO — e início da ISO 22313).
  - `05-TCE-SC 2026 - Pos Edital\07-Sistemas Operacionais`, `aula 03.pdf`, Teoria: pág. 95-109
    (trecho de "Linux - Serviços de Rede e Segurança" — monitoramento e resposta a incidentes).
- **Complemento via IA (gap 🟡):** logs e monitoramento de incidentes de forma genérica
  (não específica de Linux) — a fonte encontrada é mais estreita que o assunto do edital pede.
- **Pretest:** 2-3 questões de cada fonte.
- **Fixação:** 5-8 questões ao final.
- **Banco de reserva:** restante da Teoria + Listas de Questões — volta antes do simulado #1.
- **Observações:** gap 🟡 de logs/monitoramento genérico registrado acima.

### Dom 01/11 (parte Segurança) — Criptografia, PKI, TLS, LGPD aplicada (fechamento)
*(Direito Administrativo, no mesmo dia, é bloco diferente — sem mudança aqui.)*
- **Leitura:** `05-TCE-SC 2026 - Pos Edital\06-Redes e Segurança`:
  - `aula 11.pdf`, Teoria: pág. 4-21 (SSL e TLS).
  - `aula 12.pdf`, Teoria: pág. 4-25 (Criptografia simétrica/assimétrica, hashes).
  - `aula 13.pdf`, Teoria completa: pág. 4-6 (Assinatura Digital — curta).
  - `aula 14.pdf`, trecho: pág. 75-90 (mascaramento de dados, pseudonimização, anonimização).
- **Complemento via IA (gap 🟡):** LGPD como lei aplicada a sistemas/analytics/IA e Privacy by
  Design — o ângulo jurídico específico não está nesta fonte técnica; cruzar com o material de
  Direito/Gerais quando estudado (já previsto neste mesmo dia no cronograma, "Governo Digital e
  LGPD como lei", ver bloco IA/PLN/GenAI).
- **Pretest:** 2-3 questões de cada fonte.
- **Fixação:** 5-8 questões ao final — fecha a Segurança da Informação e a Trilha 3 inteira.
- **Banco de reserva:** restante da Teoria + Listas de Questões — volta antes do simulado #1.
- **Observações:** gap 🟡 de LGPD/Privacy by Design registrado acima — resolver cruzando com o
  material de Direito quando disponível.

## Impacto no cronograma master

Nenhum — os dias já orçados (Seg-Ter 26-27/10 e Qui-Sex-Dom 29-30/10-01/11) se confirmaram
suficientes, embora densos. **Fecha a Trilha 3 inteira.**
