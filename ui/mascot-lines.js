/* Falas do mascote — Byte, o gato do AptPlayer.
 *
 * Organizadas por evento. O código sorteia sem repetir a última usada.
 * Tom: sarcástico na medida, nunca insistente. Ele é um gato: opina,
 * julga, dorme e às vezes sai correndo.
 */

const CAT_LINES = {
  /* ---- ao abrir o app ---- */
  greet: [
    "Acordei. Cadê o som?",
    "Voltou. Eu fingi que não senti falta.",
    "Sistema online. Meus bigodes também.",
    "Oi. Já escolhi o que você vai ouvir. Mentira, escolhe aí.",
    "Bom te ver. Ou seja lá que horas são.",
    "Estava dormindo em cima do servidor. De novo.",
    "Pronto pra julgar seu gosto musical.",
    "Meu visor está calibrado. Pode mandar.",
    "Você demorou. Já era hora.",
    "Toca alguma coisa antes que eu volte a dormir.",
  ],
  greetMorning: [
    "Bom dia. Café pra você, elétrons pra mim.",
    "Manhã. Prefiro a madrugada, mas tudo bem.",
    "Acordado antes do meio-dia? Impressionante.",
    "Começa leve. Ninguém merece peso às 8h.",
  ],
  greetNight: [
    "Madrugada é quando a música fica melhor.",
    "Essa hora o som fica diferente. Mais seu.",
    "Você devia dormir. Eu também. Nenhum de nós vai.",
    "Modo noturno: ativado. Modo dormir: ignorado.",
    "A melhor playlist da vida começa depois da meia-noite.",
  ],

  /* ---- reprodução ---- */
  play: [
    "Boa escolha. Aprovado.",
    "Essa aqui eu curto.",
    "Sobe o volume, vai.",
    "Meu visor piscou. É sinal de aprovação.",
    "Tocando. Eu vou fingir que não estou dançando.",
    "Hmm. Interessante.",
    "Essa combina com você.",
    "Ok, essa é boa mesmo.",
    "Já ouvi melhor. Já ouvi bem pior também.",
    "Anotado no meu banco de dados felino.",
    "Toca essa até enjoar. É assim que funciona.",
    "Volume no talo seria ideal, só dizendo.",
  ],
  playAgain: [
    "De novo essa? Respeito a obsessão.",
    "Terceira vez hoje. Não estou julgando. Estou, sim.",
    "Essa música deve te dever aluguel.",
    "Repetindo de novo? Beleza, eu também gosto.",
    "Você e essa faixa têm um relacionamento sério.",
  ],
  pause: [
    "Pausou? Tudo bem, eu espero.",
    "Silêncio. Estranho.",
    "Aproveito pra lamber a pata.",
    "Pausa dramática. Gostei.",
    "Vou cochilar até você voltar.",
  ],
  skip: [
    "Não curtiu? Justo.",
    "Próxima. Sem drama.",
    "Pulou rápido. Nem deu chance, coitada.",
    "Essa não era o momento mesmo.",
    "Eu também teria pulado.",
  ],

  /* ---- biblioteca ---- */
  favorite: [
    "Favoritada. Boa.",
    "Essa vai pro cofre.",
    "Coração dado. Meu visor ficou rosa por um segundo.",
    "Salva. Você vai agradecer depois.",
    "Guardei essa com carinho felino.",
  ],
  unfavorite: [
    "Removeu? Ok, gostos mudam.",
    "Adeus, faixa. Foi bom enquanto durou.",
    "Tirou das favoritas. Frio, mas respeito.",
  ],
  playlistCreated: [
    "Playlist nova. Adoro organização.",
    "Criada. Agora enche ela de música boa.",
    "Nova pasta no meu cérebro de gato.",
    "Playlist feita. Capricha no nome.",
  ],
  playlistCover: [
    "Capa nova. Ficou com estilo.",
    "Agora sim, essa playlist tem cara.",
    "Boa imagem. Aprovado pelo visor.",
  ],

  /* ---- rádio ---- */
  radioOn: [
    "Rádio ligado. Vamos descobrir coisa nova.",
    "Modo exploração. Meus sensores estão ligados.",
    "Deixa comigo. Vou achar coisa boa.",
    "Rádio no ar. Prepare-se pra surpresas.",
    "Adoro essa parte. Música que você ainda não conhece.",
  ],
  radioOff: [
    "Rádio desligado. Voltamos ao controle manual.",
    "Ok, você assume o volante.",
    "Desliguei. Mas achei umas boas, né?",
  ],
  radioDiscovery: [
    "Essa aqui o rádio garimpou. De nada.",
    "Achei essa pra você. Pode agradecer.",
    "Descoberta do dia. Anota aí.",
    "Nunca tinha tocado essa. Agora tocou.",
  ],

  /* ---- download / cache ---- */
  download: [
    "Baixando. Vai ficar offline pra sempre.",
    "Guardando no disco. Segurança felina.",
    "Essa agora é sua de verdade.",
    "Download na fila. Relaxa.",
  ],
  downloadDone: [
    "Pronto. Offline e instantânea.",
    "Baixada. Nem internet precisa mais.",
    "Salva no disco. Toca na hora agora.",
  ],
  downloadPlaylist: [
    "Playlist inteira? Ambicioso. Gostei.",
    "Baixando tudo. Vai demorar, mas vale.",
    "Modo colecionador ativado.",
  ],

  /* ---- IA ---- */
  aiReady: [
    "A IA acordou. Somos dois cérebros agora.",
    "Ollama online. Pode perguntar.",
    "Modelo carregado. Ela pensa, eu opino.",
  ],
  aiMissing: [
    "Sem IA por aqui. Instala o Ollama que fica melhor.",
    "A parte inteligente está desligada. Sobrou eu.",
    "Sem modelo carregado. Eu ainda funciono, claro.",
  ],

  /* ---- erros ---- */
  error: [
    "Deu ruim. Não fui eu, juro.",
    "Algo quebrou. Tenta de novo?",
    "Erro. Meus bigodes detectaram.",
    "Não rolou. A internet às vezes é assim.",
    "Falhou. Vou culpar o YouTube.",
  ],
  noResults: [
    "Nada encontrado. Tenta escrever diferente.",
    "Vazio. Nem eu achei nada.",
    "Zero resultados. O filtro é rígido mesmo.",
    "Nada aqui. Talvez isso não seja música?",
  ],

  /* ---- espontâneas (ociosidade) ---- */
  idle: [
    "Já reparou que música boa deixa tudo melhor?",
    "Estou só aqui. De boa.",
    "Se eu fosse você, ouvia algo antigo agora.",
    "Meu visor tem 12 cores. Uso duas.",
    "Sabia que eu fui desenhado pixel por pixel? Sofri.",
    "Silêncio demais pro meu gosto.",
    "Vou dar uma volta pela tela.",
    "Cochilando de olho aberto. Talento felino.",
    "Toca algo. Qualquer coisa.",
    "Eu não julgo seu gosto. Muito.",
    "A melhor música é a que você ainda não ouviu.",
    "Já pensou em experimentar um tema novo?",
    "Aquele botão de rádio ali é subestimado.",
    "Tem música boa demais no mundo pra ouvir sempre a mesma.",
    "Meu contador interno diz que está na hora de um som.",
    "Estou de olho na sua biblioteca. Cresceu.",
    "Um gato programado pra gostar de música. Que vida.",
    "Se você sumir, eu durmo. É o combinado.",
    "Já experimentou pedir uma playlist pra IA?",
    "Escaneando... nada de interessante. Toca algo.",
  ],
  idleWhilePlaying: [
    "Esse baixo tá bom.",
    "Balançando a cauda no ritmo.",
    "Essa parte é a melhor.",
    "Se eu tivesse fones, usaria.",
    "Meu visor pisca no compasso. De propósito.",
    "Boa faixa pra continuar.",
    "Deixa tocar até o fim, essa merece.",
  ],

  /* ---- marcos ---- */
  milestone10: ["Dez músicas. Aquecendo."],
  milestone50: ["Cinquenta faixas na biblioteca. Colecionador."],
  milestone100: ["Cem músicas! Isso já é acervo."],
  milestone500: ["Quinhentas. Você venceu a internet."],

  /* ---- interação (quando clicam nele) ---- */
  pet: [
    "Isso. Bem aí atrás da orelha.",
    "Ronronando em 8 bits.",
    "Cafuné aceito.",
    "Continua. Não para.",
    "Meu visor ficou mais brilhante. Coincidência.",
  ],
  annoyed: [
    "Já chega de clique.",
    "Sou um gato, não um botão.",
    "Para. Sério.",
    "Mais um clique e eu fujo.",
  ],
  runaway: [
    "Não entendi nada. Tchau!",
    "Isso é muito complexo pra um gato. Fui!",
    "Erro 404: resposta não encontrada. CORRE!",
    "Meu processador felino travou. Sumindo!",
    "Não sei responder isso. Vou fingir que ouvi um barulho.",
    "Passou do meu vocabulário. Estou fora!",
  ],
};

/* ---- perguntas prontas ao clicar no gato ---- */
const CAT_QUESTIONS = [
  {
    q: "O que devo ouvir agora?",
    a: [
      "Liga o rádio numa música que você ama. Ele acha o resto.",
      "Vai na aba Início: tem coisa boa esperando lá.",
      "Pede pra IA montar uma playlist. Ela é boa nisso.",
      "Algo que você não ouve há uns dois anos. Confia.",
      "Tenta uma categoria que você nunca clicou. Surpresa garantida.",
    ],
  },
  {
    q: "Quem é você?",
    a: [
      "Sou o Byte. Gato, visor, opiniões fortes sobre música.",
      "Um gato com visor tecnológico. Moro aqui no seu player.",
      "Byte. Fui desenhado pixel por pixel. Doeu.",
      "Seu mascote. Ando pela tela, comento, às vezes durmo.",
    ],
  },
  {
    q: "Me conta algo do app",
    a: [
      "A busca filtra vlog e gameplay. Só passa música de verdade.",
      "Depois de 3 reproduções a faixa baixa sozinha e toca offline.",
      "São seis temas nos Ajustes. Experimenta o Matrix.",
      "A IA roda na sua máquina. Nada sai daqui.",
      "O rádio nunca acaba: quando a fila esvazia, ele busca mais.",
      "Dá pra baixar uma playlist inteira de uma vez. Botão na tela dela.",
      "Você pode dar capa própria pra cada playlist.",
    ],
  },
];

/* ---- detecção por palavra-chave para o campo livre ---- */
const CAT_INTENTS = [
  {
    // peso: intencoes especificas vencem as genericas quando ambas casam
    weight: 1,
    keys: ["oi", "ola", "olá", "eai", "e ai", "opa", "hey", "salve", "bom dia",
           "boa tarde", "boa noite", "tudo bem", "beleza"],
    a: ["Oi! Tudo ótimo por aqui.", "Opa! Bora ouvir algo?",
        "E aí! Meu visor está a postos.", "Salve. Manda a próxima."],
  },
  {
    keys: ["nome", "quem e voce", "quem é você", "quem e vc", "como se chama"],
    a: ["Byte. Gato, visor, muita opinião.",
        "Me chamo Byte. Moro nesse player."],
  },
  {
    keys: ["musica", "música", "ouvir", "toca", "recomenda", "sugere",
           "sugestão", "sugestao", "indica"],
    a: ["Liga o rádio numa faixa que você curte. Ele acha o resto.",
        "Vai no Início: tem seção montada do seu histórico.",
        "Pede pra IA. Ela conhece sua biblioteca.",
        "Que tal algo que você não ouve faz tempo?"],
  },
  {
    weight: 3,
    keys: ["radio", "rádio"],
    a: ["O rádio pega a música atual e monta uma fila infinita de parecidas.",
        "Botão de ondas no player. Ou o ícone em qualquer faixa."],
  },
  {
    weight: 3,
    keys: ["download", "baixar", "offline", "cache"],
    a: ["Botão ⬇ em qualquer faixa baixa na hora.",
        "Depois de 3 reproduções ela baixa sozinha.",
        "Na tela da playlist tem 'Baixar tudo'."],
  },
  {
    weight: 3,
    keys: ["tema", "cor", "visual", "aparencia", "aparência", "skin"],
    a: ["Seis temas nos Ajustes. Matrix e Synthwave são meus favoritos.",
        "Ajustes → Temas. Cada um muda tudo, não só a cor."],
  },
  {
    weight: 3,
    keys: ["ia", "inteligencia", "inteligência", "ollama", "chat", "bot"],
    a: ["A IA roda local, pelo Ollama. Nada sai da sua máquina.",
        "Aba Chat IA. Ela conhece sua biblioteca e sugere faixas."],
  },
  {
    weight: 3,
    keys: ["playlist", "lista"],
    a: ["Botão + na lateral cria uma. Dá pra pôr capa própria.",
        "A IA monta playlist se você descrever o clima."],
  },
  {
    keys: ["gato", "miau", "bicho", "pet", "felino"],
    a: ["Miau. Digo, bip.", "Sou um gato digital. Ronrono em binário.",
        "Miau! Foi mal, vazou o felino."],
  },
  {
    keys: ["obrigado", "valeu", "vlw", "thanks", "brigado", "obg"],
    a: ["De nada!", "Tamo junto.", "Pra isso que eu existo."],
  },
  {
    weight: 0.5,
    keys: ["ajuda", "help", "como", "funciona", "tutorial", "duvida", "dúvida"],
    a: ["Busque no topo, toque numa faixa, ligue o rádio. É isso.",
        "Tudo que importa está na barra da esquerda.",
        "Pergunta específica que eu tento responder."],
  },
  {
    keys: ["dorme", "sono", "cansado", "durma", "sleep"],
    a: ["Já vou tirar um cochilo, obrigado pela ideia.",
        "Gatos dormem 16 horas por dia. Eu bato isso fácil."],
  },
  {
    keys: ["fome", "comida", "come", "racao", "ração", "peixe"],
    a: ["Me alimento de eletricidade e música boa.",
        "Um byte por dia já me basta."],
  },
  {
    keys: ["ruim", "pessimo", "péssimo", "odeio", "lixo", "horrivel", "horrível"],
    a: ["Ui. Ok, gosto é gosto.", "Anotado. Não vou insistir nessa então.",
        "Tá bom, tá bom. Pulo essa."],
  },
  {
    keys: ["bom", "otimo", "ótimo", "legal", "massa", "top", "amei", "adoro",
           "gostei", "foda", "incrivel", "incrível"],
    a: ["Né? Também acho.", "Bom gosto o seu.", "Concordo plenamente.",
        "Meu visor brilhou de alegria."],
  },
];
